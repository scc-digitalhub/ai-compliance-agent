"""FastAPI request/response models."""
from __future__ import annotations

from typing import Any, Optional
from pydantic import BaseModel, Field


# ── Shared ────────────────────────────────────────────────────────────────────

class FieldSchemaEntry(BaseModel):
    name: str
    dtype: str
    nullable: bool = True
    description: Optional[str] = None
    sensitivity: Optional[str] = None


# ── Task 1: Compliance Context ────────────────────────────────────────────────

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


# ── Task 2: Dataset Compliance ────────────────────────────────────────────────

class DatasetInput(BaseModel):
    name: str
    description: Optional[str] = None
    scope: str = Field(description="TRAINING | VALIDATION | SUPPORT")
    domain: Optional[str] = None
    sensitivity: Optional[str] = Field(None, description="NONE | PII | SENSITIVE | RESTRICTED | PROHIBITED")
    n_records: Optional[int] = None
    schema_fields: list[FieldSchemaEntry] = Field(default=[], description="Column definitions")
    sample_records: list[dict[str, Any]] = Field(default=[], description="Up to 3 representative rows")
    known_protected_attributes: list[str] = Field(default=[], description="Known sensitive field names")
    project: Optional[ProjectInput] = None


# ── Task 3: Model Compliance ──────────────────────────────────────────────────

class ModelInput(BaseModel):
    name: str
    description: Optional[str] = None
    ai_task: str = Field(description="AI task type matching the project")
    domain: Optional[str] = None
    framework: Optional[str] = Field(None, description="e.g. PYTORCH, SKLEARN, HUGGINGFACE")
    output_type: str = Field(default="BINARY_CLASSIFICATION",
                              description="BINARY_CLASSIFICATION | MULTI_CLASS | REGRESSION | GENERATION | RANKING")
    produces_probabilities: bool = True
    trained_on_sensitive_data: bool = False
    known_affected_groups: list[str] = Field(default=[], description="Groups affected by model decisions")
    project: Optional[ProjectInput] = None
    prior_requirements: list[dict[str, Any]] = Field(default=[],
                                                      description="Requirements from prior ComplianceContext analysis")


# ── Error ─────────────────────────────────────────────────────────────────────

class ErrorResponse(BaseModel):
    detail: str
