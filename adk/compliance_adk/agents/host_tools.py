"""ADK adapters for the framework-neutral host-driven analysis tools."""
from __future__ import annotations

from typing import Any

from google.adk.tools import ToolContext

from compliance_core.host_tools import record_compliance_analysis as _record
from compliance_core.validation_tools import (
    AnalysisKind,
    get_output_schema,
    validate_dataset_compliance as _validate_dataset,
    validate_model_compliance as _validate_model,
    validate_project_context as _validate_project,
)

from .tool_adapter import tool_env


def validate_project_context(
    request: Any, output: Any, tool_context: ToolContext
) -> dict[str, Any]:
    """Validate host-generated project context against its schema and OKF semantics."""
    return _validate_project(request, output, tool_env(tool_context).bundle)


def validate_dataset_compliance(
    request: Any, output: Any, tool_context: ToolContext
) -> dict[str, Any]:
    """Validate host-generated dataset compliance output against its schema and OKF semantics."""
    return _validate_dataset(request, output, tool_env(tool_context).bundle)


def validate_model_compliance(
    request: Any, output: Any, tool_context: ToolContext
) -> dict[str, Any]:
    """Validate host-generated model compliance output against its schema and OKF semantics."""
    return _validate_model(request, output, tool_env(tool_context).bundle)


def record_compliance_analysis(
    kind: AnalysisKind,
    request: Any,
    output: Any,
    tool_context: ToolContext,
) -> dict[str, Any]:
    """Validate and store a host-generated compliance analysis in the current conversation."""
    return _record(tool_env(tool_context), kind, request, output)


HOST_TOOL_REGISTRY = {
    "get_output_schema": get_output_schema,
    "validate_project_context": validate_project_context,
    "validate_dataset_compliance": validate_dataset_compliance,
    "validate_model_compliance": validate_model_compliance,
    "record_compliance_analysis": record_compliance_analysis,
}

__all__ = [
    "HOST_TOOL_REGISTRY",
    "get_output_schema",
    "record_compliance_analysis",
    "validate_dataset_compliance",
    "validate_model_compliance",
    "validate_project_context",
]
