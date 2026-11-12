# SPDX-FileCopyrightText: © 2026 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

"""Framework-neutral tools for retrieving and saving compliance specifications."""
from __future__ import annotations

import hashlib
import json
from urllib.parse import urlparse
from typing import Any, Callable, Optional

from pydantic import BaseModel, ValidationError

from .contracts.requests import ProjectComplianceSpec, ProjectInput
from .contracts.results import ComplianceContextOut, DataComplianceOut, ModelComplianceOut
from .ports import SpecificationKind
from .provenance import (
    PROVENANCE_FIELD, build_provenance, get_provenance, set_provenance, split_provenance,
)
from .state import (
    CONTEXT_KEY, DATASETS_KEY, MODELS_KEY, PROJECT_KEY, REVISIONS_KEY, StateStore,
    activate_project, active_project, entity_project, scoped_get, scoped_update, transaction,
)
from .tools import ToolEnv, ToolSpec

SPECIFICATIONS: dict[str, tuple[str, type[BaseModel]]] = {
    "project": ("ai-compliance", ProjectComplianceSpec),
    "dataset": ("data-compliance", DataComplianceOut),
    "model": ("model-compliance", ModelComplianceOut),
}
_SPECIFICATIONS = SPECIFICATIONS


class SpecificationError(ValueError):
    def __init__(self, message: str, code: str):
        super().__init__(message)
        self.code = code


def _error(message: str, code: str) -> dict[str, str]:
    return {"error": message, "code": code}


def _problems(exc: ValidationError) -> str:
    return "; ".join(f"{'.'.join(map(str, error['loc']))}: {error['msg']}" for error in exc.errors()[:5])


def _validate(model_type: type[BaseModel], value: Any, extra: Optional[str] = None) -> BaseModel:
    if isinstance(value, str):
        return model_type.model_validate_json(value, extra=extra)
    return model_type.model_validate(value, extra=extra)


def _scope(state: StateStore, kind: str, entity: str, project: str | None) -> str | None:
    """Workspace project that owns a specification.

    A project specification belongs to the project it names. Only analyses recorded before any
    project was selected are unscoped and may be saved under the given DigitalHub identifier.
    """
    if kind != "project":
        return project
    return None if active_project(state) is None else entity


def _resolve_project(state: StateStore, kind: str, entity: str, project: str | None) -> str | None:
    """DigitalHub project of a dataset/model: the store:// key's project, the argument or the active one."""
    if kind != "project" and entity.startswith("store://"):
        return urlparse(entity).netloc or entity_project(state, project)
    return entity_project(state, project)


def session_specification(
    state: StateStore, kind: str, entity: str, project: str | None = None,
) -> Optional[dict[str, Any]]:
    """Return a specification analysed or retrieved in the workspace, scoped by project."""
    scope = _scope(state, kind, entity, project)
    if kind == "project":
        project_input, context = scoped_get(state, PROJECT_KEY, scope), scoped_get(state, CONTEXT_KEY, scope)
        if not project_input or not context:
            return None
        spec = ProjectComplianceSpec.of(
            ProjectInput.model_validate(project_input),
            ComplianceContextOut.model_validate(context),
        )
        return spec.model_dump(mode="json")
    return scoped_get(state, DATASETS_KEY if kind == "dataset" else MODELS_KEY, scope).get(entity)


_session_specification = session_specification


def _remember(
    state: StateStore, kind: str, entity: str, specification: BaseModel, project: str | None,
    provenance: Optional[dict[str, Any]],
) -> None:
    with transaction(state):
        if isinstance(specification, ProjectComplianceSpec):
            activate_project(state, entity)
            state[PROJECT_KEY] = specification.project(entity).model_dump(mode="json")
            if specification.context is not None:
                state[CONTEXT_KEY] = specification.context.model_dump(mode="json")
        else:
            key = DATASETS_KEY if kind == "dataset" else MODELS_KEY
            scoped_update(state, key, entity, specification.model_dump(mode="json"), project)
        set_provenance(state, kind, entity, provenance, _scope(state, kind, entity, project))


def specification_revision(stored: dict[str, Any] | None) -> str | None:
    """Content fingerprint of a stored specification; None when nothing is stored."""
    if not stored:
        return None
    encoded = json.dumps(stored, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(encoded.encode()).hexdigest()[:16]


def _revision_key(kind: str, entity: str, project: str | None) -> str:
    return f"{kind}:{'' if kind == 'project' else project or ''}:{entity}"


def _set_revision(state: StateStore, key: str, revision: str | None) -> None:
    revisions = dict(state.get(REVISIONS_KEY) or {})
    if revision is None:
        revisions.pop(key, None)
    else:
        revisions[key] = revision
    state[REVISIONS_KEY] = revisions


def prepare_specification(
    state: StateStore, kind: str, entity: str, specification: Any = None, project: str | None = None,
) -> dict[str, Any]:
    """Validate and normalize the specification a save would write, without writing it.

    Raises SpecificationError with code invalid_kind, missing_project, not_found or
    invalid_specification. Returns the normalized specification, its provenance and its source.
    """
    if kind not in SPECIFICATIONS:
        raise SpecificationError(f"Unknown kind '{kind}'; use one of {list(SPECIFICATIONS)}", "invalid_kind")
    project = _resolve_project(state, kind, entity, project)
    if kind != "project" and not project and not entity.startswith("store://"):
        raise SpecificationError(
            "Specify the DigitalHub project for this specification, or provide its store:// key", "missing_project",
        )
    _, model_type = SPECIFICATIONS[kind]
    source = "argument" if specification else "session"
    raw = specification or session_specification(state, kind, entity, project)
    if not raw:
        active = active_project(state)
        hint = (
            f" The workspace's analysed project is '{active}'; save it under that identifier."
            if kind == "project" and active and active != entity.strip() else ""
        )
        raise SpecificationError(
            f"No analysed {kind} specification for '{entity}' in this conversation; run the analysis "
            f"or provide the specification.{hint}",
            "not_found",
        )
    if isinstance(raw, dict):
        raw, _ = split_provenance(raw)
    try:
        validated = _validate(model_type, raw)
    except ValidationError as exc:
        raise SpecificationError(f"Invalid {model_type.__name__}: {_problems(exc)}", "invalid_specification") from exc
    if source == "argument":
        provenance = build_provenance("supplied", None)
    else:
        provenance = get_provenance(state, kind, entity, _scope(state, kind, entity, project)) or build_provenance(
            "unknown", None,
        )
    return {
        "kind": kind,
        "entity": entity,
        "project": project,
        "specification": validated.model_dump(mode="json", exclude_none=True),
        "provenance": provenance,
        "source": source,
        "validated": validated,
    }



def get_compliance_specification(
    env: ToolEnv, kind: SpecificationKind, entity: str, project: str | None = None,
) -> dict[str, Any]:
    """Retrieve a stored compliance specification and load it into the workspace.

    The specification is loaded into the scope of its project; its provenance (how and from which
    knowledge it was produced) is returned when stored.

    Args:
        kind: 'project', 'dataset', or 'model'.
        entity: Identifier of the project, dataset, or model.
        project: DigitalHub project explicitly named by the user for a dataset or model.
            Defaults to the workspace project; a store:// key already identifies its project.
    """
    if kind not in SPECIFICATIONS:
        return _error(f"Unknown kind '{kind}'; use one of {list(SPECIFICATIONS)}", "invalid_kind")
    if env.specifications is None:
        return _error("The specification repository is not configured", "integration_unavailable")

    project = _resolve_project(env.state, kind, entity, project)
    if kind != "project" and not project and not entity.startswith("store://"):
        return _error("Specify the DigitalHub project for this specification, or provide its store:// key", "missing_project")
    _, model_type = SPECIFICATIONS[kind]
    try:
        raw = env.specifications.get(kind, entity, project=project)
    except Exception as exc:
        return _error(f"Could not read the {kind} '{entity}' from the repository: {exc}", "dh_error")
    if not raw:
        return _error(f"No compliance specification is stored for {kind} '{entity}'", "not_found")
    body, provenance = split_provenance(raw)
    try:
        specification = _validate(model_type, body, extra="ignore")
    except ValidationError as exc:
        return _error(
            f"The stored specification is not a valid {model_type.__name__}: {_problems(exc)}",
            "invalid_specification",
        )
    revision = specification_revision(raw)
    with transaction(env.state):
        _remember(env.state, kind, entity, specification, project, provenance)
        _set_revision(env.state, _revision_key(kind, entity, project), revision)
    result = {
        "kind": kind, "entity": entity, "specification": specification.model_dump(mode="json"),
        "revision": revision,
    }
    if provenance:
        result["provenance"] = provenance
    return result


def save_compliance_specification(
    env: ToolEnv,
    kind: SpecificationKind,
    entity: str,
    specification: Optional[dict[str, Any]] = None,
    project: str | None = None,
    overwrite: bool = False,
) -> dict[str, Any]:
    """Store a compliance specification, preserving repository-managed fields.

    Without `specification`, the result is loaded from the workspace. Its provenance is stored with
    it. The save is refused with code 'conflict' when the stored specification changed since it was
    last retrieved in this workspace, or exists but was never retrieved here.

    Args:
        kind: 'project', 'dataset', or 'model'.
        entity: Identifier of the project, dataset, or model.
        specification: Optional specification supplied by the user.
        project: DigitalHub project explicitly named by the user for a dataset or model.
            Defaults to the workspace project; a store:// key already identifies its project.
        overwrite: True only when the user confirmed replacing a conflicting stored specification.
    """
    if kind not in SPECIFICATIONS:
        return _error(f"Unknown kind '{kind}'; use one of {list(SPECIFICATIONS)}", "invalid_kind")
    if env.specifications is None:
        return _error("The specification repository is not configured", "integration_unavailable")
    try:
        prepared = prepare_specification(env.state, kind, entity, specification, project)
    except SpecificationError as exc:
        return _error(str(exc), exc.code)
    project = prepared["project"]
    extension_kind, _ = SPECIFICATIONS[kind]
    revision_key = _revision_key(kind, entity, project)
    try:
        current = specification_revision(env.specifications.get(kind, entity, project=project))
    except Exception as exc:
        return _error(f"Could not read the {kind} '{entity}' from the repository: {exc}", "dh_error")
    seen = (env.state.get(REVISIONS_KEY) or {}).get(revision_key)
    if current is not None and current != seen and not overwrite:
        reason = "changed since it was retrieved" if seen else "exists but was not retrieved in this workspace"
        return {
            **_error(
                f"The stored {kind} '{entity}' specification {reason}. Retrieve and review it, or save "
                "with overwrite=True only if the user confirms replacing it.",
                "conflict",
            ),
            "current_revision": current,
            "seen_revision": seen,
        }
    data = {**prepared["specification"], PROVENANCE_FIELD: prepared["provenance"]}
    try:
        env.specifications.save(kind, entity, data, project=project)
    except Exception as exc:
        return _error(f"Could not save the {kind} '{entity}' specification: {exc}", "dh_error")
    try:
        revision = specification_revision(env.specifications.get(kind, entity, project=project))
    except Exception:
        revision = None
    with transaction(env.state):
        if prepared["source"] == "argument":
            _remember(env.state, kind, entity, prepared["validated"], project, prepared["provenance"])
        _set_revision(env.state, revision_key, revision)
    return {
        "kind": kind,
        "entity": entity,
        "extension_kind": extension_kind,
        "saved": True,
        "source": prepared["source"],
        "revision": revision,
        "provenance": prepared["provenance"],
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
    "SPECIFICATIONS",
    "SPECIFICATION_TOOL_REGISTRY",
    "SPECIFICATION_TOOL_SPECS",
    "SpecificationError",
    "get_compliance_specification",
    "prepare_specification",
    "save_compliance_specification",
    "session_specification",
    "specification_revision",
]
