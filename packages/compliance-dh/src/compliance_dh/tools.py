"""DigitalHub SDK operations for entity details and compliance extensions."""
from __future__ import annotations

import json
from urllib.parse import urlparse
from typing import Any, Callable

import digitalhub as sdk
from digitalhub.utils.exceptions import EntityNotExistsError

from compliance_core.contracts.results import (
    ComplianceContextOut,
    DataComplianceOut,
    ModelComplianceOut,
)

STORE_KEY_PREFIX = "store://"

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
    project: str | None = None,
) -> Any:
    """Get a dataset or model by store key or name in an explicitly identified project."""
    getter, _ = _entity_api(entity_kind, client)
    if entity.startswith(STORE_KEY_PREFIX):
        return getter(entity)
    if not project or not project.strip():
        raise ValueError(
            f"Specify the DigitalHub project for {entity_kind} '{entity}', or provide its store:// key"
        )
    return getter(entity, project=project.strip())


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
    project: str | None = None,
) -> dict[str, Any]:
    """Retrieve the details of a dataset (dataitem) or model; empty when it does not exist."""
    try:
        return _plain(_read_entity(entity, entity_kind, client, project))
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
    project: str | None = None,
) -> dict[str, Any]:
    """Retrieve a dataset or model extension spec; empty when absent."""
    try:
        found = _read_entity(entity, entity_kind, client, project)
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
    project: str | None = None,
) -> None:
    """Create or replace a dataset or model extension while preserving its identity."""
    sdk_client = _client(client)
    _, updater = _entity_api(entity_kind, sdk_client)
    found = _read_entity(entity, entity_kind, sdk_client, project)
    found.extensions = _with_extension(
        getattr(found, "extensions", None), extension_kind, extension
    )
    updater(found)


def get_extension_schema(extension_kind: str) -> dict[str, Any]:
    """Return the JSON schema for a supported compliance extension."""
    from compliance_core.contracts.reports import ReportSpec

    schemas = {
        "ai-compliance": ComplianceContextOut,
        "data-compliance": DataComplianceOut,
        "model-compliance": ModelComplianceOut,
        "compliance-report": ReportSpec,
    }
    model = schemas.get(extension_kind)
    return model.model_json_schema() if model else {}


def _report_target(entity: str, project: str | None) -> None:
    if entity.startswith(STORE_KEY_PREFIX) and project and urlparse(entity).netloc != project:
        raise ValueError("The project argument conflicts with the store:// key")


def get_report_extension(
    entity: str, entity_kind: str, name: str, *, client: Any | None = None,
    project: str | None = None,
) -> dict[str, Any]:
    """Read one named compliance-report extension without mixing report identities."""
    _report_target(entity, project)
    if not name.strip():
        raise ValueError("A report name is required")
    try:
        found = _read_entity(entity, entity_kind, client, project)
    except EntityNotExistsError:
        return {}
    matches = [
        ext for ext in getattr(found, "extensions", None) or []
        if ext.get("kind") == "compliance-report" and ext.get("name") == name
    ]
    if len(matches) > 1:
        raise ValueError(f"Duplicate report extension name '{name}'")
    return dict(matches[0].get("spec") or {}) if matches else {}


def save_report_extensions(
    entity: str, entity_kind: str, reports: dict[str, dict[str, Any]], *,
    client: Any | None = None, project: str | None = None,
) -> None:
    """Validate all reports and stage a single update, preserving other extensions."""
    from compliance_core.contracts.reports import ReportSpec

    _report_target(entity, project)
    if not reports or any(not name.strip() for name in reports):
        raise ValueError("At least one named report is required")
    normalized = {
        name: ReportSpec.model_validate(report).model_dump(mode="json", exclude_none=True)
        for name, report in reports.items()
    }
    found = _read_entity(entity, entity_kind, client, project)
    current = list(getattr(found, "extensions", None) or [])
    staged = list(current)
    for name, report in normalized.items():
        matches = [
            ext for ext in current
            if ext.get("kind") == "compliance-report" and ext.get("name") == name
        ]
        if len(matches) > 1:
            raise ValueError(f"Duplicate report extension name '{name}'")
        replacement = {**(matches[0] if matches else {}), "kind": "compliance-report", "name": name, "spec": report}
        staged = [
            ext for ext in staged
            if not (ext.get("kind") == "compliance-report" and ext.get("name") == name)
        ]
        staged.append(replacement)
    if staged == current:
        return
    _, updater = _entity_api(entity_kind, client)
    found.extensions = staged
    updater(found)


__all__ = [
    "STORE_KEY_PREFIX",
    "get_entity",
    "get_entity_extension",
    "get_extension_schema",
    "get_project_extension",
    "save_entity_extension",
    "save_project_extension",
    "get_report_extension",
    "save_report_extensions",
]
