"""Pydantic output schemas matching the OKB JSON Schema definitions."""

from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


# All schema models use extra="forbid" so OpenAI strict-mode structured output
# receives additionalProperties: false on every object in the JSON schema.
class _Base(BaseModel):
    model_config = ConfigDict(extra="forbid")


# ── Foundations ───────────────────────────────────────────────────────────────

class AttributeRefOut(_Base):
    name: str
    semantic_type: str
    attribute_role: str
    observability: Optional[str] = None
    use_permissions: list[str] = []
    rationale: str

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


# ── Data Compliance ─────────────────────────────────────────────────────────

class DataComplianceOut(_Base):
    """Full response for the dataset compliance task."""
    scope: str = Field(description="TRAINING|VALIDATION|OTHER")
    protected_attributes: list[AttributeRefOut]
    objectives: list[ComplianceObjectiveOut]
