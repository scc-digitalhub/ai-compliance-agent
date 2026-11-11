"""Interchange envelope for externally computed objective measurements."""
from __future__ import annotations

from typing import Any, Literal

from pydantic import Field, field_validator, model_validator

from .reports import MetricResult, ReportModel, finite_json


class MeasurementEnvelope(ReportModel):
    project: str = Field(min_length=1)
    entity: str = Field(min_length=1)
    objective_ref: str = Field(min_length=1)
    objective: dict[str, Any]
    metric_result: MetricResult | None = None
    specification_revision: str | None = None
    entity_version: str | None = None
    selector: str | None = None
    status: Literal["SUCCESS", "ERROR", "INCOMPLETE"] = "SUCCESS"
    error: str | None = None
    evidence: dict[str, Any] = Field(default_factory=dict)
    provenance: dict[str, Any] = Field(default_factory=dict)

    @field_validator("objective", "evidence", "provenance")
    @classmethod
    def json_data(cls, value: dict[str, Any]) -> dict[str, Any]:
        return finite_json(value)

    @model_validator(mode="after")
    def linkage(self) -> "MeasurementEnvelope":
        from ..objective_evaluation import validate_condition
        from ..objective_refs import snapshot_hash
        validate_condition(self.objective.get("condition"))
        metric = self.objective.get("metric")
        if not isinstance(metric, dict) or not metric.get("id"):
            raise ValueError("objective requires an embedded metric identity")
        if self.objective.get("id") and self.objective["id"] != self.objective_ref:
            raise ValueError("objective reference does not match authoritative objective id")
        if self.status == "SUCCESS" and (self.metric_result is None or self.error is not None):
            raise ValueError("successful result requires a measurement and no error")
        if self.status != "SUCCESS" and not self.error:
            raise ValueError("failed/incomplete result requires an explanation")
        if self.metric_result:
            supplied = self.metric_result.metric.model_dump(mode="json", exclude_none=True)
            from .common import MetricOut
            expected = MetricOut.model_validate(metric).model_dump(mode="json", exclude_none=True)
            if supplied != expected:
                raise ValueError("measurement metric does not match objective metric snapshot")
        expected_hash = self.provenance.get("objective_snapshot_hash")
        if expected_hash is not None and expected_hash != snapshot_hash(self.objective):
            raise ValueError("objective snapshot changed")
        return self


class BuildReportRequest(ReportModel):
    results: list[MeasurementEnvelope] = Field(min_length=1)
    variants: list[Literal["EVALUATION", "TEST"]] = Field(default_factory=lambda: ["EVALUATION", "TEST"], min_length=1)
    lineage: dict[str, Any] | None = None


class ValidateReportRequest(ReportModel):
    report: dict[str, Any]
