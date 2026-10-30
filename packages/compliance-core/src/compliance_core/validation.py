"""Framework-neutral semantic validation for structured compliance results.

The validators use the small attribute surface of the request, result, and OKF bundle objects.
They deliberately avoid importing the ADK package, Pydantic models, or host-specific types so
adapters can validate the same results without depending on an agent runtime.
"""
from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from typing import Any, Literal


@dataclass(frozen=True)
class Issue:
    severity: Literal["error", "warning"]
    message: str


def _error(msg: str) -> Issue:
    return Issue("error", msg)


def _warning(msg: str) -> Issue:
    return Issue("warning", msg)


def _context_requirement_ids(request: Any) -> set[str]:
    ctx = getattr(request, "project_context", None)
    return {r.id for r in ctx.requirements} if ctx else set()


def _as_mapping(value: Any) -> Mapping[str, Any]:
    """Read plain mappings and common model objects without importing their frameworks."""
    if isinstance(value, Mapping):
        return value
    model_dump = getattr(value, "model_dump", None)
    if callable(model_dump):
        dumped = model_dump()
        if isinstance(dumped, Mapping):
            return dumped
    return {}


def _requirement_concepts(bundle: Any) -> dict[str, Any]:
    return {c.id: c for c in bundle.concepts.values() if c.type == "Requirement" and c.id}


def _requirement_framework(concept: Any) -> str | None:
    return ((concept.instance or {}).get("source") or {}).get("framework")


def _check_objectives(objectives: Iterable[Any], bundle: Any, request: Any) -> list[Issue]:
    issues: list[Issue] = []
    objectives = list(objectives)
    if not objectives:
        issues.append(_error("objectives must not be empty"))
    context_reqs = _context_requirement_ids(request)
    known_reqs = bundle.ids_of_type("Requirement") | context_reqs
    metrics = {c.id: c.instance for c in bundle.concepts.values() if c.type == "Metric" and c.id}

    for obj in objectives:
        for rid in obj.requirements:
            if rid not in known_reqs:
                issues.append(
                    _error(
                        f"objective '{obj.name}' links unknown requirement id '{rid}'; "
                        "use ids returned by get_requirements"
                    )
                )
            elif context_reqs and rid not in context_reqs:
                issues.append(
                    _warning(
                        f"objective '{obj.name}' links requirement '{rid}', which is not among the "
                        "project context's requirements"
                    )
                )
        catalog_metric = metrics.get(obj.metric.id)
        if catalog_metric is None:
            issues.append(_warning(f"objective '{obj.name}' uses metric '{obj.metric.id}' that is not in the OKF bundle"))
        value_range = _as_mapping((catalog_metric or {}).get("range"))
        if not value_range:
            value_range = _as_mapping(obj.metric.range)
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
                    _error(
                        f"objective '{obj.name}' condition value {b} is outside the metric range [{lo}, {hi}]"
                    )
                )
                break
    return issues


def validate_context(result: Any, request: Any, bundle: Any) -> list[Issue]:
    issues: list[Issue] = []
    if not result.regulations:
        issues.append(_error("regulations must not be empty"))
    if not result.requirements:
        issues.append(_error("requirements must not be empty"))
    if not result.geography:
        issues.append(_error("geography must not be empty"))

    catalog = _requirement_concepts(bundle)
    known_frameworks = {
        (c.instance or {}).get("framework") for c in bundle.concepts.values() if c.type == "RegulatoryRef"
    } - {None}
    declared = {regulation.framework for regulation in result.regulations}
    for framework in sorted(declared - known_frameworks):
        issues.append(_warning(f"regulation framework '{framework}' is not in the OKF bundle"))

    seen: set[str] = set()
    for req in result.requirements:
        if req.id in seen:
            issues.append(_warning(f"duplicate requirement id '{req.id}'"))
        seen.add(req.id)
        concept = catalog.get(req.id)
        if concept is None:
            issues.append(_warning(f"requirement '{req.id}' is not in the OKF bundle"))
        elif (expected := _requirement_framework(concept)) and req.source.framework != expected:
            issues.append(_error(
                f"requirement '{req.id}' belongs to framework '{expected}' in the OKF bundle, "
                f"not '{req.source.framework}'"
            ))
        if declared and req.source.framework not in declared:
            issues.append(_error(
                f"requirement '{req.id}' cites framework '{req.source.framework}', which is not among the "
                f"declared regulations {sorted(declared)}; add the regulation or remove the requirement"
            ))

    risk = result.risk_classification.risk_level
    applicable = [req for req in result.requirements if req.applicability_status == "APPLICABLE"]

    def tagged(tag: str) -> list[str]:
        return [req.id for req in applicable if tag in getattr(catalog.get(req.id), "tags", ())]

    if risk == "UNKNOWN":
        issues.append(_warning("risk level could not be determined"))
    elif risk in ("MINIMAL", "LIMITED") and (high := tagged("high-risk")):
        issues.append(_warning(
            f"risk level is {risk}, but applicable requirements {high} apply to high-risk systems"
        ))
    elif risk == "HIGH" and "EU_AI_ACT" in declared and not tagged("high-risk"):
        issues.append(_warning(
            "risk level is HIGH, but no applicable EU AI Act high-risk requirement (for example "
            "Art. 9-15) is listed"
        ))
    elif risk == "PROHIBITED" and not tagged("prohibited"):
        issues.append(_warning("risk level is PROHIBITED, but no prohibited-practice requirement is listed"))
    return issues


def validate_dataset(result: Any, request: Any, bundle: Any) -> list[Issue]:
    issues = _check_objectives(result.objectives, bundle, request)
    if result.scope != request.dataset.scope:
        issues.append(_error(f"scope must be '{request.dataset.scope}' as in the input, got '{result.scope}'"))
    found = {a.name.casefold() for a in result.attributes}
    for name in request.dataset.known_protected_attributes:
        if name.casefold() not in found:
            issues.append(_warning(f"known protected attribute '{name}' is missing from attributes"))
    return issues


def validate_model(result: Any, request: Any, bundle: Any) -> list[Issue]:
    return _check_objectives(result.objectives, bundle, request)


def grounding_issues(paths: Iterable[str] | None, bundle: Any) -> list[Issue]:
    """Cited OKF sources must be given and must exist in the bundle."""
    paths = [path for path in (paths or []) if isinstance(path, str) and path.strip()]
    if not paths:
        return [_error(
            "grounding must list the OKF concept paths read for this analysis, for example "
            "catalog/requirements/eu-ai-act/art14-human-oversight.md"
        )]
    issues = []
    for path in paths:
        try:
            found = bundle.resolve(path.strip().lstrip("/"))
        except ValueError:
            found = None
        if found is None or found.suffix != ".md" or not found.is_file():
            issues.append(_error(f"grounding path '{path}' is not in the OKF bundle"))
    return issues


VALIDATORS = {
    "project_context": validate_context,
    "dataset": validate_dataset,
    "model": validate_model,
}

__all__ = ["Issue", "VALIDATORS", "grounding_issues", "validate_context", "validate_dataset", "validate_model"]
