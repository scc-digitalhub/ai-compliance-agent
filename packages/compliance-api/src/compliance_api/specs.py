"""Runtime-neutral request/output metadata for API analyses."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from pydantic import BaseModel

from compliance_core.contracts import (
    DatasetAnalysisRequest,
    DatasetAgentOutput,
    ModelAnalysisRequest,
    ModelAgentOutput,
    ProjectContextAgentOutput,
    ProjectInput,
)

AnalysisKey = Literal["project_context", "dataset", "model"]


@dataclass(frozen=True)
class AnalysisSpec:
    key: AnalysisKey
    agent_name: str
    skill_name: str
    request_model: type[BaseModel]
    output_model: type[BaseModel]
    validator_tool: str


PROJECT_CONTEXT = AnalysisSpec(
    "project_context",
    "project_context_agent",
    "project-context",
    ProjectInput,
    ProjectContextAgentOutput,
    "validate_project_context",
)
DATASET = AnalysisSpec(
    "dataset",
    "dataset_agent",
    "dataset-analysis",
    DatasetAnalysisRequest,
    DatasetAgentOutput,
    "validate_dataset_compliance",
)
MODEL = AnalysisSpec(
    "model",
    "model_agent",
    "model-analysis",
    ModelAnalysisRequest,
    ModelAgentOutput,
    "validate_model_compliance",
)
ALL_SPECS = (PROJECT_CONTEXT, DATASET, MODEL)

__all__ = ["ALL_SPECS", "AnalysisKey", "AnalysisSpec", "DATASET", "MODEL", "PROJECT_CONTEXT"]
