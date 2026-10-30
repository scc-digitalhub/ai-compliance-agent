"""ADK view of the core analysis definitions (typed input, typed output, one skill each)."""
from __future__ import annotations

from dataclasses import dataclass, fields

from compliance_core import analysis_engine as core
from compliance_core.analysis_engine import AnalysisDefinition

from ..config import ModelRole


@dataclass(frozen=True)
class StructuredAgentSpec(AnalysisDefinition):
    @classmethod
    def of(cls, definition: AnalysisDefinition) -> "StructuredAgentSpec":
        return cls(**{item.name: getattr(definition, item.name) for item in fields(AnalysisDefinition)})

    @property
    def role(self) -> ModelRole:
        return self.key

    @property
    def input_schema(self):
        return self.request_model

    @property
    def output_schema(self):
        return self.output_model

    @property
    def output_key(self) -> str:
        return f"{self.key}_output"


PROJECT_CONTEXT = StructuredAgentSpec.of(core.PROJECT_CONTEXT)
DATASET = StructuredAgentSpec.of(core.DATASET)
MODEL = StructuredAgentSpec.of(core.MODEL)
ALL_SPECS = (PROJECT_CONTEXT, DATASET, MODEL)
