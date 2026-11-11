"""Framework-neutral evidence loading, deterministic reports and named persistence."""
from __future__ import annotations

from typing import Any
from urllib.parse import urlparse

from .contracts.reports import ReportSpec
from .evaluation_inputs import InputError, load_results
from .reporting import build_reports, validate_report
from .provenance import build_provenance
from .specification_tools import specification_revision
from .state import REPORTS_KEY, StateStore, entity_project, scoped_get, scoped_update, transaction
from .tools import ToolEnv, ToolSpec

class ReportError(ValueError):
    def __init__(self, message: str, code: str):
        super().__init__(message)
        self.code = code


def _error(message: str, code: str) -> dict[str, Any]:
    return {"error": message, "code": code}


def _target(state: StateStore, kind: str, entity: str, name: str, project: str | None) -> str:
    if kind not in ("dataset", "model"):
        raise ReportError("Report target kind must be dataset or model", "invalid_kind")
    if not entity.strip() or not name.strip():
        raise ReportError("An entity and report name are required", "invalid_target")
    if entity.startswith("store://"):
        embedded = urlparse(entity).netloc
        if project and embedded != project:
            raise ReportError("store:// project conflicts with explicit project", "project_mismatch")
        project = embedded
    project = entity_project(state, project)
    if not project:
        raise ReportError("Specify a project or a project-scoped store:// key", "missing_project")
    return project


def report_key(kind: str, entity: str, name: str) -> str:
    import json
    return json.dumps([kind, entity, name], separators=(",", ":"))


def prepare_report(
    state: StateStore, kind: str, entity: str, name: str,
    report: Any = None, project: str | None = None,
) -> dict[str, Any]:
    """Normalize exactly the named report a save/approval would write."""
    project = _target(state, kind, entity, name, project)
    source = "argument" if report is not None else "session"
    if report is None:
        saved = scoped_get(state, REPORTS_KEY, project).get(report_key(kind, entity, name))
        report = saved.get("report") if saved else None
    if report is None:
        raise ReportError("No report supplied or staged under this target/name", "not_found")
    try:
        validated = validate_report(report)
    except ValueError as exc:
        raise ReportError(f"Invalid report: {exc}", "invalid_report") from exc
    return {"kind": kind, "entity": entity, "name": name, "project": project,
            "report": validated.model_dump(mode="json", exclude_none=True, by_alias=True),
            "validated": validated, "source": source}


prepare_compliance_report = prepare_report


def build_compliance_report(
    env: ToolEnv, results: Any, variants: Any = None, lineage: Any = None,
) -> dict[str, Any]:
    """Build separate validated EVALUATION/TEST reports from supplied evidence, without writes."""
    try:
        if isinstance(results, dict) and "results" in results:
            results = results["results"]
        return build_reports(results, variants=("EVALUATION", "TEST") if variants is None else variants, lineage=lineage)
    except (ValueError, TypeError) as exc:
        return _error(f"Invalid report inputs: {exc}", "invalid_input")


def validate_compliance_report(env: ToolEnv, report: Any) -> dict[str, Any]:
    """Validate report kind/content agreement and strict OKF-compatible report structure."""
    try:
        normalized = validate_report(report).model_dump(mode="json", exclude_none=True, by_alias=True)
    except (ValueError, TypeError) as exc:
        return _error(f"Invalid report: {exc}", "invalid_report")
    return {"valid": True, "report": normalized}


def load_evaluation_results(
    env: ToolEnv, source: str, format: str = "json", mapping: Any = None,
) -> dict[str, Any]:
    """Read bounded JSON through an authorized reader, or regular files under the working directory."""
    try:
        return load_results(source, format=format, mapping=mapping, reader=getattr(env, "input_reader", None))
    except InputError as exc:
        return _error(str(exc), exc.code)


def record_compliance_report(
    env: ToolEnv, kind: str, entity: str, name: str, report: Any,
    project: str | None = None, provenance: Any = None,
) -> dict[str, Any]:
    """Validate and stage named report evidence locally, without writing to DigitalHub."""
    try:
        prepared = prepare_report(env.state, kind, entity, name, report, project)
        if provenance is not None and not isinstance(provenance, dict):
            raise ReportError("Source provenance must be an object", "invalid_provenance")
    except ReportError as exc:
        return _error(str(exc), exc.code)
    project = prepared["project"]
    key = report_key(kind, entity, name)
    recorded_provenance = {
        **build_provenance("supplied", env.bundle.version),
        "source": provenance or {},
    }
    with transaction(env.state):
        previous = scoped_get(env.state, REPORTS_KEY, project).get(key, {})
        scoped_update(env.state, REPORTS_KEY, key, {
            "report": prepared["report"],
            "revision": previous.get("revision"),
            "provenance": recorded_provenance,
        }, project)
    return {
        "stored": True, "kind": kind, "entity": entity, "name": name, "project": project,
        "report": prepared["report"], "provenance": recorded_provenance,
    }


def get_session_compliance_reports(env: ToolEnv, project: str | None = None) -> dict[str, Any]:
    """Retrieve report evidence staged or retrieved in the selected workspace project."""
    selected = entity_project(env.state, project)
    return {"project": selected, "reports": scoped_get(env.state, REPORTS_KEY, selected)}


def get_compliance_report(
    env: ToolEnv, kind: str, entity: str, name: str, project: str | None = None,
) -> dict[str, Any]:
    """Retrieve a named project-scoped compliance-report and remember its revision."""
    repository = getattr(env, "reports", None)
    if repository is None:
        return _error("The report repository is not configured", "integration_unavailable")
    try:
        project = _target(env.state, kind, entity, name, project)
        raw = repository.get(kind, entity, name, project=project)
        if not raw:
            return _error("Named compliance report was not found", "not_found")
        normalized = validate_report(raw).model_dump(mode="json", exclude_none=True, by_alias=True)
        revision = specification_revision(raw)
        scoped_update(env.state, REPORTS_KEY, report_key(kind, entity, name),
                      {"report": normalized, "revision": revision}, project)
    except ReportError as exc:
        return _error(str(exc), exc.code)
    except ValueError as exc:
        return _error(f"Stored report is invalid: {exc}", "invalid_report")
    except Exception as exc:
        return _error(f"Could not retrieve report: {exc}", "dh_error")
    return {"kind": kind, "entity": entity, "name": name, "project": project,
            "report": normalized, "revision": revision}


def save_compliance_report(
    env: ToolEnv, kind: str, entity: str, name: str, report: Any = None,
    project: str | None = None, overwrite: bool = False,
) -> dict[str, Any]:
    """Save a named report after explicit authorization by the host.

    Refuse replacing unseen/stale reports unless overwrite is explicitly approved.
    This read/check/write is not an atomic compare-and-swap.
    """
    repository = getattr(env, "reports", None)
    if repository is None:
        return _error("The report repository is not configured", "integration_unavailable")
    try:
        prepared = prepare_report(env.state, kind, entity, name, report, project)
    except ReportError as exc:
        return _error(str(exc), exc.code)
    project = prepared["project"]
    key = report_key(kind, entity, name)
    try:
        current = specification_revision(repository.get(kind, entity, name, project=project))
        cached = scoped_get(env.state, REPORTS_KEY, project).get(key, {})
        seen = cached.get("revision")
        if current is not None and current != seen and not overwrite:
            return {**_error("Named report exists but was not retrieved, or changed since retrieval", "conflict"),
                    "current_revision": current, "seen_revision": seen}
        repository.save(kind, entity, name, prepared["report"], project=project)
    except Exception as exc:
        return _error(f"Could not save report: {exc}", "dh_error")
    try:
        revision = specification_revision(repository.get(kind, entity, name, project=project))
    except Exception:
        revision = None
    with transaction(env.state):
        previous = scoped_get(env.state, REPORTS_KEY, project).get(key, {})
        scoped_update(env.state, REPORTS_KEY, key, {
            **previous, "report": prepared["report"], "revision": revision,
        }, project)
    return {"kind": kind, "entity": entity, "name": name, "project": project,
            "extension_kind": "compliance-report", "saved": True,
            "source": prepared["source"], "revision": revision}


REPORT_TOOL_SPECS = (
    ToolSpec("record_compliance_report", record_compliance_report, "session", record_compliance_report.__doc__ or "", False),
    ToolSpec("get_session_compliance_reports", get_session_compliance_reports, "session", get_session_compliance_reports.__doc__ or "", True),
    ToolSpec("load_evaluation_results", load_evaluation_results, "validation", load_evaluation_results.__doc__ or "", True),
    ToolSpec("build_compliance_report", build_compliance_report, "validation", build_compliance_report.__doc__ or "", True),
    ToolSpec("validate_compliance_report", validate_compliance_report, "validation", validate_compliance_report.__doc__ or "", True),
    ToolSpec("get_compliance_report", get_compliance_report, "dh", get_compliance_report.__doc__ or "", False),
    ToolSpec("save_compliance_report", save_compliance_report, "dh", save_compliance_report.__doc__ or "", False, destructive=True),
)
REPORT_TOOL_REGISTRY = {spec.name: spec.fn for spec in REPORT_TOOL_SPECS}
TOOL_SPECS = REPORT_TOOL_SPECS
