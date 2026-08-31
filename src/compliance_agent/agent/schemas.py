"""Pydantic output schemas matching the OKB JSON Schema definitions."""
from __future__ import annotations

from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


# All schema models use extra="forbid" so OpenAI strict-mode structured output
# receives additionalProperties: false on every object in the JSON schema.
class _Base(BaseModel):
    model_config = ConfigDict(extra="forbid")


# ── Foundations ───────────────────────────────────────────────────────────────

class RegulatoryRefOut(_Base):
    framework: str = Field(description="Framework id, e.g. EU_AI_ACT, GDPR")
    article: Optional[str] = None
    version: Optional[str] = None
    uri: Optional[str] = None


class RequirementOut(_Base):
    id: str
    name: str
    description: Optional[str] = None
    source: RegulatoryRefOut
    requirement_text: str
    summary: Optional[str] = None
    kind: str = Field(description="DESIGN|TESTING|DOCUMENTATION|MONITORING|DATA_PROTECTION|TRANSPARENCY|HUMAN_OVERSIGHT|DATA_GOVERNANCE|RISK_MANAGEMENT|CYBERSECURITY|QUALITY_MANAGEMENT|OPERATIONAL_CONTROL|OTHER")
    applicability_status: str = "APPLICABLE"
    related_requirements: list[str] = []


class AttributeRefOut(_Base):
    id: str
    name: str
    semantic_type: str
    semantic_type_value: Optional[str] = None
    attribute_role: str
    attribute_role_value: Optional[str] = None
    observability: Optional[str] = None
    use_permissions: list[str] = []
    rationale: Optional[str] = None


class GroupSpecOut(_Base):
    id: str
    name: str
    description: Optional[str] = None
    group_kind: str
    group_role: str
    vulnerability: Optional[str] = None
    vulnerability_value: Optional[str] = None
    rationale: Optional[str] = None


class RiskClassificationOut(_Base):
    risk_level: str = Field(description="PROHIBITED|HIGH|LIMITED|MINIMAL|UNKNOWN|OTHER")
    risk_level_value: Optional[str] = None
    classification_status: str = "PRELIMINARY"
    rationale: Optional[str] = None


class HumanOversightOut(_Base):
    oversight_mode: str
    overseer_roles: list[str] = []
    intervention_points: list[str] = []
    authority: list[str] = []
    availability: str = "BUSINESS_HOURS"
    escalation_channels: list[str] = []
    rationale: Optional[str] = None


class MisuseScenarioOut(_Base):
    id: str
    name: str
    misuse_kind: str
    intentionality: str
    likelihood: str
    impact: str
    rationale: Optional[str] = None


# ── Compliance Context ─────────────────────────────────────────────────────────

class ComplianceContextOut(_Base):
    """Schema-compliant ComplianceContext output."""
    environment: str = "PRODUCTION"
    regulations: list[RegulatoryRefOut] = []
    geography: list[str] = []
    actor_role: str = "PROVIDER"
    actor_role_value: Optional[str] = None
    requirements: list[RequirementOut] = []
    affected_groups: list[GroupSpecOut] = []
    vulnerable_groups: list[GroupSpecOut] = []
    protected_attributes: list[AttributeRefOut] = []
    foreseeable_misuse: list[MisuseScenarioOut] = []
    risk_classification: Optional[RiskClassificationOut] = None
    human_oversight: Optional[HumanOversightOut] = None


# ── Objectives & Metrics ───────────────────────────────────────────────────────

class UnitOfMeasureOut(_Base):
    symbol: str
    name: str


class ValueRangeOut(_Base):
    lower: Optional[float] = None
    upper: Optional[float] = None
    discrete: bool = False
    categories: Optional[list[str]] = None


class MetricOut(_Base):
    id: str
    name: str
    description: Optional[str] = None
    kind: str
    scale: str
    unit: Optional[UnitOfMeasureOut] = None
    range: Optional[ValueRangeOut] = None


class ThresholdConditionOut(_Base):
    operator: str = Field(description="GEQ|LEQ|GT|LT|EQ|NEQ")
    value: float


class RangeConditionOut(_Base):
    lower: float
    upper: float
    inclusive: bool = True


class ObjectiveConditionOut(_Base):
    threshold: Optional[ThresholdConditionOut] = None
    range: Optional[RangeConditionOut] = None


class ComplianceObjectiveOut(_Base):
    name: str
    description: str
    metric: MetricOut
    condition: ObjectiveConditionOut
    priority: str = Field(description="MANDATORY|RECOMMENDED|INFORMATIONAL")
    severity: str = Field(description="CRITICAL|HIGH|MEDIUM|LOW|INFO")
    requirements: list[str] = Field(default=[], description="Linked requirement ids")
    rationale: Optional[str] = None


# ── Top-level responses ────────────────────────────────────────────────────────

class ComplianceContextResponse(_Base):
    """Full response for the compliance context task."""
    narrative_summary: str
    regulatory_analysis: str
    risk_analysis: str
    oversight_analysis: str
    compliance_context: ComplianceContextOut


class DataComplianceResponse(_Base):
    """Full response for the dataset compliance task."""
    narrative_summary: str
    data_quality_analysis: str
    privacy_analysis: str
    fairness_analysis: str
    scope: str
    protected_attributes: list[AttributeRefOut]
    objectives: list[ComplianceObjectiveOut]


class ModelComplianceResponse(_Base):
    """Full response for the model compliance task."""
    narrative_summary: str
    fairness_analysis: str
    robustness_analysis: str
    transparency_analysis: str
    objectives: list[ComplianceObjectiveOut]
