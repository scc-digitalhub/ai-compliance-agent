"""Access to the DH platform entities and their compliance extensions, through the DH Python SDK.

Extensions live in the `extensions` field of projects, dataitems and models as a list of
`{"kind", "name", "id", "spec"}` objects; the compliance specification is the `spec` of the extension.
At most one extension of a given kind exists on an entity. The platform replaces the whole list on
update, so saving resends every extension and keeps the `id` of the one being replaced.

Connection settings are read by the SDK from the DHCORE_* environment variables.
"""
from __future__ import annotations

import json
from typing import Any, Callable

import digitalhub as sdk
from digitalhub.utils.exceptions import EntityNotExistsError

from ..config import get_settings
from ..contracts.results import ComplianceContextOut, DataComplianceOut, ModelComplianceOut

STORE_KEY_PREFIX = "store://"

# entity kind used by the agents -> (SDK getter, SDK updater)
_ENTITY_API: dict[str, tuple[str, str]] = {
    "dataset": ("get_dataitem", "update_dataitem"),
    "model": ("get_model", "update_model"),
}


def _entity_api(entity_kind: str) -> tuple[Callable[..., Any], Callable[..., Any]]:
    if entity_kind not in _ENTITY_API:
        raise ValueError(f"Unsupported entity kind '{entity_kind}'; use one of {list(_ENTITY_API)}")
    getter, updater = _ENTITY_API[entity_kind]
    return getattr(sdk, getter), getattr(sdk, updater)


def _read_entity(entity: str, entity_kind: str) -> Any:
    """The SDK object of a dataitem or model, by store key or by name in the configured project."""
    getter, _ = _entity_api(entity_kind)
    if entity.startswith(STORE_KEY_PREFIX):
        return getter(entity)
    project = get_settings().dh_project
    if not project:
        raise ValueError(f"Set DH_PROJECT, or identify {entity_kind} '{entity}' by its store:// key")
    return getter(entity, project=project)


def _plain(obj: Any) -> dict:
    """A JSON-safe copy of an SDK entity dictionary."""
    return json.loads(json.dumps(obj.to_dict(), default=str))


def _find_extension(extensions: list[dict] | None, extension_kind: str) -> dict:
    found = next((e for e in extensions or [] if e.get("kind") == extension_kind), None)
    return dict(found.get("spec") or {}) if found else {}


def _with_extension(extensions: list[dict] | None, extension_kind: str, spec: dict) -> list[dict]:
    """The extensions list with the single extension of `extension_kind` replaced (or added)."""
    current = list(extensions or [])
    existing = next((e for e in current if e.get("kind") == extension_kind), None)
    replacement = {**(existing or {"kind": extension_kind, "name": extension_kind}), "spec": spec}
    others = [e for e in current if e.get("kind") != extension_kind]
    return [*others, replacement]


def get_entity(entity: str, entity_kind: str) -> dict:
    """Retrieve the details of a dataset (dataitem) or model; empty when it does not exist."""
    try:
        return _plain(_read_entity(entity, entity_kind))
    except EntityNotExistsError:
        return {}


def get_project_extension(project: str, extension_kind: str) -> dict:
    """Retrieve the spec of the project extension of the given kind; empty when there is none."""
    try:
        found = sdk.get_project(project)
    except EntityNotExistsError:
        return {}
    return _find_extension(getattr(found, "extensions", None), extension_kind)


def get_entity_extension(entity: str, entity_kind: str, extension_kind: str) -> dict:
    """Retrieve the spec of the dataset or model extension of the given kind; empty when there is none."""
    try:
        found = _read_entity(entity, entity_kind)
    except EntityNotExistsError:
        return {}
    return _find_extension(found.extensions, extension_kind)


def save_project_extension(project: str, extension_kind: str, extension: dict) -> None:
    """Create or replace the project extension of the given kind."""
    found = sdk.get_project(project)
    found.extensions = _with_extension(getattr(found, "extensions", None), extension_kind, extension)
    sdk.update_project(found)


def save_entity_extension(entity: str, entity_kind: str, extension_kind: str, extension: dict) -> None:
    """Create or replace the dataset or model extension of the given kind."""
    _, updater = _entity_api(entity_kind)
    found = _read_entity(entity, entity_kind)
    found.extensions = _with_extension(found.extensions, extension_kind, extension)
    updater(found)


def get_extension_schema(extension_kind: str) -> dict:
    """Retrieve the JSON schema for a given extension kind."""
    if extension_kind == "ai-compliance":
        return ComplianceContextOut.model_json_schema()
    if extension_kind == "data-compliance":
        return DataComplianceOut.model_json_schema()
    if extension_kind == "model-compliance":
        return ModelComplianceOut.model_json_schema()
    return {}
