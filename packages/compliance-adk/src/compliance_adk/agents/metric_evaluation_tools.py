# SPDX-FileCopyrightText: © 2026 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

"""ADK adapters for metric computation and evaluation-code tools."""
from __future__ import annotations

from typing import Any, Callable

from compliance_core.metric_evaluation_tools import TOOL_SPECS

from .tool_adapter import wrap_core_tool

TOOL_REGISTRY: dict[str, Callable[..., Any]] = {
    spec.name: wrap_core_tool(spec.fn) for spec in TOOL_SPECS
}

__all__ = ["TOOL_REGISTRY"]
