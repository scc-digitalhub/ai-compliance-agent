"""Ports implemented by host, persistence, and analysis-runtime adapters."""
from __future__ import annotations

from typing import Any, Literal, Protocol

from pydantic import BaseModel

from .contracts.envelope import AnalysisResponse

SpecificationKind = Literal["project", "dataset", "model"]
EntityKind = Literal["dataset", "model"]


class SpecificationRepository(Protocol):
    def get(self, kind: SpecificationKind, entity: str, project: str | None = None) -> dict[str, Any]: ...

    def save(
        self, kind: SpecificationKind, entity: str, specification: dict[str, Any],
        project: str | None = None,
    ) -> None: ...


class EntityCatalog(Protocol):
    def get(self, kind: EntityKind, entity: str, project: str | None = None) -> dict[str, Any]: ...


class AnalysisEngine(Protocol):
    async def run(
        self, analysis: str, request: BaseModel, request_id: str | None = None
    ) -> AnalysisResponse[Any]: ...


class GroundingRecorder(Protocol):
    def record(self, path: str) -> None: ...

    def paths(self) -> list[str]: ...


__all__ = [
    "AnalysisEngine",
    "EntityCatalog",
    "EntityKind",
    "GroundingRecorder",
    "SpecificationKind",
    "SpecificationRepository",
]
