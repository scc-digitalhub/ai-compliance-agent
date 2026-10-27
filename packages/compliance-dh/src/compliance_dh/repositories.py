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

    def get(self, kind: EntityKind, entity: str) -> dict[str, Any]:
        return self._adapter.get_entity(entity, kind)


class DhSpecificationRepository:
    def __init__(self, adapter: Any = tools) -> None:
        self._adapter = adapter

    def get(self, kind: SpecificationKind, entity: str) -> dict[str, Any]:
        extension_kind = _EXTENSION_KINDS[kind]
        if kind == "project":
            return self._adapter.get_project_extension(entity, extension_kind)
        return self._adapter.get_entity_extension(entity, kind, extension_kind)

    def save(self, kind: SpecificationKind, entity: str, specification: dict[str, Any]) -> None:
        extension_kind = _EXTENSION_KINDS[kind]
        current = self.get(kind, entity)
        merged = {**current, **specification}
        if kind == "project":
            self._adapter.save_project_extension(entity, extension_kind, merged)
        else:
            self._adapter.save_entity_extension(entity, kind, extension_kind, merged)


__all__ = ["DhEntityCatalog", "DhSpecificationRepository"]
