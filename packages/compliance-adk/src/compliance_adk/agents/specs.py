"""Specifications of the structured agents (typed input, typed output, one skill each)."""
from __future__ import annotations

from dataclasses import dataclass

from pydantic import BaseModel

from ..config import ModelRole
from compliance_core.contracts import (
    DatasetAgentOutput,
    DatasetAnalysisRequest,
    ModelAgentOutput,
    ModelAnalysisRequest,
    ProjectContextAgentOutput,
    ProjectInput,
)


@dataclass(frozen=True)
class StructuredAgentSpec:
    key: str
    agent_name: str
    role: ModelRole
    skill_name: str
    description: str
    input_schema: type[BaseModel]
    output_schema: type[BaseModel]

    @property
    def output_key(self) -> str:
        return f"{self.key}_output"


PROJECT_CONTEXT = StructuredAgentSpec(
    key="project_context",
    agent_name="project_context_agent",
    role="project_context",
    skill_name="project-context",
    description="Builds the structured compliance context of an AI project definition.",
    input_schema=ProjectInput,
    output_schema=ProjectContextAgentOutput,
)

DATASET = StructuredAgentSpec(
    key="dataset",
    agent_name="dataset_agent",
    role="dataset",
    skill_name="dataset-analysis",
    description="Derives the structured data compliance specification of an AI dataset.",
    input_schema=DatasetAnalysisRequest,
    output_schema=DatasetAgentOutput,
)

MODEL = StructuredAgentSpec(
    key="model",
    agent_name="model_agent",
    role="model",
    skill_name="model-analysis",
    description="Derives the structured model compliance specification of an AI model.",
    input_schema=ModelAnalysisRequest,
    output_schema=ModelAgentOutput,
)

ALL_SPECS = (PROJECT_CONTEXT, DATASET, MODEL)
