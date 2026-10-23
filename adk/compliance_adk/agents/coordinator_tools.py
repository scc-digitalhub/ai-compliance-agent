"""Tools that let the coordinator run the same structured agents as the API.

Results are kept in session state so follow-up questions reuse them and later analyses receive the
earlier ones (project context into dataset and model analysis) without the LLM re-sending them.
"""
from __future__ import annotations

from typing import Any, Optional, TypeVar

from google.adk.tools import ToolContext
from pydantic import BaseModel

from ..contracts import (
    AnalysisResponse,
    ComplianceContextOut,
    DataComplianceOut,
    DatasetAnalysisRequest,
    DatasetInput,
    ModelAnalysisRequest,
    ModelInput,
    ProjectInput,
)
from ..errors import ComplianceAdkError
from ..runtime import get_registry
from .session_state import CONTEXT_KEY, DATASETS_KEY, MODELS_KEY, PROJECT_KEY
from .specification_tools import get_compliance_specification

InputModel = TypeVar("InputModel", bound=BaseModel)


def _normalize_input(model_type: type[InputModel], value: Any) -> InputModel:
    if isinstance(value, str):
        return model_type.model_validate_json(value)
    return model_type.model_validate(value)


async def _run(agent_key: str, request: BaseModel) -> AnalysisResponse[Any] | dict[str, str]:
    try:
        return await get_registry().get(agent_key).run(request)
    except ComplianceAdkError as exc:
        return {"error": str(exc), "code": exc.code}


def _payload(response: AnalysisResponse[Any]) -> dict[str, Any]:
    return {
        "data": response.data.model_dump(mode="json"),
        "assumptions": response.meta.assumptions,
        "warnings": response.meta.warnings,
        "grounding": response.meta.grounding,
    }


def _stored_context(state: Any) -> Optional[ComplianceContextOut]:
    raw = state.get(CONTEXT_KEY)
    return ComplianceContextOut.model_validate(raw) if raw else None


def _stored_project(state: Any) -> Optional[ProjectInput]:
    raw = state.get(PROJECT_KEY)
    return ProjectInput.model_validate(raw) if raw else None


def _stored_on_dh(kind: str, entity: str, tool_context: ToolContext) -> Optional[dict[str, Any]]:
    """The specification already stored on the DH platform (also loaded into the session), if any."""
    found = get_compliance_specification(kind, entity, tool_context)
    if "specification" not in found:
        return None
    return {
        "stored_on_dh": True,
        "analysis_run": False,
        "kind": kind,
        "entity": entity,
        "specification": found["specification"],
        "message": (
            f"A specification for {kind} '{entity}' is already stored on the DH platform and was loaded. "
            "No analysis was run. Present it and ask the user whether to re-run the analysis; "
            "call this tool again with rerun=True only if the user decides to."
        ),
    }


async def analyze_project_context(
    project: ProjectInput, tool_context: ToolContext, rerun: bool = False
) -> dict[str, Any]:
    """Build the structured compliance context of an AI project.

    Returns regulations, requirements, affected and vulnerable groups, protected attributes,
    foreseeable misuse, risk classification and human oversight, grounded in the OKF bundle.
    The result is stored and reused by later dataset and model analyses.

    The DH platform is checked first (identifier: the project name). When a specification is already
    stored there, it is returned without running the analysis; the user decides whether to re-run.

    Args:
        project: The project definition (name, domain, ai_task and goal are required).
        rerun: True only when the user asked to run the analysis again despite a stored specification.
    """
    project = _normalize_input(ProjectInput, project)
    if not rerun and (stored := _stored_on_dh("project", project.name, tool_context)):
        return stored
    response = await _run("project_context", project)
    if isinstance(response, dict):
        return response
    tool_context.state[PROJECT_KEY] = project.model_dump(mode="json")
    tool_context.state[CONTEXT_KEY] = response.data.model_dump(mode="json")
    return _payload(response)


async def analyze_dataset(
    dataset: DatasetInput, tool_context: ToolContext, project: Optional[ProjectInput] = None, rerun: bool = False
) -> dict[str, Any]:
    """Derive the structured compliance specification of an AI dataset.

    Returns the dataset scope, protected attributes and compliance objectives. The stored project
    context is attached automatically; do not pass it.

    The DH platform is checked first (identifier: the dataset name). When a specification is already
    stored there, it is returned without running the analysis; the user decides whether to re-run.

    Args:
        dataset: The dataset definition (name and scope are required).
        project: Optional project definition; defaults to the one analysed earlier in the session.
        rerun: True only when the user asked to run the analysis again despite a stored specification.
    """
    state = tool_context.state
    dataset = _normalize_input(DatasetInput, dataset)
    if not rerun and (stored := _stored_on_dh("dataset", dataset.name, tool_context)):
        return stored
    if project is not None:
        project = _normalize_input(ProjectInput, project)
    request = DatasetAnalysisRequest(
        dataset=dataset, project=project or _stored_project(state), project_context=_stored_context(state)
    )
    response = await _run("dataset", request)
    if isinstance(response, dict):
        return response
    state[DATASETS_KEY] = {**state.get(DATASETS_KEY, {}), dataset.name: response.data.model_dump(mode="json")}
    return _payload(response)


async def analyze_model(
    model: ModelInput, tool_context: ToolContext, project: Optional[ProjectInput] = None, rerun: bool = False
) -> dict[str, Any]:
    """Derive the structured compliance specification of an AI model.

    Returns compliance objectives with metrics and acceptance conditions. The stored project context
    and dataset analyses are attached automatically; do not pass them.

    The DH platform is checked first (identifier: the model name). When a specification is already
    stored there, it is returned without running the analysis; the user decides whether to re-run.

    Args:
        model: The model definition (name and ai_task are required).
        project: Optional project definition; defaults to the one analysed earlier in the session.
        rerun: True only when the user asked to run the analysis again despite a stored specification.
    """
    state = tool_context.state
    model = _normalize_input(ModelInput, model)
    if not rerun and (stored := _stored_on_dh("model", model.name, tool_context)):
        return stored
    if project is not None:
        project = _normalize_input(ProjectInput, project)
    datasets = [DataComplianceOut.model_validate(d) for d in state.get(DATASETS_KEY, {}).values()]
    request = ModelAnalysisRequest(
        model=model,
        project=project or _stored_project(state),
        project_context=_stored_context(state),
        dataset_compliance=datasets[:10],
    )
    response = await _run("model", request)
    if isinstance(response, dict):
        return response
    state[MODELS_KEY] = {**state.get(MODELS_KEY, {}), model.name: response.data.model_dump(mode="json")}
    return _payload(response)


def get_session_analyses(tool_context: ToolContext) -> dict[str, Any]:
    """Return the analyses already produced in this conversation (project context, datasets, models).

    Use it to answer follow-up questions without running the analyses again. It never reads the DH
    platform: specifications stored there are retrieved with the compliance-specifications skill.
    """
    state = tool_context.state
    return {
        "project": state.get(PROJECT_KEY),
        "project_context": state.get(CONTEXT_KEY),
        "datasets": state.get(DATASETS_KEY, {}),
        "models": state.get(MODELS_KEY, {}),
    }


COORDINATOR_TOOLS = (analyze_project_context, analyze_dataset, analyze_model, get_session_analyses)
