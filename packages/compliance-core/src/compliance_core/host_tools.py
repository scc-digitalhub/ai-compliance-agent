# SPDX-FileCopyrightText: © 2026 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

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
from .provenance import build_provenance, set_provenance
from .validation import grounding_issues
from .state import (
    CONTEXT_KEY, DATASETS_KEY, MODELS_KEY, PROJECT_KEY, activate_project, scoped_update, transaction,
)
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
    env: ToolEnv, kind: AnalysisKind, request: Any, output: Any,
    grounding: list[str] | None = None,
) -> dict[str, Any]:
    """Validate a host-generated analysis and store valid results in workspace state.

    Results are stored in the scope of the request's project (or the active project), together with
    provenance: OKF version, consulted OKF paths, assumptions and validation warnings. This does not
    call an LLM or write to DigitalHub. Use save_compliance_specification separately when the user
    asks to persist a recorded result to DigitalHub.

    Args:
        kind: Analysis type: 'project', 'dataset', or 'model'.
        request: Original validated analysis input.
        output: Host-generated structured output matching the kind's output schema.
        grounding: Required. OKF concept paths read to produce the result, for example
            catalog/requirements/eu-ai-act/art14-human-oversight.md; each must exist in the bundle.
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
    cited = grounding_issues(grounding, env.bundle)
    if cited:
        errors = [{"message": issue.message} for issue in cited]
        return {**validation, "valid": False, "errors": errors, "stored": False}
    grounding = [path.strip().lstrip("/") for path in grounding]

    parsed_request = _parse_request(kind, request)
    parsed_output = _OUTPUT_MODELS[kind].model_validate(validation["normalized"])
    result = parsed_output.result.model_dump(mode="json")
    provenance = build_provenance(
        "host", env.bundle.version, grounding=grounding,
        assumptions=parsed_output.assumptions,
        warnings=[warning["message"] for warning in validation["warnings"]],
    )

    with transaction(env.state):
        if kind == "project":
            activate_project(env.state, parsed_request.name)
            env.state[PROJECT_KEY] = parsed_request.model_dump(mode="json")
            env.state[CONTEXT_KEY] = result
            set_provenance(env.state, kind, parsed_request.name, provenance)
        else:
            entity = parsed_request.dataset if kind == "dataset" else parsed_request.model
            project = parsed_request.project.name if parsed_request.project else None
            scoped_update(env.state, DATASETS_KEY if kind == "dataset" else MODELS_KEY,
                          entity.name, result, project)
            set_provenance(env.state, kind, entity.name, provenance, project)

    return {**validation, "stored": True, "provenance": provenance}


RECORD_ANALYSIS_TOOL_SPEC = ToolSpec(
    name="record_compliance_analysis",
    fn=record_compliance_analysis,
    group="validation",
    description=record_compliance_analysis.__doc__ or "",
    read_only=False,
)

__all__ = ["RECORD_ANALYSIS_TOOL_SPEC", "record_compliance_analysis"]
