# SPDX-FileCopyrightText: © 2026 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

"""Contracts for generated metric-evaluator code artifacts.

These are deliberately separate from measurement interchange: generated source is an artifact,
not evidence that a metric has been evaluated.
"""
from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

CodeStatus = Literal["ready", "needs_input", "unsupported"]


class CodeContract(BaseModel):
    model_config = ConfigDict(extra="forbid")


class MetricEvaluationCodeRequest(CodeContract):
    """Ground a Python evaluator in a specific target, objective and explicit bindings."""

    project: str = Field(min_length=1)
    entity_kind: Literal["dataset", "model"]
    entity: str = Field(min_length=1)
    entity_version: str | None = None
    objective_ref: str = Field(min_length=1)
    objective: dict[str, Any]
    bindings: dict[str, Any] = Field(
        default_factory=dict,
        description="Explicit input-to-metric bindings; no input is inferred from entity metadata.",
    )
    evaluation_data: dict[str, Any] | None = Field(
        None, description="Explicit evaluation data contract for a model objective, not the data itself."
    )
    selected_outputs: dict[str, Any] = Field(
        default_factory=dict, description="Explicit selectors for multi-valued metric outputs."
    )
    computation_guidance: dict[str, Any] = Field(
        default_factory=dict,
        description="Exact resolver output from the selected OKF bundle; source material, not executable input.",
    )


class EntityInputContract(CodeContract):
    """Declared read-only interface expected by a generated evaluator."""

    kind: Literal["dataset", "model", "dataitem"]
    name: str = Field(min_length=1)
    project: str = Field(min_length=1)
    entity_version: str | None = None
    interface: Literal["mapping", "attributes", "digitalhub"]
    read_only: Literal[True] = True
    fields: dict[str, Any] = Field(default_factory=dict)


class MetricEvaluationCodeArtifact(CodeContract):
    status: CodeStatus
    artifact_id: str | None = None
    source_code: str | None = None
    source_hash: str | None = None
    entry_point: str | None = None
    entity_contract: EntityInputContract | None = None
    result_contract: dict[str, Any] = Field(default_factory=dict)
    dependencies: list[str] = Field(default_factory=list)
    parameters: dict[str, Any] = Field(default_factory=dict)
    objective_ref: str | None = None
    objective: dict[str, Any] | None = None
    metric: dict[str, Any] | None = None
    source_paths: list[str] = Field(default_factory=list)
    source_hashes: dict[str, str] = Field(default_factory=dict)
    bundle_version: str | None = None
    required_inputs: list[str] = Field(default_factory=list)
    missing_inputs: list[str] = Field(default_factory=list)
    unsupported_reasons: list[str] = Field(default_factory=list)
    validation: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def _consistent_readiness(self) -> "MetricEvaluationCodeArtifact":
        if self.status == "ready":
            if not self.source_code or not self.entry_point:
                raise ValueError("ready artifacts require source_code and entry_point")
            if self.entity_contract is None:
                raise ValueError("ready artifacts require a declared entity input contract")
            if self.missing_inputs or self.unsupported_reasons:
                raise ValueError("ready artifacts cannot have missing inputs or unsupported reasons")
        elif self.source_code is not None:
            raise ValueError("non-ready artifacts must not contain executable source_code")
        if self.status == "needs_input" and not self.missing_inputs:
            raise ValueError("needs_input artifacts require at least one missing input")
        if self.status == "unsupported" and not self.unsupported_reasons:
            raise ValueError("unsupported artifacts require at least one reason")
        return self


class MetricEvaluationCodeOutput(CodeContract):
    """Structured-engine response: result plus general-knowledge assumptions."""

    result: MetricEvaluationCodeArtifact
    assumptions: list[str] = Field(default_factory=list)


__all__ = [
    "CodeStatus",
    "EntityInputContract",
    "MetricEvaluationCodeArtifact",
    "MetricEvaluationCodeOutput",
    "MetricEvaluationCodeRequest",
]
