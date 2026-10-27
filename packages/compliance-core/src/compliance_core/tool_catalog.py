"""Canonical framework-neutral registry of compliance tool definitions."""
from __future__ import annotations

from typing import Any

from .analysis_tools import ANALYSIS_TOOL_SPECS
from .entity_tools import TOOL_SPEC as ENTITY_TOOL_SPEC
from .host_tools import RECORD_ANALYSIS_TOOL_SPEC
from .knowledge_tools import TOOL_SPECS as KNOWLEDGE_TOOL_SPECS
from .specification_tools import SPECIFICATION_TOOL_SPECS
from .tools import ToolEnv, ToolSpec
from .validation_tools import (
    AnalysisKind,
    get_output_schema as _get_output_schema,
    validate_dataset_compliance as _validate_dataset_compliance,
    validate_model_compliance as _validate_model_compliance,
    validate_project_context as _validate_project_context,
)


def validate_project_context(env: ToolEnv, request: Any, output: Any) -> dict[str, Any]:
    """Validate a host-generated project context against its schema and OKF semantics."""
    return _validate_project_context(request, output, env.bundle)


def validate_dataset_compliance(env: ToolEnv, request: Any, output: Any) -> dict[str, Any]:
    """Validate a host-generated dataset result against its schema and OKF semantics."""
    return _validate_dataset_compliance(request, output, env.bundle)


def validate_model_compliance(env: ToolEnv, request: Any, output: Any) -> dict[str, Any]:
    """Validate a host-generated model result against its schema and OKF semantics."""
    return _validate_model_compliance(request, output, env.bundle)


def get_output_schema(kind: AnalysisKind) -> dict[str, Any]:
    """Return the JSON Schema a host model must follow for an analysis result."""
    return _get_output_schema(kind)


VALIDATION_TOOL_SPECS = (
    ToolSpec(
        name="validate_project_context",
        fn=validate_project_context,
        group="validation",
        description=validate_project_context.__doc__ or "",
        read_only=True,
    ),
    ToolSpec(
        name="validate_dataset_compliance",
        fn=validate_dataset_compliance,
        group="validation",
        description=validate_dataset_compliance.__doc__ or "",
        read_only=True,
    ),
    ToolSpec(
        name="validate_model_compliance",
        fn=validate_model_compliance,
        group="validation",
        description=validate_model_compliance.__doc__ or "",
        read_only=True,
    ),
    ToolSpec(
        name="get_output_schema",
        fn=get_output_schema,
        group="validation",
        description=get_output_schema.__doc__ or "",
        read_only=True,
    ),
)

TOOL_SPECS = (
    *KNOWLEDGE_TOOL_SPECS,
    *VALIDATION_TOOL_SPECS,
    RECORD_ANALYSIS_TOOL_SPEC,
    ENTITY_TOOL_SPEC,
    *SPECIFICATION_TOOL_SPECS,
    *ANALYSIS_TOOL_SPECS,
)
TOOL_CATALOG = {spec.name: spec for spec in TOOL_SPECS}

if len(TOOL_CATALOG) != len(TOOL_SPECS):
    raise RuntimeError("Tool catalog contains duplicate names")

__all__ = ["TOOL_CATALOG", "TOOL_SPECS", "VALIDATION_TOOL_SPECS"]
