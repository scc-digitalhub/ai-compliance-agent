"""Pydantic output schemas matching the OKB JSON Schema definitions."""

from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


# All schema models use extra="forbid" so OpenAI strict-mode structured output
# receives additionalProperties: false on every object in the JSON schema.
class _Base(BaseModel):
    model_config = ConfigDict(extra="forbid")


# ── Foundations ───────────────────────────────────────────────────────────────

class RegulatoryRefOut(_Base):
    framework: str = Field(description="Framework id, e.g. EU_AI_ACT, GDPR")
    article: str
    uri: str
    version: Optional[str] = None


class RequirementOut(_Base):
    id: str
    name: str
    description: str
    source: RegulatoryRefOut
    requirement_text: str
    kind: str = Field(description="DESIGN|TESTING|DOCUMENTATION|MONITORING|DATA_PROTECTION|TRANSPARENCY|HUMAN_OVERSIGHT|DATA_GOVERNANCE|RISK_MANAGEMENT|CYBERSECURITY|QUALITY_MANAGEMENT|OPERATIONAL_CONTROL|OTHER")
    applicability_status: str = "APPLICABLE"
    related_requirements: list[str] = []


class AttributeRefOut(_Base):
    name: str
    semantic_type: str
    attribute_role: str
    observability: Optional[str] = None
    use_permissions: list[str] = []
    rationale: str


class GroupSpecOut(_Base):
    name: str
    description: str
    group_kind: str
    group_role: str
    vulnerability: Optional[str] = None
    rationale: str


class RiskClassificationOut(_Base):
    risk_level: str = Field(description="PROHIBITED|HIGH|LIMITED|MINIMAL|UNKNOWN|OTHER")
    classification_status: str = "PRELIMINARY"
    rationale: str


class HumanOversightOut(_Base):
    oversight_mode: str
    overseer_roles: list[str] = []
    intervention_points: list[str] = []
    authority: list[str] = []
    availability: str = "BUSINESS_HOURS"
    escalation_channels: list[str] = []
    rationale: str


class MisuseScenarioOut(_Base):
    name: str
    misuse_kind: str
    intentionality: str
    likelihood: str
    impact: str
    rationale: str


# ── Compliance Context ─────────────────────────────────────────────────────────

class ComplianceContextOut(_Base):
    """Schema-compliant ComplianceContext output."""
    environment: str = "PRODUCTION"
    regulations: list[RegulatoryRefOut]
    geography: list[str]
    actor_role: str = "PROVIDER"
    requirements: list[RequirementOut]
    affected_groups: list[GroupSpecOut] = []
    vulnerable_groups: list[GroupSpecOut] = []
    protected_attributes: list[AttributeRefOut] = []
    foreseeable_misuse: list[MisuseScenarioOut]
    risk_classification: RiskClassificationOut
    human_oversight: HumanOversightOut


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

class ProjectInput(BaseModel):
    name: str = Field(description="Project or application name")
    domain: str = Field(description="Application domain, e.g. healthcare, finance")
    subdomain: Optional[str] = None
    ai_task: str = Field(description="AI task type, e.g. CLASSIFICATION, DETECTION, GENERATION")
    goal: str = Field(description="High-level goal of the AI application")
    purpose: Optional[str] = Field(None, description="Intended function or business capability")
    audience: Optional[str] = Field(None, description="Target users")
    scope_in: list[str] = Field(default=[], description="In-scope capabilities")
    scope_out: list[str] = Field(default=[], description="Out-of-scope capabilities")
    deployment: str = Field(default="CLOUD", description="EDGE | CLOUD | EMBEDDED | PREMISE")
    geography: list[str] = Field(default=["EU"], description="Deployment jurisdictions")
    environment: str = Field(default="PRODUCTION", description="PRODUCTION | SANDBOX | PILOT")
