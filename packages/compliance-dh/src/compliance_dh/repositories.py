"""DigitalHub implementations of the framework-neutral repository ports."""
from __future__ import annotations

from typing import Any

from compliance_core.ports import EntityKind, SpecificationKind

from . import tools

_EXTENSION_KINDS = {
    "project": "ai-compliance",
    "dataset": "data-compliance",
    "model": "model-compliance",
}


class DhEntityCatalog:
    def __init__(self, adapter: Any = tools) -> None:
        self._adapter = adapter

    def get(self, kind: EntityKind, entity: str, project: str | None = None) -> dict[str, Any]:
        return self._adapter.get_entity(entity, kind, project=project)


class DhSpecificationRepository:
    def __init__(self, adapter: Any = tools) -> None:
        self._adapter = adapter

    def get(self, kind: SpecificationKind, entity: str, project: str | None = None) -> dict[str, Any]:
        extension_kind = _EXTENSION_KINDS[kind]
        if kind == "project":
            return self._adapter.get_project_extension(entity, extension_kind)
        return self._adapter.get_entity_extension(entity, kind, extension_kind, project=project)

    def save(
        self, kind: SpecificationKind, entity: str, specification: dict[str, Any],
        project: str | None = None,
    ) -> None:
        extension_kind = _EXTENSION_KINDS[kind]
        current = self.get(kind, entity, project=project)
        merged = {**current, **specification}
        if kind == "project":
            self._adapter.save_project_extension(entity, extension_kind, merged)
        else:
            self._adapter.save_entity_extension(entity, kind, extension_kind, merged, project=project)


class DhReportRepository:
    """Named reports staged into a single entity update.

    The SDK has no conditional update/transaction contract; strict atomicity is unsupported.
    """

    supports_atomic_batch = False

    def __init__(self, adapter: Any = tools) -> None:
        self._adapter = adapter

    def get(
        self, kind: EntityKind, entity: str, name: str, project: str | None = None,
    ) -> dict[str, Any]:
        return self._adapter.get_report_extension(entity, kind, name, project=project)

    def get_specification_revision(
        self, kind: EntityKind, entity: str, project: str | None = None,
    ) -> str | None:
        """Read the current subject specification fingerprint, without claiming CAS."""
        from compliance_core.specification_tools import specification_revision

        tools._report_target(entity, project)
        extension_kind = _EXTENSION_KINDS[kind]
        current = self._adapter.get_entity_extension(entity, kind, extension_kind, project=project)
        return specification_revision(current)

    def save(
        self, kind: EntityKind, entity: str, name: str, report: dict[str, Any],
        project: str | None = None,
    ) -> None:
        self.save_batch(kind, entity, {name: report}, project)

    def save_batch(
        self, kind: EntityKind, entity: str, reports: dict[str, dict[str, Any]],
        project: str | None = None, *, strict_atomic: bool = False,
    ) -> None:
        if strict_atomic:
            raise ValueError("DigitalHub SDK does not guarantee atomic conditional report publication")
        self._adapter.save_report_extensions(entity, kind, reports, project=project)


__all__ = ["DhEntityCatalog", "DhSpecificationRepository", "DhReportRepository"]
