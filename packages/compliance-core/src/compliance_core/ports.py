# SPDX-FileCopyrightText: © 2026 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

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

class ReportRepository(Protocol):
    """Named report extensions; strict atomicity must be explicitly supported."""

    supports_atomic_batch: bool

    def get(
        self, kind: EntityKind, entity: str, name: str, project: str | None = None,
    ) -> dict[str, Any]: ...

    def save(
        self, kind: EntityKind, entity: str, name: str, report: dict[str, Any],
        project: str | None = None,
    ) -> None: ...

    def save_batch(
        self, kind: EntityKind, entity: str, reports: dict[str, dict[str, Any]],
        project: str | None = None, *, strict_atomic: bool = False,
    ) -> None: ...


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
    "ReportRepository",
    "SpecificationKind",
    "SpecificationRepository",
]
