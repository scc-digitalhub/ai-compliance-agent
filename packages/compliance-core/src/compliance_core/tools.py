"""Runtime-neutral tool metadata and dependencies supplied by each host adapter."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Literal

from .knowledge import OkfBundle
from .ports import AnalysisEngine, EntityCatalog, GroundingRecorder, ReportRepository, SpecificationRepository
from .state import StateStore

ToolGroup = Literal["knowledge", "validation", "analysis", "session", "dh"]


@dataclass(frozen=True)
class ToolSpec:
    name: str
    fn: Callable[..., Any]
    group: ToolGroup
    description: str
    read_only: bool
    destructive: bool = False
    needs_llm: bool = False


@dataclass
class ToolEnv:
    state: StateStore
    bundle: OkfBundle
    specifications: SpecificationRepository | None = None
    entities: EntityCatalog | None = None
    analysis_engine: AnalysisEngine | None = None
    grounding: GroundingRecorder | None = None
    reports: ReportRepository | None = None
    input_reader: Callable[[str], bytes] | None = None


__all__ = ["ToolEnv", "ToolGroup", "ToolSpec"]
