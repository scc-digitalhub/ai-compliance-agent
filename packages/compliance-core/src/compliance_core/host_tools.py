"""Tools for host-driven compliance analyses."""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel

from .contracts import (
    DatasetAnalysisRequest,
    DatasetAgentOutput,
    ModelAnalysisRequest,
    ModelAgentOutput,
    ProjectContextAgentOutput,
    ProjectInput,
)
from .state import CONTEXT_KEY, DATASETS_KEY, MODELS_KEY, PROJECT_KEY
from .tools import ToolEnv, ToolSpec
from .validation_tools import (
    AnalysisKind,
    validate_dataset_compliance,
    validate_model_compliance,
    validate_project_context,
)


def _parse_request(kind: AnalysisKind, request: Any) -> BaseModel:
    request_model = _REQUEST_MODELS[kind]
    if isinstance(request, str):
        return request_model.model_validate_json(request)
    return request_model.model_validate(request)


_REQUEST_MODELS: dict[AnalysisKind, type[BaseModel]] = {
    "project": ProjectInput,
    "dataset": DatasetAnalysisRequest,
    "model": ModelAnalysisRequest,
}
_OUTPUT_MODELS: dict[AnalysisKind, type[BaseModel]] = {
    "project": ProjectContextAgentOutput,
    "dataset": DatasetAgentOutput,
    "model": ModelAgentOutput,
}
_VALIDATORS = {
    "project": validate_project_context,
    "dataset": validate_dataset_compliance,
    "model": validate_model_compliance,
}


def record_compliance_analysis(
    env: ToolEnv, kind: AnalysisKind, request: Any, output: Any
) -> dict[str, Any]:
    """Validate a host-generated analysis and store valid results in workspace state.

    This does not call an LLM or write to DigitalHub. Use save_compliance_specification
    separately when the user asks to persist a recorded result to DigitalHub.

    Args:
        kind: Analysis type: 'project', 'dataset', or 'model'.
        request: Original validated analysis input.
        output: Host-generated structured output matching the kind's output schema.
    """
    if kind not in _VALIDATORS:
        return {
            "valid": False,
            "errors": [{"message": f"Unknown analysis kind '{kind}'"}],
            "warnings": [],
            "stored": False,
        }

    validation = _VALIDATORS[kind](request, output, env.bundle)
    if not validation["valid"]:
        return {**validation, "stored": False}

    parsed_request = _parse_request(kind, request)
    parsed_output = _OUTPUT_MODELS[kind].model_validate(validation["normalized"])
    result = parsed_output.result.model_dump(mode="json")

    if kind == "project":
        env.state[PROJECT_KEY] = parsed_request.model_dump(mode="json")
        env.state[CONTEXT_KEY] = result
    elif kind == "dataset":
        name = parsed_request.dataset.name
        env.state[DATASETS_KEY] = {
            **env.state.get(DATASETS_KEY, {}),
            name: result,
        }
    else:
        name = parsed_request.model.name
        env.state[MODELS_KEY] = {
            **env.state.get(MODELS_KEY, {}),
            name: result,
        }

    return {**validation, "stored": True}


RECORD_ANALYSIS_TOOL_SPEC = ToolSpec(
    name="record_compliance_analysis",
    fn=record_compliance_analysis,
    group="validation",
    description=record_compliance_analysis.__doc__ or "",
    read_only=False,
)

__all__ = ["RECORD_ANALYSIS_TOOL_SPEC", "record_compliance_analysis"]
