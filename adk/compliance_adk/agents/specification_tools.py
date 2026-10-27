"""ADK-compatible wrappers around framework-neutral specification tools."""
from __future__ import annotations

from typing import Any, Callable

from google.adk.tools import ToolContext

from compliance_core.ports import SpecificationKind
from compliance_core.specification_tools import (
    get_compliance_specification as _get_compliance_specification,
    save_compliance_specification as _save_compliance_specification,
)

from .tool_adapter import tool_env


def get_compliance_specification(
    kind: SpecificationKind, entity: str, tool_context: ToolContext
) -> dict[str, Any]:
    """Retrieve a stored compliance specification from the DH platform.

    The specification is also loaded into this conversation, so later analyses reuse it.

    Args:
        kind: 'project' (project description and compliance context), 'dataset' (data compliance) or 'model'.
        entity: Identifier of the project, dataset or model on the DH platform.
    """
    return _get_compliance_specification(tool_env(tool_context), kind, entity)


def save_compliance_specification(
    kind: SpecificationKind,
    entity: str,
    tool_context: ToolContext,
    specification: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Store a compliance specification on the DH platform, replacing the stored one.

    Without `specification`, the one analysed earlier in this conversation is stored. Fields managed on
    the platform only (e.g. compliance_status, documentation) are kept.

    Args:
        kind: 'project' (project description and compliance context), 'dataset' (data compliance) or 'model'.
        entity: Identifier of the project, dataset or model on the DH platform.
        specification: Optional specification to store instead of the analysed one, as provided by the user.
    """
    return _save_compliance_specification(
        tool_env(tool_context), kind, entity, specification=specification
    )


SPECIFICATION_TOOL_REGISTRY: dict[str, Callable[..., Any]] = {
    get_compliance_specification.__name__: get_compliance_specification,
    save_compliance_specification.__name__: save_compliance_specification,
}

__all__ = [
    "SPECIFICATION_TOOL_REGISTRY",
    "get_compliance_specification",
    "save_compliance_specification",
]
