"""ADK adapters for report construction, report persistence and reporting-code tools."""
from __future__ import annotations

from typing import Any, Callable

from compliance_core.report_code_tools import TOOL_SPECS as REPORT_CODE_TOOL_SPECS
from compliance_core.report_tools import REPORT_TOOL_SPECS

from .tool_adapter import wrap_core_tool

TOOL_REGISTRY: dict[str, Callable[..., Any]] = {
    spec.name: wrap_core_tool(spec.fn)
    for spec in (*REPORT_TOOL_SPECS, *REPORT_CODE_TOOL_SPECS)
}

__all__ = ["TOOL_REGISTRY"]
