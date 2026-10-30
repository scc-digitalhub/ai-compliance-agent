"""ADK-compatible wrappers around framework-neutral coordinator tools."""
from __future__ import annotations

from typing import Any, Optional

from google.adk.tools import ToolContext

from compliance_core.analysis_tools import (
    ANALYSIS_TOOL_SPECS,
    _stored_on_dh as _core_stored_on_dh,
    analyze_dataset as _analyze_dataset,
    analyze_model as _analyze_model,
    analyze_project_context as _analyze_project_context,
    get_session_analyses as _get_session_analyses,
)
from compliance_core.contracts import DatasetInput, ModelInput, ProjectInput
from compliance_core.ports import SpecificationKind

from .tool_adapter import tool_env


def _stored_on_dh(
    kind: SpecificationKind, entity: str, tool_context: ToolContext
) -> Optional[dict[str, Any]]:
    return _core_stored_on_dh(tool_env(tool_context), kind, entity)


async def analyze_project_context(
    project: ProjectInput, tool_context: ToolContext, rerun: bool = False
) -> dict[str, Any]:
    """Build the structured compliance context of an AI project definition.

    The DH platform is checked first. Existing complete specifications are returned without
    analysis until the user asks for a re-run.

    Args:
        project: Project definition (name, domain, ai_task and goal are required).
        rerun: True only when the user asked to re-run an existing analysis.
    """
    return await _analyze_project_context(tool_env(tool_context), project, rerun)


async def analyze_dataset(
    dataset: DatasetInput,
    tool_context: ToolContext,
    project: Optional[ProjectInput] = None,
    rerun: bool = False,
) -> dict[str, Any]:
    """Derive the structured compliance specification of an AI dataset.

    The stored project context is attached automatically; the DH platform is checked first.

    Args:
        dataset: Dataset definition (name and scope are required).
        project: Optional project definition; defaults to the one already analyzed.
        rerun: True only when the user asked to re-run an existing analysis.
    """
    return await _analyze_dataset(tool_env(tool_context), dataset, project, rerun)


async def analyze_model(
    model: ModelInput,
    tool_context: ToolContext,
    project: Optional[ProjectInput] = None,
    rerun: bool = False,
) -> dict[str, Any]:
    """Derive the structured compliance specification of an AI model.

    Stored project context and dataset analyses are attached automatically; the DH platform is
    checked first.

    Args:
        model: Model definition (name and ai_task are required).
        project: Optional project definition; defaults to the one already analyzed.
        rerun: True only when the user asked to re-run an existing analysis.
    """
    return await _analyze_model(tool_env(tool_context), model, project, rerun)


def get_session_analyses(tool_context: ToolContext, project: Optional[str] = None) -> dict[str, Any]:
    """Return analyses and DH entity details already loaded into this conversation."""
    return _get_session_analyses(tool_env(tool_context), project)


_FUNCTIONS = (
    analyze_project_context,
    analyze_dataset,
    analyze_model,
    get_session_analyses,
)
_CORE_FUNCTIONS = {spec.name: spec.fn for spec in ANALYSIS_TOOL_SPECS}
for _function in _FUNCTIONS:
    _function.__doc__ = _CORE_FUNCTIONS[_function.__name__].__doc__

COORDINATOR_TOOLS = _FUNCTIONS

__all__ = [
    "COORDINATOR_TOOLS",
    "analyze_dataset",
    "analyze_model",
    "analyze_project_context",
    "get_session_analyses",
]
