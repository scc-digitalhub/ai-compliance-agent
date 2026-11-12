# SPDX-FileCopyrightText: © 2026 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

"""ADK-compatible wrappers around the framework-neutral entity tools."""
from __future__ import annotations

from typing import Any, Callable

from google.adk.tools import ToolContext

from compliance_core.entity_tools import (
    ENTITY_KINDS,
    get_entity_details as _get_entity_details,
)
from compliance_core.ports import EntityKind

from .tool_adapter import tool_env


def get_entity_details(
    kind: EntityKind, entity: str, tool_context: ToolContext, refresh: bool = False,
    project: str | None = None,
) -> dict[str, Any]:
    """Retrieve the details of a dataset or model registered on the DH platform.

    The details are kept in this conversation: later calls return them without contacting the platform
    (source 'session') unless `refresh` is True.

    Args:
        kind: 'dataset' or 'model'.
        entity: Name of the dataset or model on the DH platform.
        refresh: True only when the user asks to reload the details from the DH platform.
        project: DigitalHub project explicitly named by the user; defaults to the conversation project.
    """
    return _get_entity_details(tool_env(tool_context), kind, entity, refresh, project=project)


ENTITY_TOOL_REGISTRY: dict[str, Callable[..., Any]] = {
    get_entity_details.__name__: get_entity_details,
}

__all__ = ["ENTITY_KINDS", "ENTITY_TOOL_REGISTRY", "EntityKind", "get_entity_details"]
