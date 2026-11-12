# SPDX-FileCopyrightText: © 2026 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import asyncio
import json
from importlib.resources import files
from pathlib import Path

from compliance_core.analysis_engine import ANALYSES_BY_KEY, AnalysisTrace, build_response
from compliance_core.errors import OutputValidationError
from compliance_core.evaluation import evaluate, load_cases, render_markdown
from compliance_core.knowledge import get_bundle

ROOT = Path(__file__).resolve().parents[3]
CASES = ROOT / "evals" / "cases.json"
SKILLS = {"project_context": "project-context", "dataset": "dataset-analysis", "model": "model-analysis"}


def example(analysis: str) -> dict:
    return json.loads(files("compliance_skills").joinpath("skills", SKILLS[analysis], "references", "example.json").read_text())


def test_benchmark_cases_are_valid_and_reference_catalog_ids():
    bundle = get_bundle()
    requirement_ids = bundle.ids_of_type("Requirement")
    cases = load_cases(CASES)
    assert len(cases) >= 8
    for case in cases:
        ANALYSES_BY_KEY[case.analysis].request_model.model_validate(case.request)
        assert set(case.expected.requirements) <= requirement_ids, case.id
        assert case.rationale
    assert {case.expected.risk_level for case in cases} >= {"HIGH", "LIMITED", "MINIMAL", "PROHIBITED"}


class ExampleEngine:
    """Answers every case with the skill example; one case fails, one invents an id."""

    async def run(self, analysis, request, request_id=None):
        if request_id == "eval-exam-grading":
            raise OutputValidationError("The model did not produce valid output", ["broken"])
        definition = ANALYSES_BY_KEY[analysis]
        raw = example(analysis)
        if request_id == "eval-cv-screening":
            raw["result"]["requirements"][0]["id"] = "req-invented"
        output = definition.output_model.model_validate(raw)
        trace = AnalysisTrace(attempts=2 if request_id == "eval-cv-screening" else 1)
        trace.grounding["catalog/requirements/eu-ai-act/art14-human-oversight.md"] = None
        return build_response(definition, output, [], trace, request_id=request_id, model="example",
                              bundle=get_bundle(), latency_ms=5)


def test_evaluation_scores_cases_and_renders_a_comparison():
    report = asyncio.run(evaluate(load_cases(CASES), ExampleEngine(), get_bundle(), label="example"))
    cases = {case.id: case for case in report.cases}

    credit = cases["consumer-credit-scoring"]
    assert credit.valid and credit.risk_match is True and credit.requirement_recall == 0.25
    assert cases["customer-support-chatbot"].risk_match is False
    assert cases["exam-grading"].valid is False and "OutputValidationError" in cases["exam-grading"].error
    assert cases["cv-screening"].invented_ids == ["req-invented"]
    assert cases["recruitment-training-data"].attribute_recall is not None

    summary = report.summary
    assert summary["cases"] == len(report.cases)
    assert summary["validity_rate"] == round((len(report.cases) - 1) / len(report.cases), 3)
    assert 0 < summary["retry_rate"] < 1 and summary["grounded_rate"] == 1.0

    markdown = render_markdown([report, report.model_copy(update={"label": "other"})])
    assert "| validity_rate |" in markdown and "| Metric | example | other |" in markdown
    assert "req-invented" in markdown
