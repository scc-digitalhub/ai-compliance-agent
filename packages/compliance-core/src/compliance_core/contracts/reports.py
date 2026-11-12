# SPDX-FileCopyrightText: © 2026 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

"""Strict runtime contracts for OKF measurements and report specifications."""
from __future__ import annotations

import math
from datetime import datetime
from typing import Any, Literal

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, StrictBool, model_validator, field_validator

from .common import MetricOut


class ReportModel(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)


def finite_json(value: Any) -> Any:
    if value is None or isinstance(value, (str, bool, int)):
        return value
    if isinstance(value, float) and math.isfinite(value):
        return value
    if isinstance(value, list):
        return [finite_json(item) for item in value]
    if isinstance(value, dict) and all(isinstance(key, str) for key in value):
        return {key: finite_json(item) for key, item in value.items()}
    raise ValueError("values must be finite JSON data")


def numeric(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


class ConfidenceInterval(ReportModel):
    lower: float
    upper: float
    level: float

    @model_validator(mode="after")
    def bounds(self) -> "ConfidenceInterval":
        if self.lower > self.upper or not 0 < self.level < 1:
            raise ValueError("invalid confidence interval bounds or level")
        return self


class MetricResult(ReportModel):
    metric: MetricOut
    value: Any
    computed_at: AwareDatetime
    confidence: ConfidenceInterval | None = None

    @field_validator("computed_at", mode="before")
    @classmethod
    def timestamp(cls, value: Any) -> Any:
        if not isinstance(value, (str, datetime)):
            raise ValueError("computed_at must be an explicit timezone-aware timestamp")
        return value

    @field_validator("value")
    @classmethod
    def json_value(cls, value: Any) -> Any:
        return finite_json(value)

    @model_validator(mode="after")
    def domain(self) -> "MetricResult":
        bounds = self.metric.range
        if bounds:
            finite_json(bounds.model_dump())
            if bounds.lower is not None and bounds.upper is not None and bounds.lower > bounds.upper:
                raise ValueError("metric range lower exceeds upper")
            def check(value: Any) -> None:
                if isinstance(value, dict):
                    for item in value.values():
                        check(item)
                elif numeric(value):
                    if bounds.lower is not None and value < bounds.lower:
                        raise ValueError("measurement is below metric range")
                    if bounds.upper is not None and value > bounds.upper:
                        raise ValueError("measurement is above metric range")
                    if bounds.discrete and int(value) != value:
                        raise ValueError("measurement must be discrete")
                elif bounds.categories is not None and value not in bounds.categories:
                    raise ValueError("measurement is outside metric categories")
            check(self.value)
        if self.confidence and numeric(self.value):
            if not self.confidence.lower <= self.value <= self.confidence.upper:
                raise ValueError("confidence interval does not contain measured value")
        return self


class EvaluationContent(ReportModel):
    metrics: list[MetricResult]
    summary: str | None = None


class TestResult(ReportModel):
    __test__ = False
    measured: str
    expected: dict[str, Any]
    passed: StrictBool
    details: str | None = None

    @field_validator("expected")
    @classmethod
    def condition(cls, value: dict[str, Any]) -> dict[str, Any]:
        from ..objective_evaluation import validate_condition
        return validate_condition(value)


class TestContent(ReportModel):
    __test__ = False
    results: list[TestResult] = Field(default_factory=list)
    verdict: Literal["PASS", "FAIL", "INCONCLUSIVE", "ERROR"]
    summary: str | None = None

    @model_validator(mode="after")
    def consistent(self) -> "TestContent":
        if self.verdict == "PASS" and (not self.results or not all(item.passed for item in self.results)):
            raise ValueError("PASS requires nonempty successful determinate checks")
        if self.verdict == "FAIL" and not any(not item.passed for item in self.results):
            raise ValueError("FAIL requires a failed determinate check")
        return self


class LogWindow(ReportModel):
    from_: AwareDatetime = Field(alias="from")
    to: AwareDatetime

    @model_validator(mode="after")
    def ordered(self) -> "LogWindow":
        if self.from_ > self.to:
            raise ValueError("log window is reversed")
        return self


class LogContent(ReportModel):
    kind: Literal["INPUT_OUTPUT", "RESOURCE", "EVENT", "AUDIT"]
    window: LogWindow


class ReportContent(ReportModel):
    evaluation: EvaluationContent | None = None
    test: TestContent | None = None
    log: LogContent | None = None

    @model_validator(mode="after")
    def one_variant(self) -> "ReportContent":
        if sum(getattr(self, name) is not None for name in ("evaluation", "test", "log")) != 1:
            raise ValueError("exactly one report content variant must be populated")
        return self


class Lineage(ReportModel):
    sources: list[str] = Field(default_factory=list)
    operation: str | None = None


class ReportSpec(ReportModel):
    kind: Literal["EVALUATION", "TEST", "LOG"]
    content: ReportContent
    lineage: Lineage | None = None
    objectives: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def agreement(self) -> "ReportSpec":
        if getattr(self.content, self.kind.lower()) is None:
            raise ValueError("report kind and content variant disagree")
        if len(set(self.objectives)) != len(self.objectives):
            raise ValueError("objective references must be unique")
        return self
