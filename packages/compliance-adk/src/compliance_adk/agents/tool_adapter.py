"""Bridge ADK invocation context to the runtime-neutral ToolEnv."""
from __future__ import annotations

from typing import Any
from collections.abc import Callable
from contextvars import ContextVar

from google.adk.tools import ToolContext
from pydantic import BaseModel

from compliance_core.contracts.envelope import AnalysisResponse
from compliance_core.state import MappingStateStore
from compliance_core.tools import ToolEnv

from compliance_core.knowledge import get_bundle
from compliance_dh.repositories import DhEntityCatalog, DhSpecificationRepository

TOOL_ENV_FACTORY: ContextVar[Callable[[ToolContext], ToolEnv] | None] = ContextVar(
    "compliance_tool_env_factory", default=None
)


class AdkAnalysisEngine:
    async def run(
        self, analysis: str, request: BaseModel, request_id: str | None = None
    ) -> AnalysisResponse[Any]:
        from ..runtime import get_registry

        return await get_registry().get(analysis).run(request, request_id)


def tool_env(tool_context: ToolContext) -> ToolEnv:
    factory = TOOL_ENV_FACTORY.get()
    if factory is not None:
        return factory(tool_context)
    return ToolEnv(
        state=MappingStateStore(tool_context.state),
        bundle=get_bundle(),
        specifications=DhSpecificationRepository(),
        entities=DhEntityCatalog(),
        analysis_engine=AdkAnalysisEngine(),
    )


__all__ = ["AdkAnalysisEngine", "tool_env"]
