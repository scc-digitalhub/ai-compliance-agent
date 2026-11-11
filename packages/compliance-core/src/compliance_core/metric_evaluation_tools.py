"""Grounded generation, static validation and workspace recording of evaluator code.

Generated source is parsed as text only. This module never imports, compiles, or executes it.
"""
from __future__ import annotations

import ast
import hashlib
import json
from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, ValidationError

from .contracts.evaluation_code import (
    MetricEvaluationCodeArtifact,
    MetricEvaluationCodeOutput,
    MetricEvaluationCodeRequest,
)
from .errors import ComplianceError
from .metric_computation import resolve_metric_computation
from .state import CODES_KEY, active_project, known_projects, scoped_get, scoped_update, transaction
from .tools import ToolEnv, ToolSpec

_BLOCKED_IMPORTS = {
    "builtins", "importlib", "multiprocessing", "os", "pathlib", "pickle", "requests",
    "shutil", "socket", "subprocess", "tempfile", "urllib",
}
_BLOCKED_CALLS = {
    "__import__", "compile", "delattr", "eval", "exec", "open", "print", "setattr",
    "system", "popen", "write_text", "write_bytes", "to_csv", "to_excel",
}
_CREDENTIAL_KEYS = {
    "password", "secret", "credential", "credentials", "token", "access_token",
    "api_key", "client_secret",
}
_OUTPUT_MODELS: dict[str, type[BaseModel]] = {
    "request": MetricEvaluationCodeRequest,
    "artifact": MetricEvaluationCodeArtifact,
}


def _validate_model(model: type[BaseModel], value: Any) -> BaseModel:
    if isinstance(value, str):
        return model.model_validate_json(value)
    if isinstance(value, BaseModel):
        return model.model_validate(value.model_dump(mode="json"))
    return model.model_validate(value)


def _metric_id(objective: dict[str, Any]) -> str | None:
    metric = objective.get("metric")
    return metric.get("id") if isinstance(metric, dict) and isinstance(metric.get("id"), str) else None


def _has_explicit_data_binding(request: MetricEvaluationCodeRequest) -> bool:
    keys = {key.casefold() for key in request.bindings}
    data_keys = {
        "data", "dataset", "dataframe", "frame", "table", "records", "data_source",
        "data_path", "input_data", "entity_data", "data_item", "evaluation_data",
        "x", "features", "y_true", "y_pred", "labels", "predictions",
    }
    return bool(keys & data_keys) or bool(request.evaluation_data)


def _credential_fields(value: Any, prefix: str = "") -> list[str]:
    found = []
    if isinstance(value, dict):
        for key, child in value.items():
            path = f"{prefix}.{key}" if prefix else str(key)
            normalized = str(key).casefold().replace("-", "_")
            if normalized in _CREDENTIAL_KEYS and not normalized.endswith("_env"):
                found.append(path)
            found.extend(_credential_fields(child, path))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            found.extend(_credential_fields(child, f"{prefix}[{index}]"))
    return found


def _hash(value: Any) -> str:
    serialized = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, default=str)
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def _issue(message: str) -> dict[str, str]:
    return {"message": message}


def validate_metric_evaluation_code(request: Any, artifact: Any) -> dict[str, Any]:
    """Statically validate an evaluator artifact against its explicit request.

    Validation is intentionally conservative and never imports or executes generated source.
    """
    errors: list[dict[str, str]] = []
    warnings: list[dict[str, str]] = []
    try:
        parsed_request = _validate_model(MetricEvaluationCodeRequest, request)
        parsed_artifact = _validate_model(MetricEvaluationCodeArtifact, artifact)
    except (ValidationError, TypeError, ValueError) as exc:
        detail = "; ".join(
            f"{'.'.join(map(str, e.get('loc', ())))}: {e.get('msg', str(exc))}"
            for e in getattr(exc, "errors", lambda: [])()[:8]
        ) or str(exc)
        return {"valid": False, "errors": [_issue(detail)], "warnings": [], "normalized": None}

    req: MetricEvaluationCodeRequest = parsed_request  # type: ignore[assignment]
    code: MetricEvaluationCodeArtifact = parsed_artifact  # type: ignore[assignment]
    credential_fields = _credential_fields({
        "bindings": req.bindings,
        "evaluation_data": req.evaluation_data,
    })
    if credential_fields:
        errors.append(_issue(
            "Credential values must not be included in code-generation inputs; use external runtime credentials."
        ))
    if code.objective_ref not in (None, req.objective_ref):
        errors.append(_issue("Artifact objective_ref must match the request."))
    if code.objective not in (None, req.objective):
        errors.append(_issue("Artifact objective snapshot must exactly match the request."))
    expected_metric = _metric_id(req.objective)
    if code.metric is not None and code.metric != req.objective.get("metric"):
        errors.append(_issue("Artifact metric snapshot must exactly match the selected objective metric."))
    if code.status != "ready":
        return {
            "valid": not errors, "errors": errors, "warnings": warnings,
            "normalized": code.model_dump(mode="json", exclude_none=True),
            "ready": False,
        }

    actual_metric = (code.metric or {}).get("id") if isinstance(code.metric, dict) else None
    if expected_metric is None or actual_metric != expected_metric or code.metric != req.objective.get("metric"):
        errors.append(_issue("Artifact metric identity must match the selected objective metric."))
    if code.result_contract.get("title") != "MeasurementEnvelope" and code.result_contract.get("type") != "MeasurementEnvelope":
        errors.append(_issue("Evaluator result_contract must describe the shared MeasurementEnvelope contract."))
    guidance = req.computation_guidance
    if not guidance.get("source_path") or guidance.get("status") == "unsupported":
        errors.append(_issue("Ready evaluator requests must include supported OKF computation guidance."))
    elif guidance.get("metric", {}).get("instance", {}).get("id") != expected_metric:
        errors.append(_issue("Resolved computation guidance does not match the objective metric."))
    entity_contract = code.entity_contract.model_dump(mode="json") if code.entity_contract else {}
    if entity_contract.get("kind") not in (req.entity_kind, "dataitem" if req.entity_kind == "dataset" else None):
        errors.append(_issue("Artifact entity contract has the wrong entity kind."))
    if entity_contract.get("name") != req.entity:
        errors.append(_issue("Artifact entity contract does not match the requested entity."))
    if entity_contract.get("project") != req.project:
        errors.append(_issue("Artifact entity contract does not match the requested project."))
    if entity_contract.get("entity_version") != req.entity_version:
        errors.append(_issue("Artifact entity contract does not match the requested entity version."))
    if entity_contract.get("read_only") is not True:
        errors.append(_issue("Evaluator entity interface must be declared read-only."))
    for field in entity_contract.get("fields", {}):
        if field not in req.bindings and field not in (req.evaluation_data or {}):
            errors.append(_issue(f"Entity interface field '{field}' has no explicit request binding."))
    if guidance.get("source_path"):
        expected_path = guidance["source_path"]
        if expected_path not in code.source_paths:
            errors.append(_issue("Artifact must cite the resolved metric computation source path."))
        if set(code.source_paths) != {expected_path}:
            errors.append(_issue("Artifact source_paths must contain only the resolved computation source."))
        if guidance.get("source_hash") and code.source_hashes.get(expected_path) != guidance["source_hash"]:
            errors.append(_issue("Artifact must preserve the computation source hash."))
        if set(code.source_hashes) - {expected_path}:
            errors.append(_issue("Artifact source_hashes contain paths outside the resolved computation source."))
        if code.bundle_version != guidance.get("bundle_version"):
            errors.append(_issue("Artifact bundle_version must match the resolved computation guidance."))
    for parameter, binding in code.parameters.items():
        if parameter not in req.bindings and binding != req.evaluation_data:
            errors.append(_issue(f"Artifact parameter '{parameter}' has no explicit request binding."))
    if req.entity_kind == "model" and req.evaluation_data is None and not req.bindings:
        errors.append(_issue("Model evaluation requires explicit evaluation data, labels/predictions, or bindings."))

    try:
        tree = ast.parse(code.source_code or "", filename=f"<{code.entry_point or 'evaluator'}>", mode="exec")
    except (SyntaxError, ValueError) as exc:
        errors.append(_issue(f"Generated Python is not syntactically valid: {exc}"))
        tree = None

    if tree is not None:
        for node in tree.body:
            if isinstance(node, (ast.Import, ast.ImportFrom, ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            if isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
                continue
            errors.append(_issue("Evaluator modules may contain only imports and function definitions at module scope."))
        functions = [
            node for node in tree.body
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == code.entry_point
        ]
        if len(functions) != 1 or not isinstance(functions[0], ast.FunctionDef):
            errors.append(_issue("entry_point must name one top-level synchronous Python function."))
        else:
            function = functions[0]
            args = [arg.arg for arg in function.args.posonlyargs + function.args.args]
            if not args or args[0] != "entity":
                errors.append(_issue("Evaluator entry point must take the assessed entity as its first argument."))
            if not any(isinstance(node, ast.Return) for node in ast.walk(function)):
                errors.append(_issue("Evaluator entry point must return its structured measurement result."))

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                modules = [alias.name.split(".", 1)[0] for alias in node.names]
            elif isinstance(node, ast.ImportFrom):
                modules = [(node.module or "").split(".", 1)[0]]
            else:
                modules = []
            if any(name in _BLOCKED_IMPORTS for name in modules):
                errors.append(_issue("Evaluator source imports a prohibited side-effect or dynamic-loading module."))
            if isinstance(node, ast.Call):
                name = node.func.id if isinstance(node.func, ast.Name) else (
                    node.func.attr if isinstance(node.func, ast.Attribute) else ""
                )
                if name in _BLOCKED_CALLS:
                    errors.append(_issue(f"Evaluator source calls prohibited side-effect function '{name}'."))
                if isinstance(node.func, ast.Attribute) and name in {"save", "update", "delete", "publish", "attach"}:
                    errors.append(_issue(f"Evaluator source may not publish or mutate through '{name}'."))
                if isinstance(node.func, ast.Attribute) and name in {"clear", "pop", "popitem", "setdefault", "append", "extend", "insert", "remove"}:
                    root = node.func.value
                    while isinstance(root, (ast.Attribute, ast.Subscript)):
                        root = root.value
                    if isinstance(root, ast.Name) and root.id == "entity":
                        errors.append(_issue("Evaluator source may not mutate the assessed entity."))
            if isinstance(node, (ast.Assign, ast.AnnAssign, ast.AugAssign, ast.Delete)):
                targets = node.targets if isinstance(node, ast.Assign) else [node.target] if hasattr(node, "target") else node.targets
                def check_target(target: ast.AST) -> None:
                    if isinstance(target, (ast.Tuple, ast.List)):
                        for item in target.elts:
                            check_target(item)
                        return
                    root = target
                    while isinstance(root, (ast.Attribute, ast.Subscript)):
                        root = root.value
                    if isinstance(root, ast.Name) and root.id == "entity":
                        errors.append(_issue("Evaluator source may not assign to or delete from the assessed entity."))
                for target in targets:
                    check_target(target)

    if code.source_hash and code.source_hash != hashlib.sha256((code.source_code or "").encode()).hexdigest():
        errors.append(_issue("Artifact source_hash does not match source_code."))
    if not code.source_hash:
        warnings.append(_issue("Artifact omitted source_hash; a canonical hash was computed during validation."))
    normalized = code.model_dump(mode="json", exclude_none=True)
    normalized["source_hash"] = hashlib.sha256((code.source_code or "").encode()).hexdigest()
    normalized["artifact_id"] = code.artifact_id or _hash({
        "request": req.model_dump(mode="json", exclude_none=True),
        "source_hash": normalized["source_hash"],
    })[:24]
    normalized["validation"] = {
        "valid": not errors,
        "static_only": True,
        "executed": False,
        "warnings": [item["message"] for item in warnings],
    }
    return {"valid": not errors, "errors": errors, "warnings": warnings, "normalized": normalized, "ready": True}


def get_metric_computation(env: ToolEnv, metric_id: str, entity_kind: str | None = None) -> dict[str, Any]:
    """Retrieve the exact metric computation text and code examples from the OKF bundle."""
    result = resolve_metric_computation(env.bundle, metric_id, entity_kind=entity_kind)
    source_path = result.get("source_path")
    if source_path and env.grounding is not None:
        env.grounding.record(source_path)
    return result


def get_evaluation_schema() -> dict[str, Any]:
    """Return the strict result-plus-assumptions schema for generated evaluator artifacts."""
    return MetricEvaluationCodeOutput.model_json_schema(mode="validation")


def get_session_evaluation_codes(
    env: ToolEnv, project: str | None = None, artifact_id: str | None = None,
) -> dict[str, Any]:
    """Retrieve evaluator artifacts already recorded in one project-scoped workspace."""
    scope = active_project(env.state) if project is None else project
    records = scoped_get(env.state, CODES_KEY, scope)
    if artifact_id:
        found = records.get(artifact_id)
        if not found or not (found.get("artifact") or {}).get("source_code"):
            return {"error": f"No evaluator code artifact '{artifact_id}' in project '{scope or ''}'.",
                    "code": "not_found"}
        items = {artifact_id: found}
    else:
        items = {
            key: value for key, value in records.items()
            if (value.get("artifact") or {}).get("source_code")
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


def record_metric_evaluation_code(
    env: ToolEnv, request: Any, artifact: Any, assumptions: list[str] | None = None,
) -> dict[str, Any]:
    """Validate and store an evaluator artifact, assumptions and metadata in project-scoped state."""
    validation = validate_metric_evaluation_code(request, artifact)
    if not validation["valid"] or not validation.get("ready"):
        return {**validation, "stored": False}
    parsed_request = _validate_model(MetricEvaluationCodeRequest, request)
    normalized = validation["normalized"]
    record = {
        "request": parsed_request.model_dump(mode="json", exclude_none=True),
        "artifact": normalized,
        "assumptions": list(assumptions or []),
        "recorded_at": datetime.now(timezone.utc).isoformat(),
    }
    project = parsed_request.project
    with transaction(env.state):
        scoped_update(env.state, CODES_KEY, normalized["artifact_id"], record, project)
    return {**validation, "stored": True}


async def generate_metric_evaluation_code(env: ToolEnv, request: Any) -> dict[str, Any]:
    """Delegate grounded evaluator-source drafting to the configured structured engine."""
    try:
        parsed_request = _validate_model(MetricEvaluationCodeRequest, request)
    except (ValidationError, TypeError, ValueError) as exc:
        return {"error": str(exc), "code": "invalid_request"}
    credential_fields = _credential_fields({
        "bindings": parsed_request.bindings,
        "evaluation_data": parsed_request.evaluation_data,
    })
    if credential_fields:
        return {
            "error": "Credential values must not be included in code-generation inputs; use external runtime credentials.",
            "code": "credentials_in_request",
        }

    metric_id = _metric_id(parsed_request.objective)
    if not metric_id:
        return {
            "status": "unsupported",
            "artifact": {
                "status": "unsupported",
                "unsupported_reasons": ["Selected objective has no catalog metric id."],
            },
            "assumptions": [],
        }
    computation = get_metric_computation(env, metric_id, parsed_request.entity_kind)
    parsed_request.computation_guidance = computation
    if computation.get("status") == "unsupported":
        artifact = MetricEvaluationCodeArtifact(
            status="unsupported", objective_ref=parsed_request.objective_ref,
            objective=parsed_request.objective, metric=parsed_request.objective.get("metric"),
            source_paths=[computation["source_path"]] if computation.get("source_path") else [],
            bundle_version=env.bundle.version,
            unsupported_reasons=[computation.get("reason", "No supported computation is available.")],
        )
        return {"status": artifact.status, "artifact": artifact.model_dump(mode="json"), "assumptions": []}

    missing: list[str] = []
    if not _has_explicit_data_binding(parsed_request):
        missing.append("explicit input bindings (data location/interface and required columns or parameters)")
    if parsed_request.entity_kind == "model" and parsed_request.evaluation_data is None and not _has_explicit_data_binding(parsed_request):
        missing.append("evaluation data, labels/predictions, or an explicit evaluation-data interface")
    if missing:
        artifact = MetricEvaluationCodeArtifact(
            status="needs_input", objective_ref=parsed_request.objective_ref,
            objective=parsed_request.objective, metric=parsed_request.objective.get("metric"),
            source_paths=[computation["source_path"]], source_hashes={computation["source_path"]: computation["source_hash"]},
            bundle_version=env.bundle.version, missing_inputs=missing,
        )
        return {"status": artifact.status, "artifact": artifact.model_dump(mode="json"), "assumptions": []}

    if env.analysis_engine is None:
        return {"error": "The structured code-generation engine is not configured", "code": "integration_unavailable"}
    try:
        response = await env.analysis_engine.run("metric_evaluation_code", parsed_request)
    except ComplianceError as exc:
        return {"error": str(exc), "code": exc.code}
    output = response.data
    if isinstance(output, BaseModel):
        output = output.model_dump(mode="json")
    try:
        parsed_output = MetricEvaluationCodeOutput.model_validate(output)
    except ValidationError as exc:
        return {"error": "The code-generation engine returned an invalid response", "code": "invalid_output",
                "details": exc.errors(include_url=False)}
    validation = validate_metric_evaluation_code(parsed_request, parsed_output.result)
    if not validation["valid"]:
        return {
            "status": "invalid",
            "artifact": parsed_output.result.model_dump(mode="json", exclude_none=True),
            "assumptions": parsed_output.assumptions,
            "validation": validation,
        }
    if validation.get("ready"):
        stored = record_metric_evaluation_code(
            env, parsed_request, validation["normalized"], parsed_output.assumptions,
        )
        if not stored.get("stored"):
            return {"status": "invalid", "artifact": validation["normalized"], "validation": stored,
                    "assumptions": parsed_output.assumptions}
    return {
        "status": parsed_output.result.status,
        "artifact": validation["normalized"],
        "assumptions": parsed_output.assumptions,
        "validation": validation,
        "stored": bool(validation.get("ready")),
        "provenance": {
            "bundle_version": env.bundle.version,
            "grounding": parsed_output.result.source_paths,
            "model": getattr(response.meta, "model", None),
        },
    }


def validate_metric_evaluation_code_tool(env: ToolEnv, request: Any, artifact: Any) -> dict[str, Any]:
    """Check a host-generated evaluator artifact without executing it."""
    return validate_metric_evaluation_code(request, artifact)


METRIC_COMPUTATION_TOOL_SPEC = ToolSpec(
    name="get_metric_computation",
    fn=get_metric_computation,
    group="knowledge",
    description=get_metric_computation.__doc__ or "",
    read_only=True,
)
EVALUATION_SCHEMA_TOOL_SPEC = ToolSpec(
    name="get_evaluation_schema",
    fn=get_evaluation_schema,
    group="validation",
    description=get_evaluation_schema.__doc__ or "",
    read_only=True,
)
SESSION_EVALUATION_CODES_TOOL_SPEC = ToolSpec(
    name="get_session_evaluation_codes",
    fn=get_session_evaluation_codes,
    group="session",
    description=get_session_evaluation_codes.__doc__ or "",
    read_only=True,
)
METRIC_EVALUATION_CODE_TOOL_SPEC = ToolSpec(
    name="generate_metric_evaluation_code",
    fn=generate_metric_evaluation_code,
    group="analysis",
    description=generate_metric_evaluation_code.__doc__ or "",
    read_only=False,
    needs_llm=True,
)
VALIDATE_METRIC_EVALUATION_CODE_TOOL_SPEC = ToolSpec(
    name="validate_metric_evaluation_code",
    fn=validate_metric_evaluation_code_tool,
    group="validation",
    description=validate_metric_evaluation_code_tool.__doc__ or "",
    read_only=True,
)
RECORD_METRIC_EVALUATION_CODE_TOOL_SPEC = ToolSpec(
    name="record_metric_evaluation_code",
    fn=record_metric_evaluation_code,
    group="validation",
    description=record_metric_evaluation_code.__doc__ or "",
    read_only=False,
)

TOOL_SPECS = (
    METRIC_COMPUTATION_TOOL_SPEC,
    EVALUATION_SCHEMA_TOOL_SPEC,
    SESSION_EVALUATION_CODES_TOOL_SPEC,
    METRIC_EVALUATION_CODE_TOOL_SPEC,
    VALIDATE_METRIC_EVALUATION_CODE_TOOL_SPEC,
    RECORD_METRIC_EVALUATION_CODE_TOOL_SPEC,
)
TOOL_REGISTRY = {spec.name: spec for spec in TOOL_SPECS}

__all__ = [
    "METRIC_COMPUTATION_TOOL_SPEC",
    "METRIC_EVALUATION_CODE_TOOL_SPEC",
    "EVALUATION_SCHEMA_TOOL_SPEC",
    "SESSION_EVALUATION_CODES_TOOL_SPEC",
    "RECORD_METRIC_EVALUATION_CODE_TOOL_SPEC",
    "TOOL_REGISTRY",
    "TOOL_SPECS",
    "VALIDATE_METRIC_EVALUATION_CODE_TOOL_SPEC",
    "generate_metric_evaluation_code",
    "get_evaluation_schema",
    "get_metric_computation",
    "get_session_evaluation_codes",
    "record_metric_evaluation_code",
    "validate_metric_evaluation_code",
    "validate_metric_evaluation_code_tool",
]
