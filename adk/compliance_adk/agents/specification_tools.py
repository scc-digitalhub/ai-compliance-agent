"""Tools of the compliance-specifications skill: store and retrieve specifications on the DH platform.

The session holds the specifications produced by the analyses; these tools persist them through
`dh.tools` and load stored ones back into the session so later analyses reuse them. The project
specification combines the project description and its compliance context (okb ProjectComplianceSpec).
"""
from __future__ import annotations

from typing import Any, Callable, Literal, Optional

from google.adk.tools import ToolContext
from pydantic import BaseModel, ValidationError

from ..contracts.requests import ProjectComplianceSpec, ProjectInput
from ..contracts.results import ComplianceContextOut, DataComplianceOut, ModelComplianceOut
from ..dh import tools as dh
from .session_state import CONTEXT_KEY, DATASETS_KEY, MODELS_KEY, PROJECT_KEY

SpecificationKind = Literal["project", "dataset", "model"]

# kind -> (DH extension kind, specification model)
_SPECIFICATIONS: dict[str, tuple[str, type[BaseModel]]] = {
    "project": ("ai-compliance", ProjectComplianceSpec),
    "dataset": ("data-compliance", DataComplianceOut),
    "model": ("model-compliance", ModelComplianceOut),
}


def _error(message: str, code: str) -> dict[str, str]:
    return {"error": message, "code": code}


def _problems(exc: ValidationError) -> str:
    return "; ".join(f"{'.'.join(map(str, e['loc']))}: {e['msg']}" for e in exc.errors()[:5])


def _validate(model_type: type[BaseModel], value: Any, extra: Optional[str] = None) -> BaseModel:
    # Providers may deliver an object argument as JSON text.
    if isinstance(value, str):
        return model_type.model_validate_json(value, extra=extra)
    return model_type.model_validate(value, extra=extra)


def _session_specification(state: Any, kind: str, entity: str) -> Optional[dict[str, Any]]:
    if kind == "project":
        project, context = state.get(PROJECT_KEY), state.get(CONTEXT_KEY)
        if not project or not context:
            return None
        spec = ProjectComplianceSpec.of(ProjectInput.model_validate(project), ComplianceContextOut.model_validate(context))
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
    kind: SpecificationKind, entity: str, tool_context: ToolContext
) -> dict[str, Any]:
    """Retrieve a stored compliance specification from the DH platform.

    The specification is also loaded into this conversation, so later analyses reuse it.

    Args:
        kind: 'project' (project description and compliance context), 'dataset' (data compliance) or 'model'.
        entity: Identifier of the project, dataset or model on the DH platform.
    """
    if kind not in _SPECIFICATIONS:
        return _error(f"Unknown kind '{kind}'; use one of {list(_SPECIFICATIONS)}", "invalid_kind")
    extension_kind, model_type = _SPECIFICATIONS[kind]
    try:
        raw = (
            dh.get_project_extension(entity, extension_kind)
            if kind == "project"
            else dh.get_entity_extension(entity, kind, extension_kind)
        )
    except Exception as exc:  # the platform client may fail in many ways; report, don't raise
        return _error(f"Could not read the {kind} '{entity}' from the DH platform: {exc}", "dh_error")
    if not raw:
        return _error(f"No compliance specification is stored for {kind} '{entity}'", "not_found")
    try:
        # Fields managed on the platform only (e.g. compliance_status, documentation) are ignored.
        specification = _validate(model_type, raw, extra="ignore")
    except ValidationError as exc:
        return _error(
            f"The stored specification is not a valid {model_type.__name__}: {_problems(exc)}",
            "invalid_specification",
        )
    _remember(tool_context.state, kind, entity, specification)
    return {"kind": kind, "entity": entity, "specification": specification.model_dump(mode="json")}


def save_compliance_specification(
    kind: SpecificationKind,
    entity: str,
    tool_context: ToolContext,
    specification: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    """Store a compliance specification on the DH platform, replacing the stored one.

    Without `specification`, the one analysed earlier in this conversation is stored. Fields managed on
    the platform only (e.g. compliance_status, documentation) are kept.

    Args:
        kind: 'project' (project description and compliance context), 'dataset' (data compliance) or 'model'.
        entity: Identifier of the project, dataset or model on the DH platform. For datasets and
            models analysed in this conversation, it is the name used in the analysis.
        specification: Optional specification to store instead of the analysed one, as provided by the user.
    """
    if kind not in _SPECIFICATIONS:
        return _error(f"Unknown kind '{kind}'; use one of {list(_SPECIFICATIONS)}", "invalid_kind")
    extension_kind, model_type = _SPECIFICATIONS[kind]
    source = "argument" if specification else "session"
    raw = specification or _session_specification(tool_context.state, kind, entity)
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
    # DH validates the spec against its JSON schema, which does not accept nulls.
    data = validated.model_dump(mode="json", exclude_none=True)
    try:
        if kind == "project":
            stored = dh.get_project_extension(entity, extension_kind)
            dh.save_project_extension(entity, extension_kind, {**stored, **data})
        else:
            stored = dh.get_entity_extension(entity, kind, extension_kind)
            dh.save_entity_extension(entity, kind, extension_kind, {**stored, **data})
    except Exception as exc:  # e.g. the entity does not exist or the platform is unreachable
        return _error(f"Could not save the {kind} '{entity}' specification on the DH platform: {exc}", "dh_error")
    if source == "argument":
        _remember(tool_context.state, kind, entity, validated)
    return {"kind": kind, "entity": entity, "extension_kind": extension_kind, "saved": True, "source": source}


SPECIFICATION_TOOL_REGISTRY: dict[str, Callable[..., Any]] = {
    fn.__name__: fn for fn in (get_compliance_specification, save_compliance_specification)
}
