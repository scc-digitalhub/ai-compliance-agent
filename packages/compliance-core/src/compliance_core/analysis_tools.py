"""Framework-neutral coordinator tools for structured compliance analyses."""
from __future__ import annotations

from typing import Any, Optional, TypeVar

from pydantic import BaseModel

from .contracts import (
    AnalysisResponse,
    ComplianceContextOut,
    DataComplianceOut,
    DatasetAnalysisRequest,
    DatasetInput,
    ModelAnalysisRequest,
    ModelInput,
    ProjectInput,
)
from .errors import ComplianceError
from .ports import SpecificationKind
from .specification_tools import (
    get_compliance_specification as _get_compliance_specification,
)
from .state import CONTEXT_KEY, DATASETS_KEY, ENTITIES_KEY, MODELS_KEY, PROJECT_KEY
from .tools import ToolEnv, ToolSpec

InputModel = TypeVar("InputModel", bound=BaseModel)


def _normalize_input(model_type: type[InputModel], value: Any) -> InputModel:
    if isinstance(value, str):
        return model_type.model_validate_json(value)
    return model_type.model_validate(value)


async def _run(
    env: ToolEnv, agent_key: str, request: BaseModel
) -> AnalysisResponse[Any] | dict[str, str]:
    if env.analysis_engine is None:
        return {
            "error": "The structured analysis engine is not configured",
            "code": "integration_unavailable",
        }
    try:
        return await env.analysis_engine.run(agent_key, request)
    except ComplianceError as exc:
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


def _stored_on_dh(
    env: ToolEnv, kind: SpecificationKind, entity: str, project: str | None = None,
) -> Optional[dict[str, Any]]:
    found = _get_compliance_specification(env, kind, entity, project=project)
    if "specification" not in found:
        if found.get("code") == "not_found":
            return None
        return found
    if kind == "project" and not found["specification"].get("context"):
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
    env: ToolEnv, project: ProjectInput, rerun: bool = False
) -> dict[str, Any]:
    """Build the structured compliance context of an AI project definition.

    The DH platform is checked first. When a complete specification is already stored, return it
    without running the analysis; the user decides whether to re-run.

    Args:
        project: Project definition (name, domain, ai_task and goal are required).
        rerun: True only when the user asked to run analysis again despite a stored specification.
    """
    project = _normalize_input(ProjectInput, project)
    if not rerun and (stored := _stored_on_dh(env, "project", project.name)):
        return stored
    response = await _run(env, "project_context", project)
    if isinstance(response, dict):
        return response
    env.state[PROJECT_KEY] = project.model_dump(mode="json")
    env.state[CONTEXT_KEY] = response.data.model_dump(mode="json")
    return _payload(response)


async def analyze_dataset(
    env: ToolEnv,
    dataset: DatasetInput,
    project: Optional[ProjectInput] = None,
    rerun: bool = False,
) -> dict[str, Any]:
    """Derive the structured compliance specification of an AI dataset.

    The stored project context is attached automatically. A stored DH specification is returned
    without analysis until the user requests a re-run.

    Args:
        dataset: Dataset definition (name and scope are required).
        project: Optional project definition; defaults to the one already analyzed.
        rerun: True only when the user asked to run analysis again despite a stored specification.
    """
    dataset = _normalize_input(DatasetInput, dataset)
    if project is not None:
        project = _normalize_input(ProjectInput, project)
    if not rerun and (stored := _stored_on_dh(
        env, "dataset", dataset.name, project=project.name if project else None
    )):
        return stored
    request = DatasetAnalysisRequest(
        dataset=dataset,
        project=project or _stored_project(env.state),
        project_context=_stored_context(env.state),
    )
    response = await _run(env, "dataset", request)
    if isinstance(response, dict):
        return response
    env.state[DATASETS_KEY] = {
        **env.state.get(DATASETS_KEY, {}),
        dataset.name: response.data.model_dump(mode="json"),
    }
    return _payload(response)


async def analyze_model(
    env: ToolEnv,
    model: ModelInput,
    project: Optional[ProjectInput] = None,
    rerun: bool = False,
) -> dict[str, Any]:
    """Derive the structured compliance specification of an AI model.

    The stored project and dataset analyses are attached automatically. A stored DH specification
    is returned without analysis until the user requests a re-run.

    Args:
        model: Model definition (name and ai_task are required).
        project: Optional project definition; defaults to the one already analyzed.
        rerun: True only when the user asked to run analysis again despite a stored specification.
    """
    model = _normalize_input(ModelInput, model)
    if project is not None:
        project = _normalize_input(ProjectInput, project)
    if not rerun and (stored := _stored_on_dh(
        env, "model", model.name, project=project.name if project else None
    )):
        return stored
    datasets = [
        DataComplianceOut.model_validate(value)
        for value in env.state.get(DATASETS_KEY, {}).values()
    ]
    request = ModelAnalysisRequest(
        model=model,
        project=project or _stored_project(env.state),
        project_context=_stored_context(env.state),
        dataset_compliance=datasets[:10],
    )
    response = await _run(env, "model", request)
    if isinstance(response, dict):
        return response
    env.state[MODELS_KEY] = {
        **env.state.get(MODELS_KEY, {}),
        model.name: response.data.model_dump(mode="json"),
    }
    return _payload(response)


def get_session_analyses(env: ToolEnv) -> dict[str, Any]:
    """Return analyses and DH entity details already loaded into the current workspace."""
    state = env.state
    return {
        "project": state.get(PROJECT_KEY),
        "project_context": state.get(CONTEXT_KEY),
        "datasets": state.get(DATASETS_KEY, {}),
        "models": state.get(MODELS_KEY, {}),
        "entities": state.get(ENTITIES_KEY, {}),
    }


ANALYSIS_TOOL_SPECS = (
    ToolSpec(
        name="analyze_project_context",
        fn=analyze_project_context,
        group="analysis",
        description=analyze_project_context.__doc__ or "",
        read_only=False,
        needs_llm=True,
    ),
    ToolSpec(
        name="analyze_dataset",
        fn=analyze_dataset,
        group="analysis",
        description=analyze_dataset.__doc__ or "",
        read_only=False,
        needs_llm=True,
    ),
    ToolSpec(
        name="analyze_model",
        fn=analyze_model,
        group="analysis",
        description=analyze_model.__doc__ or "",
        read_only=False,
        needs_llm=True,
    ),
    ToolSpec(
        name="get_session_analyses",
        fn=get_session_analyses,
        group="session",
        description=get_session_analyses.__doc__ or "",
        read_only=True,
    ),
)

__all__ = [
    "ANALYSIS_TOOL_SPECS",
    "analyze_dataset",
    "analyze_model",
    "analyze_project_context",
    "get_session_analyses",
]
