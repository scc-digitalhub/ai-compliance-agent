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