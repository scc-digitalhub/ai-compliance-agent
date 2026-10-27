"""Framework-neutral tools for retrieving and saving compliance specifications."""
from __future__ import annotations

from typing import Any, Callable, Optional

from pydantic import BaseModel, ValidationError

from .contracts.requests import ProjectComplianceSpec, ProjectInput
from .contracts.results import ComplianceContextOut, DataComplianceOut, ModelComplianceOut
from .ports import SpecificationKind
from .state import CONTEXT_KEY, DATASETS_KEY, MODELS_KEY, PROJECT_KEY
from .tools import ToolEnv, ToolSpec

_SPECIFICATIONS: dict[str, tuple[str, type[BaseModel]]] = {
    "project": ("ai-compliance", ProjectComplianceSpec),
    "dataset": ("data-compliance", DataComplianceOut),
    "model": ("model-compliance", ModelComplianceOut),
}


def _error(message: str, code: str) -> dict[str, str]:
    return {"error": message, "code": code}


def _problems(exc: ValidationError) -> str:
    return "; ".join(f"{'.'.join(map(str, error['loc']))}: {error['msg']}" for error in exc.errors()[:5])


def _validate(model_type: type[BaseModel], value: Any, extra: Optional[str] = None) -> BaseModel:
    if isinstance(value, str):
        return model_type.model_validate_json(value, extra=extra)
    return model_type.model_validate(value, extra=extra)


def _session_specification(state: Any, kind: str, entity: str) -> Optional[dict[str, Any]]:
    if kind == "project":
        project, context = state.get(PROJECT_KEY), state.get(CONTEXT_KEY)
        if not project or not context:
            return None
        spec = ProjectComplianceSpec.of(
            ProjectInput.model_validate(project),
            ComplianceContextOut.model_validate(context),
        )
        return spec.model_dump(mode="json")
    return state.get(DATASETS_KEY if kind == "dataset" else MODELS_KEY, {}).get(entity)


def _remember(state: Any, kind: str, entity: str, specification: BaseModel) -> None:
    data = specification.model_dump(mode="json")
    if isinstance(specification, ProjectComplianceSpec):
        state[PROJECT_KEY] = specification.project(entity).model_dump(mode="json")
        if specification.context is not None:
            state[CONTEXT_KEY] = specification.context.model_dump(mode="json")
    else:
        key = DATASETS_KEY if kind == "dataset" else MODELS_KEY
        state[key] = {**state.get(key, {}), entity: data}


def get_compliance_specification(
    env: ToolEnv, kind: SpecificationKind, entity: str
) -> dict[str, Any]:
    """Retrieve a stored compliance specification and load it into the workspace.

    Args:
        kind: 'project', 'dataset', or 'model'.
        entity: Identifier of the project, dataset, or model.
    """
    if kind not in _SPECIFICATIONS:
        return _error(f"Unknown kind '{kind}'; use one of {list(_SPECIFICATIONS)}", "invalid_kind")
    if env.specifications is None:
        return _error("The specification repository is not configured", "integration_unavailable")

    _, model_type = _SPECIFICATIONS[kind]
    try:
        raw = env.specifications.get(kind, entity)
    except Exception as exc:
        return _error(f"Could not read the {kind} '{entity}' from the repository: {exc}", "dh_error")
    if not raw:
        return _error(f"No compliance specification is stored for {kind} '{entity}'", "not_found")
    try:
        specification = _validate(model_type, raw, extra="ignore")
    except ValidationError as exc:
        return _error(
            f"The stored specification is not a valid {model_type.__name__}: {_problems(exc)}",
            "invalid_specification",
        )
    _remember(env.state, kind, entity, specification)
    return {"kind": kind, "entity": entity, "specification": specification.model_dump(mode="json")}


def save_compliance_specification(
    env: ToolEnv,
    kind: SpecificationKind,
    entity: str,
    specification: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    """Store a compliance specification, preserving repository-managed fields.

    Without `specification`, the result is loaded from the workspace.

    Args:
        kind: 'project', 'dataset', or 'model'.
        entity: Identifier of the project, dataset, or model.
        specification: Optional specification supplied by the user.
    """
    if kind not in _SPECIFICATIONS:
        return _error(f"Unknown kind '{kind}'; use one of {list(_SPECIFICATIONS)}", "invalid_kind")
    if env.specifications is None:
        return _error("The specification repository is not configured", "integration_unavailable")

    extension_kind, model_type = _SPECIFICATIONS[kind]
    source = "argument" if specification else "session"
    raw = specification or _session_specification(env.state, kind, entity)
    if not raw:
        return _error(
            f"No analysed {kind} specification for '{entity}' in this conversation; run the analysis "
            "or provide the specification",
            "not_found",
        )
    try:
        validated = _validate(model_type, raw)
    except ValidationError as exc:
        return _error(f"Invalid {model_type.__name__}: {_problems(exc)}", "invalid_specification")
    data = validated.model_dump(mode="json", exclude_none=True)
    try:
        env.specifications.save(kind, entity, data)
    except Exception as exc:
        return _error(f"Could not save the {kind} '{entity}' specification: {exc}", "dh_error")
    if source == "argument":
        _remember(env.state, kind, entity, validated)
    return {
        "kind": kind,
        "entity": entity,
        "extension_kind": extension_kind,
        "saved": True,
        "source": source,
    }


GET_TOOL_SPEC = ToolSpec(
    name="get_compliance_specification",
    fn=get_compliance_specification,
    group="dh",
    description=get_compliance_specification.__doc__ or "",
    read_only=False,
)
SAVE_TOOL_SPEC = ToolSpec(
    name="save_compliance_specification",
    fn=save_compliance_specification,
    group="dh",
    description=save_compliance_specification.__doc__ or "",
    read_only=False,
    destructive=True,
)
SPECIFICATION_TOOL_SPECS = (GET_TOOL_SPEC, SAVE_TOOL_SPEC)
SPECIFICATION_TOOL_REGISTRY: dict[str, Callable[..., Any]] = {
    spec.name: spec.fn for spec in SPECIFICATION_TOOL_SPECS
}

__all__ = [
    "GET_TOOL_SPEC",
    "SAVE_TOOL_SPEC",
    "SPECIFICATION_TOOL_REGISTRY",
    "SPECIFICATION_TOOL_SPECS",
    "get_compliance_specification",
    "save_compliance_specification",
]
