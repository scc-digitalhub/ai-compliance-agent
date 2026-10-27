"""Host-callable schema and semantic validation helpers for host-driven analysis."""
from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ValidationError

from .contracts import (
    DatasetAnalysisRequest,
    DatasetAgentOutput,
    ModelAnalysisRequest,
    ModelAgentOutput,
    ProjectContextAgentOutput,
    ProjectInput,
)
from .knowledge import OkfBundle
from .validation import Issue, validate_context, validate_dataset, validate_model

AnalysisKind = Literal["project", "dataset", "model"]

_OUTPUT_MODELS: dict[str, type[BaseModel]] = {
    "project": ProjectContextAgentOutput,
    "dataset": DatasetAgentOutput,
    "model": ModelAgentOutput,
}


def get_output_schema(kind: AnalysisKind) -> dict[str, Any]:
    """Return the JSON Schema a host model must follow for an analysis result."""
    return _OUTPUT_MODELS[kind].model_json_schema()


def _parse(model: type[BaseModel], value: Any) -> BaseModel:
    if isinstance(value, str):
        return model.model_validate_json(value)
    return model.model_validate(value)


def _validation_errors(exc: ValidationError) -> list[dict[str, str]]:
    return [
        {
            "path": ".".join(str(part) for part in error["loc"]),
            "message": error["msg"],
        }
        for error in exc.errors()
    ]


def _validate(
    request_model: type[BaseModel],
    output_model: type[BaseModel],
    validator: Any,
    request: Any,
    output: Any,
    bundle: OkfBundle,
) -> dict[str, Any]:
    try:
        parsed_request = _parse(request_model, request)
        parsed_output = _parse(output_model, output)
    except ValidationError as exc:
        return {"valid": False, "errors": _validation_errors(exc), "warnings": []}

    issues: list[Issue] = validator(parsed_output.result, parsed_request, bundle)
    errors = [{"message": issue.message} for issue in issues if issue.severity == "error"]
    warnings = [{"message": issue.message} for issue in issues if issue.severity == "warning"]
    return {
        "valid": not errors,
        "errors": errors,
        "warnings": warnings,
        "normalized": parsed_output.model_dump(mode="json"),
    }


def validate_project_context(
    request: Any, output: Any, bundle: OkfBundle
) -> dict[str, Any]:
    """Check a host-generated project context against its schema and OKF semantics."""
    return _validate(
        ProjectInput, ProjectContextAgentOutput, validate_context, request, output, bundle
    )


def validate_dataset_compliance(
    request: Any, output: Any, bundle: OkfBundle
) -> dict[str, Any]:
    """Check a host-generated dataset result against its schema and OKF semantics."""
    return _validate(
        DatasetAnalysisRequest, DatasetAgentOutput, validate_dataset, request, output, bundle
    )


def validate_model_compliance(
    request: Any, output: Any, bundle: OkfBundle
) -> dict[str, Any]:
    """Check a host-generated model result against its schema and OKF semantics."""
    return _validate(
        ModelAnalysisRequest, ModelAgentOutput, validate_model, request, output, bundle
    )


__all__ = [
    "AnalysisKind",
    "get_output_schema",
    "validate_dataset_compliance",
    "validate_model_compliance",
    "validate_project_context",
]
