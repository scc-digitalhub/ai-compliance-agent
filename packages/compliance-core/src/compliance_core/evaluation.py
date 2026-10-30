"""Benchmark evaluation of structured analyses: run cases through an engine, score and compare.

Scores per case: output validity, risk-level agreement, recall of expected catalog requirements and
attributes, invented catalog ids, retries, warnings, tokens and latency.
"""
from __future__ import annotations

import asyncio
import json
import time
from pathlib import Path
from statistics import mean
from typing import Any, Optional

from pydantic import BaseModel, Field

from .analysis_engine import ANALYSES_BY_KEY, AnalysisKey
from .contracts.enums import RiskLevel
from .errors import ComplianceError
from .knowledge import OkfBundle
from .ports import AnalysisEngine
from .version import framework_version


class Expectations(BaseModel):
    risk_level: Optional[RiskLevel] = None
    requirements: list[str] = Field(default_factory=list, description="Catalog requirement ids expected")
    attributes: list[str] = Field(default_factory=list, description="Attribute names expected (datasets)")


class EvalCase(BaseModel):
    id: str
    analysis: AnalysisKey
    request: dict[str, Any]
    expected: Expectations
    rationale: str = Field(description="Why these expectations hold, with the legal basis")


class CaseResult(BaseModel):
    id: str
    analysis: AnalysisKey
    valid: bool
    error: Optional[str] = None
    risk_level: Optional[str] = None
    risk_match: Optional[bool] = None
    requirement_recall: Optional[float] = None
    attribute_recall: Optional[float] = None
    invented_ids: list[str] = Field(default_factory=list)
    attempts: int = 0
    warnings: int = 0
    grounded: bool = False
    input_tokens: int = 0
    output_tokens: int = 0
    latency_ms: int = 0


class EvalReport(BaseModel):
    label: str
    okf_version: str
    framework_version: str
    summary: dict[str, Optional[float]]
    cases: list[CaseResult]


def load_cases(path: str | Path) -> list[EvalCase]:
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    cases = [EvalCase.model_validate(item) for item in raw["cases"]]
    if len({case.id for case in cases}) != len(cases):
        raise ValueError("Evaluation case ids must be unique")
    return cases


def _recall(expected: list[str], found: set[str]) -> Optional[float]:
    if not expected:
        return None
    return sum(1 for item in expected if item in found) / len(expected)


def score(case: EvalCase, response: Any, bundle: OkfBundle) -> CaseResult:
    data, meta = response.data, response.meta
    requirement_ids = set(bundle.ids_of_type("Requirement"))
    metric_ids = set(bundle.ids_of_type("Metric"))
    risk = None
    if case.analysis == "project_context":
        risk = data.risk_classification.risk_level
        linked = {requirement.id for requirement in data.requirements}
        invented = sorted(linked - requirement_ids)
    else:
        linked = {rid for objective in data.objectives for rid in objective.requirements}
        metrics = {objective.metric.id for objective in data.objectives}
        invented = sorted((linked - requirement_ids) | (metrics - metric_ids))
    attributes = {attribute.name.casefold() for attribute in getattr(data, "attributes", [])}
    return CaseResult(
        id=case.id,
        analysis=case.analysis,
        valid=True,
        risk_level=risk,
        risk_match=None if case.expected.risk_level is None else risk == case.expected.risk_level,
        requirement_recall=_recall(case.expected.requirements, linked),
        attribute_recall=_recall([name.casefold() for name in case.expected.attributes], attributes),
        invented_ids=invented,
        attempts=meta.attempts,
        warnings=len(meta.warnings),
        grounded=bool(meta.grounding),
        input_tokens=meta.usage.input_tokens,
        output_tokens=meta.usage.output_tokens,
        latency_ms=meta.latency_ms,
    )


async def run_case(case: EvalCase, engine: AnalysisEngine, bundle: OkfBundle) -> CaseResult:
    definition = ANALYSES_BY_KEY[case.analysis]
    started = time.perf_counter()
    try:
        request = definition.request_model.model_validate(case.request)
        response = await engine.run(case.analysis, request, f"eval-{case.id}")
    except (ComplianceError, ValueError) as exc:
        return CaseResult(
            id=case.id, analysis=case.analysis, valid=False, error=f"{type(exc).__name__}: {exc}",
            latency_ms=int((time.perf_counter() - started) * 1000),
        )
    return score(case, response, bundle)


def _mean(values: list[float]) -> Optional[float]:
    return round(mean(values), 3) if values else None


def summarize(results: list[CaseResult]) -> dict[str, Optional[float]]:
    valid = [result for result in results if result.valid]
    return {
        "cases": len(results),
        "validity_rate": _mean([float(result.valid) for result in results]),
        "risk_accuracy": _mean([float(r.risk_match) for r in valid if r.risk_match is not None]),
        "requirement_recall": _mean([r.requirement_recall for r in valid if r.requirement_recall is not None]),
        "attribute_recall": _mean([r.attribute_recall for r in valid if r.attribute_recall is not None]),
        "invented_id_rate": _mean([float(bool(r.invented_ids)) for r in valid]),
        "grounded_rate": _mean([float(r.grounded) for r in valid]),
        "retry_rate": _mean([float(r.attempts > 1) for r in valid]),
        "mean_warnings": _mean([float(r.warnings) for r in valid]),
        "mean_latency_ms": _mean([float(r.latency_ms) for r in valid]),
        "total_tokens": float(sum(r.input_tokens + r.output_tokens for r in valid)),
    }


async def evaluate(
    cases: list[EvalCase], engine: AnalysisEngine, bundle: OkfBundle, *, label: str, concurrency: int = 2,
) -> EvalReport:
    semaphore = asyncio.Semaphore(concurrency)

    async def bounded(case: EvalCase) -> CaseResult:
        async with semaphore:
            return await run_case(case, engine, bundle)

    results = await asyncio.gather(*(bounded(case) for case in cases))
    return EvalReport(
        label=label, okf_version=bundle.version, framework_version=framework_version(),
        summary=summarize(list(results)), cases=list(results),
    )


def render_markdown(reports: list[EvalReport]) -> str:
    """Comparison table of report summaries, followed by per-case results."""
    if not reports:
        return ""
    keys = list(reports[0].summary)
    lines = [
        f"OKF {reports[0].okf_version} · framework {reports[0].framework_version}",
        "",
        "| Metric | " + " | ".join(report.label for report in reports) + " |",
        "|---|" + "---|" * len(reports),
    ]
    for key in keys:
        values = ["–" if report.summary[key] is None else f"{report.summary[key]:g}" for report in reports]
        lines.append(f"| {key} | " + " | ".join(values) + " |")
    for report in reports:
        lines += ["", f"### {report.label}", "",
                  "| Case | Valid | Risk | Req. recall | Invented ids | Attempts | Warnings |",
                  "|---|---|---|---|---|---|---|"]
        for case in report.cases:
            risk = case.risk_level or "–"
            if case.risk_match is not None:
                risk += " ✓" if case.risk_match else " ✗"
            recall = "–" if case.requirement_recall is None else f"{case.requirement_recall:.2f}"
            lines.append(
                f"| {case.id} | {'yes' if case.valid else 'no: ' + (case.error or '')[:60]} | {risk} | "
                f"{recall} | {', '.join(case.invented_ids) or '–'} | {case.attempts} | {case.warnings} |"
            )
    return "\n".join(lines) + "\n"


__all__ = [
    "CaseResult",
    "EvalCase",
    "EvalReport",
    "Expectations",
    "evaluate",
    "load_cases",
    "render_markdown",
    "run_case",
    "score",
    "summarize",
]
