"""DigitalHub SDK operations for entity details and compliance extensions."""
from __future__ import annotations

import json
from typing import Any, Callable

import digitalhub as sdk
from digitalhub.utils.exceptions import EntityNotExistsError

from compliance_core.contracts.results import (
    ComplianceContextOut,
    DataComplianceOut,
    ModelComplianceOut,
)

from .settings import get_dh_settings

STORE_KEY_PREFIX = "store://"
_UNSET = object()

_ENTITY_API: dict[str, tuple[str, str]] = {
    "dataset": ("get_dataitem", "update_dataitem"),
    "model": ("get_model", "update_model"),
}


def _client(client: Any | None) -> Any:
    return client if client is not None else sdk


def _entity_api(entity_kind: str, client: Any | None = None) -> tuple[Callable[..., Any], Callable[..., Any]]:
    if entity_kind not in _ENTITY_API:
        raise ValueError(f"Unsupported entity kind '{entity_kind}'; use one of {list(_ENTITY_API)}")
    getter, updater = _ENTITY_API[entity_kind]
    sdk_client = _client(client)
    return getattr(sdk_client, getter), getattr(sdk_client, updater)


def _read_entity(
    entity: str,
    entity_kind: str,
    client: Any | None = None,
    dh_project: str | None | object = _UNSET,
) -> Any:
    """Get a dataset or model by store key or name in the configured DH project."""
    getter, _ = _entity_api(entity_kind, client)
    if entity.startswith(STORE_KEY_PREFIX):
        return getter(entity)
    project = get_dh_settings().dh_project if dh_project is _UNSET else dh_project
    if not project:
        raise ValueError(
            f"Set DH_PROJECT, or identify {entity_kind} '{entity}' by its store:// key"
        )
    return getter(entity, project=project)


def _plain(obj: Any) -> dict[str, Any]:
    return json.loads(json.dumps(obj.to_dict(), default=str))


def _find_extension(extensions: list[dict[str, Any]] | None, extension_kind: str) -> dict[str, Any]:
    found = next((extension for extension in extensions or [] if extension.get("kind") == extension_kind), None)
    return dict(found.get("spec") or {}) if found else {}


def _with_extension(
    extensions: list[dict[str, Any]] | None, extension_kind: str, spec: dict[str, Any]
) -> list[dict[str, Any]]:
    """Replace or add one extension while preserving other extensions and its id."""
    current = list(extensions or [])
    existing = next((extension for extension in current if extension.get("kind") == extension_kind), None)
    replacement = {
        **(existing or {"kind": extension_kind, "name": extension_kind}),
        "spec": spec,
    }
    return [
        *[extension for extension in current if extension.get("kind") != extension_kind],
        replacement,
    ]


def get_entity(
    entity: str,
    entity_kind: str,
    *,
    client: Any | None = None,
    dh_project: str | None | object = _UNSET,
) -> dict[str, Any]:
    """Retrieve the details of a dataset (dataitem) or model; empty when it does not exist."""
    try:
        return _plain(_read_entity(entity, entity_kind, client, dh_project))
    except EntityNotExistsError:
        return {}


def get_project_extension(
    project: str, extension_kind: str, *, client: Any | None = None
) -> dict[str, Any]:
    """Retrieve a project extension spec; empty when the project or extension is absent."""
    try:
        found = _client(client).get_project(project)
    except EntityNotExistsError:
        return {}
    return _find_extension(getattr(found, "extensions", None), extension_kind)


def get_entity_extension(
    entity: str,
    entity_kind: str,
    extension_kind: str,
    *,
    client: Any | None = None,
    dh_project: str | None | object = _UNSET,
) -> dict[str, Any]:
    """Retrieve a dataset or model extension spec; empty when absent."""
    try:
        found = _read_entity(entity, entity_kind, client, dh_project)
    except EntityNotExistsError:
        return {}
    return _find_extension(getattr(found, "extensions", None), extension_kind)


def save_project_extension(
    project: str,
    extension_kind: str,
    extension: dict[str, Any],
    *,
    client: Any | None = None,
) -> None:
    """Create or replace a project extension while preserving all other extensions."""
    sdk_client = _client(client)
    found = sdk_client.get_project(project)
    found.extensions = _with_extension(
        getattr(found, "extensions", None), extension_kind, extension
    )
    sdk_client.update_project(found)


def save_entity_extension(
    entity: str,
    entity_kind: str,
    extension_kind: str,
    extension: dict[str, Any],
    *,
    client: Any | None = None,
    dh_project: str | None | object = _UNSET,
) -> None:
    """Create or replace a dataset or model extension while preserving its identity."""
    sdk_client = _client(client)
    _, updater = _entity_api(entity_kind, sdk_client)
    found = _read_entity(entity, entity_kind, sdk_client, dh_project)
    found.extensions = _with_extension(
        getattr(found, "extensions", None), extension_kind, extension
    )
    updater(found)


def get_extension_schema(extension_kind: str) -> dict[str, Any]:
    """Return the JSON schema for a supported compliance extension."""
    schemas = {
        "ai-compliance": ComplianceContextOut,
        "data-compliance": DataComplianceOut,
        "model-compliance": ModelComplianceOut,
    }
    model = schemas.get(extension_kind)
    return model.model_json_schema() if model else {}


__all__ = [
    "STORE_KEY_PREFIX",
    "get_entity",
    "get_entity_extension",
    "get_extension_schema",
    "get_project_extension",
    "save_entity_extension",
    "save_project_extension",
]
