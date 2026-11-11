"""Generate, statically validate and record standalone/combined report executables.

No artifact generated here is imported, executed, or published to DigitalHub.
"""
from __future__ import annotations

import ast
import hashlib
import json
import re
import shlex
import subprocess
from datetime import datetime, timezone
from pathlib import PurePosixPath
from typing import Any

from pydantic import BaseModel, ValidationError

from .contracts.evaluation_code import MetricEvaluationCodeArtifact
from .contracts.report_code import ReportCodeArtifact, ReportCodeOutput, ReportCodeRequest
from .errors import ComplianceError
from .metric_evaluation_tools import validate_metric_evaluation_code
from .state import CODES_KEY, active_project, known_projects, scoped_get, scoped_update, transaction
from .tools import ToolEnv, ToolSpec

_CALL_BLOCKLIST = {"__import__", "compile", "eval", "exec", "system", "popen"}
_SHELL_BLOCKLIST = re.compile(r"(?:\beval\b|\bsource\b|`|\$\(|\brm\b|\bcurl\b|\bwget\b|\bnc\b|\bsocat\b)")
_CREDENTIAL_KEYS = {
    "password", "secret", "credential", "credentials", "token", "access_token",
    "api_key", "client_secret",
}


def _validate_model(model: type[BaseModel], value: Any) -> BaseModel:
    if isinstance(value, str):
        return model.model_validate_json(value)
    if isinstance(value, BaseModel):
        return model.model_validate(value.model_dump(mode="json"))
    return model.model_validate(value)


def _hash(value: Any) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, default=str)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _issue(message: str) -> dict[str, str]:
    return {"message": message}


def _credential_fields(value: Any, prefix: str = "") -> list[str]:
    found = []
    if isinstance(value, dict):
        for key, child in value.items():
            path = f"{prefix}.{key}" if prefix else str(key)
            normalized = str(key).casefold().replace("-", "_")
            if normalized in _CREDENTIAL_KEYS:
                found.append(path)
            found.extend(_credential_fields(child, path))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            found.extend(_credential_fields(child, f"{prefix}[{index}]"))
    return found


def _parse_python(path: str, source: str, errors: list[dict[str, str]]) -> ast.Module | None:
    try:
        return ast.parse(source, filename=f"<{path}>", mode="exec")
    except (SyntaxError, ValueError) as exc:
        errors.append(_issue(f"{path} is not syntactically valid Python: {exc}"))
        return None


def _check_python_side_effect_boundary(
    tree: ast.Module, *, allow_publication: bool, errors: list[dict[str, str]],
) -> None:
    """Reject dynamic execution; allow declared, target-bound report publication."""
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            name = node.func.id if isinstance(node.func, ast.Name) else (
                node.func.attr if isinstance(node.func, ast.Attribute) else ""
            )
            if name in _CALL_BLOCKLIST:
                errors.append(_issue(f"Generated Python calls prohibited dynamic function '{name}'."))
            if not allow_publication and name in {
                "save_compliance_report", "save_batch", "publish", "attach",
                "save", "update", "delete", "write_text", "write_bytes",
            }:
                errors.append(_issue(f"Evaluator code may not perform publication or mutation through '{name}'."))


def _check_shell(path: str, source: str, errors: list[dict[str, str]]) -> None:
    if _SHELL_BLOCKLIST.search(source):
        errors.append(_issue(f"{path} uses a prohibited dynamic or unrelated shell operation."))
    try:
        parsed = subprocess.run(
            ["sh", "-n"], input=source, text=True, capture_output=True, check=False,
        )
    except OSError as exc:
        errors.append(_issue(f"Could not run a non-executing shell syntax check: {exc}"))
        return
    if parsed.returncode:
        errors.append(_issue(f"{path} has invalid shell syntax: {parsed.stderr.strip()}"))
    # Shell artifacts are wrappers, not a second implementation of report semantics.
    commands = []
    for line in source.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or stripped in {"set -e", "set -u", "set -eu"}:
            continue
        try:
            parsed = shlex.split(stripped)
            commands.append(parsed)
        except ValueError as exc:
            errors.append(_issue(f"{path} has invalid shell quoting: {exc}"))
            continue
        if parsed and parsed[0].split("/")[-1] not in {"compliance-report", "set"}:
            errors.append(_issue(f"{path} may contain only packaged CLI invocations and shell safety settings."))
    if not any(
        argv and argv[0].split("/")[-1] in {"compliance-report", "python", "python3"}
        and any(arg in {"preview", "publish"} for arg in argv)
        for argv in commands
    ):
        errors.append(_issue(f"{path} must invoke the packaged compliance-report preview/publish CLI."))


def _expected_names(request: ReportCodeRequest) -> dict[str, str]:
    return {
        variant: request.report_names.get(variant, f"compliance-{variant.lower()}")
        for variant in request.variants
    }


def _objective_snapshot_map(snapshots: list[dict[str, Any]]) -> dict[str, Any]:
    result = {}
    for snapshot in snapshots:
        reference = snapshot.get("objective_ref")
        if not isinstance(reference, str) or not reference.strip() or "objective" not in snapshot:
            return {}
        result[reference] = snapshot["objective"]
    return result


def validate_compliance_report_code(request: Any, artifact: Any) -> dict[str, Any]:
    """Validate report executable syntax, target bindings and declared effects without running it."""
    errors: list[dict[str, str]] = []
    warnings: list[dict[str, str]] = []
    try:
        req = _validate_model(ReportCodeRequest, request)
        code = _validate_model(ReportCodeArtifact, artifact)
    except (ValidationError, TypeError, ValueError) as exc:
        detail = "; ".join(
            f"{'.'.join(map(str, e.get('loc', ())))}: {e.get('msg', str(exc))}"
            for e in getattr(exc, "errors", lambda: [])()[:8]
        ) or str(exc)
        return {"valid": False, "errors": [_issue(detail)], "warnings": [], "normalized": None}
    if _credential_fields({
        "runtime_context": req.runtime_context,
        "input_contract": req.input_contract,
    }):
        errors.append(_issue(
            "Credential values must not be included in code-generation inputs; use external runtime credentials."
        ))

    if code.status != "ready":
        return {
            "valid": True, "errors": [], "warnings": [],
            "normalized": code.model_dump(mode="json", exclude_none=True), "ready": False,
        }
    if req.strict_atomic:
        errors.append(_issue("Strict atomic publication is unavailable with the current DigitalHub adapter."))
    if req.mode == "combined" and req.language != "python":
        errors.append(_issue("Combined evaluator/report workflows currently require Python."))
    if req.mode == "combined" and not req.evaluator_artifacts:
        errors.append(_issue("Combined requests require ready evaluator artifacts for the requested objectives."))
    if req.mode == "combined" and any(item.status != "ready" for item in req.evaluator_artifacts):
        errors.append(_issue("Combined requests require ready evaluator artifacts for every objective."))
    if req.mode == "combined":
        snapshot_map = _objective_snapshot_map(req.objective_snapshots)
        evaluator_refs = {item.objective_ref for item in req.evaluator_artifacts if item.objective_ref}
        if not snapshot_map:
            errors.append(_issue("Combined requests require explicit objective_ref/objective snapshots."))
        if set(snapshot_map) != evaluator_refs:
            errors.append(_issue("Combined objective snapshots must exactly cover the evaluator artifacts."))
        for evaluator in req.evaluator_artifacts:
            contract = evaluator.entity_contract.model_dump(mode="json") if evaluator.entity_contract else {}
            if (
                contract.get("project") != req.project
                or contract.get("kind") not in (req.entity_kind, "dataitem" if req.entity_kind == "dataset" else None)
                or contract.get("name") != req.entity
                or contract.get("entity_version") != req.entity_version
            ):
                errors.append(_issue("Evaluator target must exactly match the report executable target."))
            if (
                evaluator.objective_ref not in snapshot_map
                or evaluator.objective != snapshot_map.get(evaluator.objective_ref)
            ):
                errors.append(_issue("Evaluator objective snapshot must exactly match the combined request snapshot."))
    if code.language != req.language or code.mode != req.mode:
        errors.append(_issue("Artifact language and mode must match the request."))
    expected_target = {"project": req.project, "entity_kind": req.entity_kind, "entity": req.entity}
    if req.entity_version is not None:
        expected_target["entity_version"] = req.entity_version
    if code.target != expected_target:
        errors.append(_issue("Artifact target must exactly match the explicitly requested project/entity."))
    expected_names = _expected_names(req)
    if any(not req.report_names.get(variant) for variant in req.variants):
        errors.append(_issue("Every requested report variant requires an explicit stable report name."))
    if code.report_names != expected_names:
        errors.append(_issue("Artifact report names must exactly match the request or the documented stable defaults."))
    if code.objective_snapshots != req.objective_snapshots:
        errors.append(_issue("Artifact objective snapshots must exactly match the request."))
    if code.input_contract != req.input_contract:
        errors.append(_issue("Artifact input contract must exactly match the request."))
    for variant, name in expected_names.items():
        effect = {
            "operation": "publish_report",
            "extension_kind": "compliance-report",
            "report_kind": variant,
            "report_name": name,
            **expected_target,
        }
        if effect not in code.declared_effects:
            errors.append(_issue(f"Artifact must declare its write effect for {variant} report '{name}'."))
    for effect in code.declared_effects:
        if (
            effect.get("extension_kind") != "compliance-report"
            or effect.get("project") != req.project
            or effect.get("entity_kind") != req.entity_kind
            or effect.get("entity") != req.entity
            or effect.get("report_name") not in expected_names.values()
        ):
            errors.append(_issue("Artifact declares a write outside the explicitly selected report target."))

    paths: set[str] = set()
    parsed_trees: dict[str, ast.Module] = {}
    for path, source in code.files.items():
        posix = PurePosixPath(path)
        if posix.is_absolute() or ".." in posix.parts or path in {"", "."}:
            errors.append(_issue(f"Artifact file path '{path}' must be a safe relative path."))
            continue
        paths.add(path)
        if code.language == "python" and posix.suffix == ".py":
            tree = _parse_python(path, source, errors)
            if tree:
                parsed_trees[path] = tree
                _check_python_side_effect_boundary(tree, allow_publication=True, errors=errors)
        elif code.language == "shell" and posix.suffix in {".sh", ""}:
            _check_shell(path, source, errors)
        elif code.language == "python":
            errors.append(_issue(f"Python artifact file '{path}' must use the .py extension."))
        else:
            errors.append(_issue(f"Shell artifact file '{path}' must use .sh or no extension."))
        declared_hash = code.source_hashes.get(path)
        actual_hash = hashlib.sha256(source.encode("utf-8")).hexdigest()
        if declared_hash is not None and declared_hash != actual_hash:
            errors.append(_issue(f"Source hash for '{path}' does not match the generated file."))
    if set(code.source_hashes) - paths:
        errors.append(_issue("Artifact source_hashes contain paths not present in the generated file bundle."))
    if code.entry_point not in paths:
        errors.append(_issue("entry_point must identify one of the generated files."))
    if code.language == "python" and code.entry_point in code.files:
        if code.entry_point not in parsed_trees:
            errors.append(_issue("Python entry_point is not a syntactically valid Python file."))
    if not any("preview" in command for command in code.invocation):
        errors.append(_issue("Invocation metadata must document a no-write preview command."))
    if not any("publish" in command for command in code.invocation):
        errors.append(_issue("Invocation metadata must document an explicit publish command."))

    if req.mode == "standalone":
        combined_source = "\n".join(code.files.values())
        if code.language == "python" and not any(
            "compliance_core.report_cli" in node.module if isinstance(node, ast.ImportFrom) and node.module
            else isinstance(node, ast.Import) and any(alias.name == "compliance_core.report_cli" for alias in node.names)
            for tree in parsed_trees.values() for node in ast.walk(tree)
        ):
            errors.append(_issue("Standalone Python artifact must use the packaged compliance_core.report_cli facade."))
        if code.language == "shell" and "compliance-report" not in combined_source:
            errors.append(_issue("Standalone shell artifact must use the packaged compliance-report CLI."))
    else:
        combined_source = "\n".join(code.files.values())
        runtime_calls = [
            node for tree in parsed_trees.values() for node in ast.walk(tree)
            if isinstance(node, ast.Call)
            and ((isinstance(node.func, ast.Name) and node.func.id == "run_report_workflow")
                 or (isinstance(node.func, ast.Attribute) and node.func.attr == "run_report_workflow"))
        ]
        if not runtime_calls:
            errors.append(_issue("Combined artifact must publish through shared run_report_workflow staging."))
        elif len(runtime_calls) != 1:
            errors.append(_issue("Combined artifact must stage the complete report set through exactly one runtime call."))
        else:
            call = runtime_calls[0]
            for call in runtime_calls:
                keywords = {item.arg: item.value for item in call.keywords if item.arg}
                if not call.args and "results" not in keywords:
                    errors.append(_issue("run_report_workflow must receive generated measurement results."))
                for key, expected in {
                    "project": req.project,
                    "entity_kind": req.entity_kind,
                    "entity": req.entity,
                }.items():
                    try:
                        actual = ast.literal_eval(keywords.get(key)) if key in keywords else None
                    except (ValueError, TypeError):
                        actual = None
                    if actual != expected:
                        errors.append(_issue(f"Combined runtime must bind '{key}' to the explicit request target."))
                if req.entity_version is not None:
                    try:
                        actual_version = ast.literal_eval(keywords.get("entity_version"))
                    except (ValueError, TypeError):
                        actual_version = None
                    if actual_version != req.entity_version:
                        errors.append(_issue("Combined runtime must bind entity_version to the requested target version."))
                try:
                    actual_variants = ast.literal_eval(keywords.get("variants")) if "variants" in keywords else None
                    actual_names = ast.literal_eval(keywords.get("names")) if "names" in keywords else None
                except (ValueError, TypeError):
                    actual_variants, actual_names = None, None
                if list(actual_variants or []) != req.variants:
                    errors.append(_issue("Combined runtime variants must exactly match the request."))
                if actual_names != expected_names:
                    errors.append(_issue("Combined runtime names must exactly match the requested report names."))
                if "mode" not in keywords:
                    errors.append(_issue("Combined runtime must expose preview/publish mode to the caller."))
            evaluator_names = {item.entry_point for item in req.evaluator_artifacts if item.entry_point}
            runtime_line = runtime_calls[0].lineno
            result_expression = (
                runtime_calls[0].args[0] if runtime_calls[0].args
                else {item.arg: item.value for item in runtime_calls[0].keywords if item.arg}.get("results")
            )
            result_calls = {
                node.func.id if isinstance(node.func, ast.Name) else
                node.func.attr if isinstance(node.func, ast.Attribute) else None
                for node in ast.walk(result_expression) if isinstance(node, ast.Call)
            } if result_expression is not None else set()
            result_lines = [
                node.lineno for node in ast.walk(result_expression)
                if isinstance(node, ast.Call)
                and (node.func.id if isinstance(node.func, ast.Name) else
                     node.func.attr if isinstance(node.func, ast.Attribute) else None) in evaluator_names
            ] if result_expression is not None else []
            if isinstance(result_expression, ast.Name):
                assigned = [
                    node.value for tree in parsed_trees.values() for node in ast.walk(tree)
                    if isinstance(node, (ast.Assign, ast.AnnAssign))
                    and node.lineno < runtime_line
                    and any(
                        isinstance(target, ast.Name) and target.id == result_expression.id
                        for target in (node.targets if isinstance(node, ast.Assign) else [node.target])
                    )
                ]
                for value in assigned:
                    result_calls.update(
                        node.func.id if isinstance(node.func, ast.Name) else
                        node.func.attr if isinstance(node.func, ast.Attribute) else None
                        for node in ast.walk(value) if isinstance(node, ast.Call)
                    )
                    result_lines.extend(
                        node.lineno for node in ast.walk(value)
                        if isinstance(node, ast.Call)
                        and (node.func.id if isinstance(node.func, ast.Name) else
                             node.func.attr if isinstance(node.func, ast.Attribute) else None) in evaluator_names
                    )
            if not evaluator_names.issubset(result_calls):
                errors.append(_issue("run_report_workflow must receive the collected output of every evaluator."))
            if not result_lines or any(line >= runtime_line for line in result_lines):
                errors.append(_issue("Every evaluator must run before the staged report publication call."))
        for evaluator in req.evaluator_artifacts:
            if evaluator.source_code and not any(evaluator.source_code in source for source in code.files.values()):
                errors.append(_issue(f"Combined artifact does not carry evaluator source for '{evaluator.entry_point}'."))
            if evaluator.entry_point and not re.search(
                rf"\b{re.escape(evaluator.entry_point)}\s*\(", combined_source,
            ):
                errors.append(_issue(f"Combined entry point does not call evaluator '{evaluator.entry_point}'."))
        imports_shared_runtime = any(
            (isinstance(node, ast.ImportFrom) and node.module == "compliance_core.report_cli")
            or (
                isinstance(node, ast.Import)
                and any(alias.name == "compliance_core.report_cli" for alias in node.names)
            )
            for tree in parsed_trees.values() for node in ast.walk(tree)
        )
        if not imports_shared_runtime:
            errors.append(_issue("Combined artifact must import the shared report CLI/runtime package."))

    normalized = code.model_dump(mode="json", exclude_none=True)
    normalized["source_hashes"] = {
        path: hashlib.sha256(source.encode("utf-8")).hexdigest()
        for path, source in code.files.items()
    }
    normalized["artifact_id"] = code.artifact_id or _hash({
        "request": req.model_dump(mode="json", exclude_none=True),
        "source_hashes": normalized["source_hashes"],
    })[:24]
    normalized["validation"] = {
        "valid": not errors,
        "static_only": True,
        "executed": False,
        "shell_syntax_only": code.language == "shell",
        "declared_effects_checked": True,
    }
    return {"valid": not errors, "errors": errors, "warnings": warnings, "normalized": normalized, "ready": True}


def record_compliance_report_code(
    env: ToolEnv, request: Any, artifact: Any, assumptions: list[str] | None = None,
) -> dict[str, Any]:
    """Validate and store a report executable, assumptions and metadata under its selected project."""
    validation = validate_compliance_report_code(request, artifact)
    if not validation["valid"] or not validation.get("ready"):
        return {**validation, "stored": False}
    req = _validate_model(ReportCodeRequest, request)
    normalized = validation["normalized"]
    with transaction(env.state):
        scoped_update(env.state, CODES_KEY, normalized["artifact_id"], {
            "request": req.model_dump(mode="json", exclude_none=True),
            "artifact": normalized,
            "assumptions": list(assumptions or []),
            "recorded_at": datetime.now(timezone.utc).isoformat(),
        }, req.project)
    return {**validation, "stored": True}


async def generate_compliance_report_code(env: ToolEnv, request: Any) -> dict[str, Any]:
    """Delegate generation of a standalone or combined executable; never run or publish it."""
    try:
        req = _validate_model(ReportCodeRequest, request)
    except (ValidationError, TypeError, ValueError) as exc:
        return {"error": str(exc), "code": "invalid_request"}
    if req.strict_atomic:
        artifact = ReportCodeArtifact(
            status="unsupported", language=req.language, mode=req.mode,
            unsupported_reasons=[
                "Strict atomic publication is not supported by the configured DigitalHub adapter."
            ],
        )
        return {"status": "unsupported", "artifact": artifact.model_dump(mode="json"), "assumptions": []}
    if req.mode == "combined" and req.language != "python":
        artifact = ReportCodeArtifact(
            status="unsupported", language=req.language, mode=req.mode,
            unsupported_reasons=["Combined evaluator/report generation currently requires Python."],
        )
        return {"status": "unsupported", "artifact": artifact.model_dump(mode="json"), "assumptions": []}
    if req.mode == "combined" and not req.evaluator_artifacts:
        artifact = ReportCodeArtifact(
            status="needs_input", language=req.language, mode=req.mode,
            missing_inputs=["ready evaluator artifact(s) for each selected objective"],
        )
        return {"status": "needs_input", "artifact": artifact.model_dump(mode="json"), "assumptions": []}
    unsupported = [
        reason
        for evaluator in req.evaluator_artifacts if evaluator.status == "unsupported"
        for reason in evaluator.unsupported_reasons
    ]
    if req.mode == "combined" and unsupported:
        artifact = ReportCodeArtifact(
            status="unsupported", language=req.language, mode=req.mode,
            unsupported_reasons=unsupported,
        )
        return {"status": "unsupported", "artifact": artifact.model_dump(mode="json"), "assumptions": []}
    missing_evaluator_inputs = [
        value
        for evaluator in req.evaluator_artifacts if evaluator.status == "needs_input"
        for value in evaluator.missing_inputs
    ]
    if req.mode == "combined" and missing_evaluator_inputs:
        artifact = ReportCodeArtifact(
            status="needs_input", language=req.language, mode=req.mode,
            missing_inputs=missing_evaluator_inputs,
        )
        return {"status": "needs_input", "artifact": artifact.model_dump(mode="json"), "assumptions": []}
    if req.mode == "combined":
        snapshot_map = _objective_snapshot_map(req.objective_snapshots)
        if not snapshot_map:
            artifact = ReportCodeArtifact(
                status="needs_input", language=req.language, mode=req.mode,
                missing_inputs=["explicit objective_ref/objective snapshots for every evaluator artifact"],
            )
            return {"status": "needs_input", "artifact": artifact.model_dump(mode="json"), "assumptions": []}
        evaluator_refs = {item.objective_ref for item in req.evaluator_artifacts if item.objective_ref}
        if set(snapshot_map) != evaluator_refs or any(
            item.objective_ref not in snapshot_map or item.objective != snapshot_map.get(item.objective_ref)
            for item in req.evaluator_artifacts
        ):
            return {
                "error": "Evaluator objectives do not match the explicitly requested objective snapshots.",
                "code": "objective_snapshot_mismatch",
            }
        if any(
            not item.entity_contract
            or item.entity_contract.project != req.project
            or item.entity_contract.name != req.entity
            or item.entity_contract.kind not in (req.entity_kind, "dataitem" if req.entity_kind == "dataset" else None)
            or item.entity_contract.entity_version != req.entity_version
            for item in req.evaluator_artifacts
        ):
            return {"error": "Evaluator target does not match the report executable target.",
                    "code": "target_mismatch"}
    missing = [f"report name for {variant}" for variant in req.variants if not req.report_names.get(variant)]
    if missing:
        artifact = ReportCodeArtifact(
            status="needs_input", language=req.language, mode=req.mode, missing_inputs=missing,
        )
        return {"status": "needs_input", "artifact": artifact.model_dump(mode="json"), "assumptions": []}

    if env.analysis_engine is None:
        return {"error": "The structured code-generation engine is not configured", "code": "integration_unavailable"}
    try:
        response = await env.analysis_engine.run("compliance_report_code", req)
    except ComplianceError as exc:
        return {"error": str(exc), "code": exc.code}
    output = response.data
    if isinstance(output, BaseModel):
        output = output.model_dump(mode="json")
    try:
        parsed = ReportCodeOutput.model_validate(output)
    except ValidationError as exc:
        return {"error": "The report-code engine returned an invalid response", "code": "invalid_output",
                "details": exc.errors(include_url=False)}
    validation = validate_compliance_report_code(req, parsed.result)
    if not validation["valid"]:
        return {"status": "invalid", "artifact": parsed.result.model_dump(mode="json", exclude_none=True),
                "assumptions": parsed.assumptions, "validation": validation}
    if validation.get("ready"):
        recorded = record_compliance_report_code(
            env, req, validation["normalized"], parsed.assumptions,
        )
        if not recorded.get("stored"):
            return {"status": "invalid", "artifact": validation["normalized"], "validation": recorded,
                    "assumptions": parsed.assumptions}
    return {
        "status": parsed.result.status,
        "artifact": validation["normalized"],
        "assumptions": parsed.assumptions,
        "validation": validation,
        "stored": bool(validation.get("ready")),
        "provenance": {
            "bundle_version": env.bundle.version,
            "model": getattr(response.meta, "model", None),
        },
    }


def validate_compliance_report_code_tool(env: ToolEnv, request: Any, artifact: Any) -> dict[str, Any]:
    """Statically validate an externally generated report artifact without executing it."""
    return validate_compliance_report_code(request, artifact)


def get_report_code_schema() -> dict[str, Any]:
    """Return the strict result-plus-assumptions schema for report executable artifacts."""
    return ReportCodeOutput.model_json_schema(mode="validation")


def get_session_report_codes(
    env: ToolEnv, project: str | None = None, artifact_id: str | None = None,
) -> dict[str, Any]:
    """Retrieve report executable artifacts already recorded in one project-scoped workspace."""
    scope = active_project(env.state) if project is None else project
    records = scoped_get(env.state, CODES_KEY, scope)
    if artifact_id:
        found = records.get(artifact_id)
        if not found or not (found.get("artifact") or {}).get("files"):
            return {"error": f"No report code artifact '{artifact_id}' in project '{scope or ''}'.",
                    "code": "not_found"}
        items = {artifact_id: found}
    else:
        items = {
            key: value for key, value in records.items()
            if (value.get("artifact") or {}).get("files")
        }
    return {
        "active_project": active_project(env.state),
        "project": scope,
        "projects": [
            name for name in known_projects(env.state)
            if scoped_get(env.state, CODES_KEY, name)
        ],
        "artifacts": items,
    }


REPORT_CODE_TOOL_SPECS = (
    ToolSpec("generate_compliance_report_code", generate_compliance_report_code, "analysis",
             generate_compliance_report_code.__doc__ or "", False, needs_llm=True),
    ToolSpec("get_report_code_schema", get_report_code_schema, "validation",
             get_report_code_schema.__doc__ or "", True),
    ToolSpec("get_session_report_codes", get_session_report_codes, "session",
             get_session_report_codes.__doc__ or "", True),
    ToolSpec("validate_compliance_report_code", validate_compliance_report_code_tool, "validation",
             validate_compliance_report_code_tool.__doc__ or "", True),
    ToolSpec("record_compliance_report_code", record_compliance_report_code, "validation",
             record_compliance_report_code.__doc__ or "", False),
)
TOOL_SPECS = REPORT_CODE_TOOL_SPECS
TOOL_REGISTRY = {spec.name: spec for spec in TOOL_SPECS}

__all__ = [
    "REPORT_CODE_TOOL_SPECS",
    "TOOL_REGISTRY",
    "TOOL_SPECS",
    "generate_compliance_report_code",
    "get_report_code_schema",
    "get_session_report_codes",
    "record_compliance_report_code",
    "validate_compliance_report_code",
    "validate_compliance_report_code_tool",
]
