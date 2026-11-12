# SPDX-FileCopyrightText: © 2026 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

"""Output building blocks matching the OKB JSON Schemas."""
from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator

from . import enums as e


# extra="forbid" gives every object additionalProperties:false, required by strict structured output.
class OutModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class RegulatoryRefOut(OutModel):
    framework: str = Field(description="Framework id, e.g. EU_AI_ACT, GDPR")
    article: Optional[str] = Field(None, description="e.g. Art. 9")
    uri: Optional[str] = None
    version: Optional[str] = None


class RequirementOut(OutModel):
    id: str = Field(description="Catalog id when the requirement comes from the OKF bundle")
    name: str
    description: str
    source: RegulatoryRefOut
    requirement_text: str
    summary: Optional[str] = None
    kind: e.RequirementKind
    applicability_status: e.ApplicabilityStatus = "APPLICABLE"
    related_requirements: list[str] = Field(default_factory=list)


class AttributeRefOut(OutModel):
    id: Optional[str] = Field(None, description="Catalog id when taken from the OKF bundle")
    name: str
    semantic_type: e.SemanticType
    semantic_type_value: Optional[str] = Field(None, description="Free text when semantic_type is OTHER")
    attribute_role: e.AttributeRole
    attribute_role_value: Optional[str] = Field(None, description="Free text when attribute_role is OTHER")
    observability: Optional[e.Observability] = None
    use_permissions: list[e.UsePermission] = Field(default_factory=list)
    rationale: str


class GroupSpecOut(OutModel):
    id: Optional[str] = Field(None, description="Catalog id when taken from the OKF bundle")
    name: str
    description: str
    group_kind: e.GroupKind
    group_kind_value: Optional[str] = Field(None, description="Free text when group_kind is OTHER")
    group_role: e.GroupRole
    group_role_value: Optional[str] = Field(None, description="Free text when group_role is OTHER")
    vulnerability: Optional[e.Vulnerability] = None
    vulnerability_value: Optional[str] = Field(None, description="Free text when vulnerability is OTHER")
    rationale: str


class RiskClassificationOut(OutModel):
    risk_level: e.RiskLevel
    risk_level_value: Optional[str] = Field(None, description="Free text when risk_level is OTHER")
    classification_status: e.ClassificationStatus = "PRELIMINARY"
    rationale: str


class HumanOversightOut(OutModel):
    oversight_mode: e.OversightMode
    oversight_mode_value: Optional[str] = Field(None, description="Free text when oversight_mode is OTHER")
    overseer_roles: list[e.ActorRole] = Field(default_factory=list, description="Roles of the parties exercising oversight")
    intervention_points: list[e.InterventionPoint] = Field(default_factory=list)
    authority: list[e.OversightAuthority] = Field(default_factory=list)
    availability: e.OversightAvailability = "BUSINESS_HOURS"
    escalation_channels: list[e.EscalationChannel] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)
    rationale: str


class MisuseScenarioOut(OutModel):
    id: Optional[str] = Field(None, description="Catalog id when taken from the OKF bundle")
    name: str
    misuse_kind: e.MisuseKind
    misuse_kind_value: Optional[str] = Field(None, description="Free text when misuse_kind is OTHER")
    intentionality: e.Intentionality = "UNKNOWN"
    likelihood: e.Likelihood = "UNKNOWN"
    impact: e.Impact = "UNKNOWN"
    rationale: str


class UnitOfMeasureOut(OutModel):
    symbol: str
    name: str


class ValueRangeOut(OutModel):
    lower: Optional[float] = None
    upper: Optional[float] = None
    discrete: bool = False
    categories: Optional[list[str]] = None


class MetricOut(OutModel):
    id: str = Field(description="Catalog id when the metric comes from the OKF bundle")
    name: str
    description: Optional[str] = None
    kind: e.MetricKind
    scale: e.MetricScale
    unit: Optional[UnitOfMeasureOut] = None
    range: Optional[ValueRangeOut] = None


class ThresholdConditionOut(OutModel):
    operator: e.ThresholdOperator
    value: float


class RangeConditionOut(OutModel):
    lower: float
    upper: float
    inclusive: bool = True


class CategoricalConditionOut(OutModel):
    allowed: list[str]


class StatisticalConditionOut(OutModel):
    test: str
    significance: float
    hypothesis: str


class ObjectiveConditionOut(OutModel):
    """Exactly one condition must be set (composite conditions are not generated)."""

    threshold: Optional[ThresholdConditionOut] = None
    range: Optional[RangeConditionOut] = None
    categorical: Optional[CategoricalConditionOut] = None
    statistical: Optional[StatisticalConditionOut] = None

    @model_validator(mode="after")
    def _exactly_one(self) -> "ObjectiveConditionOut":
        set_fields = [k for k in type(self).model_fields if getattr(self, k) is not None]
        if len(set_fields) != 1:
            raise ValueError(f"exactly one condition must be set, got {set_fields or 'none'}")
        return self


class ComplianceObjectiveOut(OutModel):
    name: str
    description: str
    metric: MetricOut
    condition: ObjectiveConditionOut
    priority: e.Priority
    severity: e.Severity
    requirements: list[str] = Field(default_factory=list, description="Linked requirement ids")
    rationale: Optional[str] = None
