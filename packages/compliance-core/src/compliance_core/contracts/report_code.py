"""Contracts for standalone and combined report-executable artifacts."""
from __future__ import annotations

from typing import Any, Literal

from pydantic import Field, model_validator

from .evaluation_code import CodeContract, CodeStatus, MetricEvaluationCodeArtifact

ReportLanguage = Literal["python", "shell"]
ReportCodeMode = Literal["standalone", "combined"]


class ReportCodeRequest(CodeContract):
    project: str = Field(min_length=1)
    entity_kind: Literal["dataset", "model"]
    entity: str = Field(min_length=1)
    entity_version: str | None = None
    language: ReportLanguage
    mode: ReportCodeMode = "standalone"
    report_names: dict[str, str] = Field(
        default_factory=dict,
        description="Report kind to stable named-extension key, e.g. EVALUATION -> evaluation-2026.",
    )
    variants: list[Literal["EVALUATION", "TEST"]] = Field(
        default_factory=lambda: ["EVALUATION"],
        description="Requested separate OKF report variants.",
    )
    input_contract: dict[str, Any] = Field(default_factory=dict)
    objective_snapshots: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Explicit list of {objective_ref, objective} snapshots for the requested run.",
    )
    evaluator_artifacts: list[MetricEvaluationCodeArtifact] = Field(default_factory=list)
    runtime_context: dict[str, Any] = Field(
        default_factory=dict,
        description="Explicit runtime environment and invocation context; never include credentials.",
    )
    strict_atomic: bool = False

    @model_validator(mode="after")
    def _valid_composition(self) -> "ReportCodeRequest":
        if not self.variants or len(self.variants) != len(set(self.variants)):
            raise ValueError("variants must be non-empty and unique")
        if set(self.report_names) - set(self.variants):
            raise ValueError("report_names may only include requested variants")
        if any(not name.strip() for name in self.report_names.values()):
            raise ValueError("report names must be non-empty")
        if len(set(self.report_names.values())) != len(self.report_names):
            raise ValueError("report names must be unique")
        return self


class ReportCodeArtifact(CodeContract):
    status: CodeStatus
    artifact_id: str | None = None
    language: ReportLanguage
    mode: ReportCodeMode
    files: dict[str, str] = Field(default_factory=dict)
    entry_point: str | None = None
    invocation: list[str] = Field(default_factory=list)
    dependencies: list[str] = Field(default_factory=list)
    input_contract: dict[str, Any] = Field(default_factory=dict)
    output_contract: dict[str, Any] = Field(default_factory=dict)
    objective_snapshots: list[dict[str, Any]] = Field(default_factory=list)
    target: dict[str, Any] = Field(default_factory=dict)
    report_names: dict[str, str] = Field(default_factory=dict)
    declared_effects: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Explicit runtime publication effects, bound to the requested target and report names.",
    )
    source_hashes: dict[str, str] = Field(default_factory=dict)
    validation: dict[str, Any] = Field(default_factory=dict)
    missing_inputs: list[str] = Field(default_factory=list)
    unsupported_reasons: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def _consistent_readiness(self) -> "ReportCodeArtifact":
        if self.status == "ready":
            if not self.files or not self.entry_point:
                raise ValueError("ready artifacts require files and an entry_point")
            if self.missing_inputs or self.unsupported_reasons:
                raise ValueError("ready artifacts cannot have missing inputs or unsupported reasons")
        elif self.files:
            raise ValueError("non-ready artifacts must not contain generated files")
        if self.status == "needs_input" and not self.missing_inputs:
            raise ValueError("needs_input artifacts require at least one missing input")
        if self.status == "unsupported" and not self.unsupported_reasons:
            raise ValueError("unsupported artifacts require at least one reason")
        return self


class ReportCodeOutput(CodeContract):
    """Structured-engine response: generated artifact plus explicit assumptions."""

    result: ReportCodeArtifact
    assumptions: list[str] = Field(default_factory=list)


__all__ = [
    "ReportCodeArtifact",
    "ReportCodeMode",
    "ReportCodeOutput",
    "ReportCodeRequest",
    "ReportLanguage",
]
