"""Tools that let the coordinator run the same structured agents as the API.

Results are kept in session state so follow-up questions reuse them and later analyses receive the
earlier ones (project context into dataset and model analysis) without the LLM re-sending them.
"""
from __future__ import annotations

from typing import Any, Optional

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

PROJECT_KEY = "analysis_project"
CONTEXT_KEY = "analysis_project_context"
DATASETS_KEY = "analysis_datasets"
MODELS_KEY = "analysis_models"


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


async def analyze_project_context(project: ProjectInput, tool_context: ToolContext) -> dict[str, Any]:
    """Build the structured compliance context of an AI project.

    Returns regulations, requirements, affected and vulnerable groups, protected attributes,
    foreseeable misuse, risk classification and human oversight, grounded in the OKF bundle.
    The result is stored and reused by later dataset and model analyses.

    Args:
        project: The project definition (name, domain, ai_task and goal are required).
    """
    response = await _run("project_context", project)
    if isinstance(response, dict):
        return response
    tool_context.state[PROJECT_KEY] = project.model_dump(mode="json")
    tool_context.state[CONTEXT_KEY] = response.data.model_dump(mode="json")
    return _payload(response)


async def analyze_dataset(
    dataset: DatasetInput, tool_context: ToolContext, project: Optional[ProjectInput] = None
) -> dict[str, Any]:
    """Derive the structured compliance specification of an AI dataset.

    Returns the dataset scope, protected attributes and compliance objectives. The stored project
    context is attached automatically; do not pass it.

    Args:
        dataset: The dataset definition (name and scope are required).
        project: Optional project definition; defaults to the one analysed earlier in the session.
    """
    state = tool_context.state
    request = DatasetAnalysisRequest(
        dataset=dataset, project=project or _stored_project(state), project_context=_stored_context(state)
    )
    response = await _run("dataset", request)
    if isinstance(response, dict):
        return response
    state[DATASETS_KEY] = {**state.get(DATASETS_KEY, {}), dataset.name: response.data.model_dump(mode="json")}
    return _payload(response)


async def analyze_model(
    model: ModelInput, tool_context: ToolContext, project: Optional[ProjectInput] = None
) -> dict[str, Any]:
    """Derive the structured compliance specification of an AI model.

    Returns compliance objectives with metrics and acceptance conditions. The stored project context
    and dataset analyses are attached automatically; do not pass them.

    Args:
        model: The model definition (name and ai_task are required).
        project: Optional project definition; defaults to the one analysed earlier in the session.
    """
    state = tool_context.state
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

    Use it to answer follow-up questions without running the analyses again.
    """
    state = tool_context.state
    return {
        "project": state.get(PROJECT_KEY),
        "project_context": state.get(CONTEXT_KEY),
        "datasets": state.get(DATASETS_KEY, {}),
        "models": state.get(MODELS_KEY, {}),
    }


COORDINATOR_TOOLS = (analyze_project_context, analyze_dataset, analyze_model, get_session_analyses)
