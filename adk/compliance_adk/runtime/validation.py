"""Semantic checks on agent output, beyond what the Pydantic schema enforces."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Literal

from pydantic import BaseModel

from ..contracts import ComplianceObjectiveOut
from ..knowledge import OkfBundle


@dataclass(frozen=True)
class Issue:
    severity: Literal["error", "warning"]
    message: str


def _error(msg: str) -> Issue:
    return Issue("error", msg)


def _warning(msg: str) -> Issue:
    return Issue("warning", msg)


def _context_requirement_ids(request: BaseModel) -> set[str]:
    ctx = getattr(request, "project_context", None)
    return {r.id for r in ctx.requirements} if ctx else set()


def _check_objectives(
    objectives: Iterable[ComplianceObjectiveOut], bundle: OkfBundle, request: BaseModel
) -> list[Issue]:
    issues: list[Issue] = []
    objectives = list(objectives)
    if not objectives:
        issues.append(_error("objectives must not be empty"))
    known_reqs = bundle.ids_of_type("Requirement") | _context_requirement_ids(request)
    metrics = {c.id: c.instance for c in bundle.concepts.values() if c.type == "Metric" and c.id}

    for obj in objectives:
        for rid in obj.requirements:
            if rid not in known_reqs:
                issues.append(
                    _error(f"objective '{obj.name}' links unknown requirement id '{rid}'; use ids returned by get_requirements")
                )
        catalog_metric = metrics.get(obj.metric.id)
        if catalog_metric is None:
            issues.append(_warning(f"objective '{obj.name}' uses metric '{obj.metric.id}' that is not in the OKF bundle"))
        value_range = (catalog_metric or {}).get("range") or (obj.metric.range.model_dump() if obj.metric.range else {})
        lo, hi = value_range.get("lower"), value_range.get("upper")
        cond = obj.condition
        bounds = []
        if cond.threshold:
            bounds.append(cond.threshold.value)
        if cond.range:
            if cond.range.lower > cond.range.upper:
                issues.append(_error(f"objective '{obj.name}' has a range with lower > upper"))
            bounds += [cond.range.lower, cond.range.upper]
        for b in bounds:
            if (lo is not None and b < lo) or (hi is not None and b > hi):
                issues.append(
                    _error(f"objective '{obj.name}' condition value {b} is outside the metric range [{lo}, {hi}]")
                )
                break
    return issues


def validate_context(result: Any, request: BaseModel, bundle: OkfBundle) -> list[Issue]:
    issues: list[Issue] = []
    if not result.regulations:
        issues.append(_error("regulations must not be empty"))
    if not result.requirements:
        issues.append(_error("requirements must not be empty"))
    if not result.geography:
        issues.append(_error("geography must not be empty"))
    known = bundle.ids_of_type("Requirement")
    seen: set[str] = set()
    for req in result.requirements:
        if req.id in seen:
            issues.append(_warning(f"duplicate requirement id '{req.id}'"))
        seen.add(req.id)
        if req.id not in known:
            issues.append(_warning(f"requirement '{req.id}' is not in the OKF bundle"))
    if result.risk_classification.risk_level == "UNKNOWN":
        issues.append(_warning("risk level could not be determined"))
    return issues


def validate_dataset(result: Any, request: BaseModel, bundle: OkfBundle) -> list[Issue]:
    issues = _check_objectives(result.objectives, bundle, request)
    if result.scope != request.dataset.scope:
        issues.append(_error(f"scope must be '{request.dataset.scope}' as in the input, got '{result.scope}'"))
    found = {a.name.casefold() for a in result.attributes}
    for name in request.dataset.known_protected_attributes:
        if name.casefold() not in found:
            issues.append(_warning(f"known protected attribute '{name}' is missing from attributes"))
    return issues


def validate_model(result: Any, request: BaseModel, bundle: OkfBundle) -> list[Issue]:
    return _check_objectives(result.objectives, bundle, request)


VALIDATORS = {
    "project_context": validate_context,
    "dataset": validate_dataset,
    "model": validate_model,
}
