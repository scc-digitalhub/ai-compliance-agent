"""Request models (inputs of the structured agents and the API)."""
from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from . import enums as e
from .results import ComplianceContextOut, DataComplianceOut


class InModel(BaseModel):
    model_config = ConfigDict(extra="ignore")


def _upper(v: Any) -> Any:
    return v.strip().upper() if isinstance(v, str) else v


class DomainDescriptor(InModel):
    domain: str = Field(min_length=1, max_length=200, description="Application domain, e.g. healthcare, finance")
    subdomain: Optional[str] = Field(None, max_length=200)
    use_case: Optional[str] = Field(None, max_length=500, description="Specific use case within the domain")


class ProjectScope(InModel):
    in_scope: list[str] = Field(default_factory=list, max_length=50, description="In-scope capabilities")
    out_of_scope: list[str] = Field(default_factory=list, max_length=50, description="Out-of-scope capabilities")


def _domain(v: Any) -> Any:
    # A bare domain name is accepted for convenience.
    return {"domain": v} if isinstance(v, str) else v


class _ProjectDescription(InModel):
    """Project fields of the DH `ai-compliance` extension (okb ProjectComplianceSpec)."""

    domain: DomainDescriptor
    ai_task: e.AiTask = Field(description="AI task type, e.g. CLASSIFICATION, DETECTION, GENERATION")
    ai_task_value: Optional[str] = Field(None, max_length=200, description="Free text when ai_task is OTHER")
    goal: str = Field(min_length=1, max_length=2000, description="High-level goal of the AI application")
    purpose: Optional[str] = Field(None, max_length=2000, description="Intended function or business capability")
    audience: Optional[str] = Field(None, max_length=1000, description="Target users")
    scope: ProjectScope = Field(default_factory=ProjectScope)
    deployment: e.Deployment = "CLOUD"

    normalize_domain = field_validator("domain", mode="before")(_domain)
    normalize_enums = field_validator("ai_task", "deployment", mode="before")(_upper)


class ProjectInput(_ProjectDescription):
    name: str = Field(min_length=1, max_length=200, description="Project name (the DH project identifier)")
    # Analysis inputs; on DH they are stored in the compliance context.
    geography: list[str] = Field(default_factory=lambda: ["EU"], max_length=50, description="Deployment jurisdictions")
    environment: e.Environment = "PRODUCTION"

    normalize_environment = field_validator("environment", mode="before")(_upper)


class ProjectComplianceSpec(_ProjectDescription):
    """Specification stored as the `ai-compliance` extension of a DH project: the project description
    and its compliance context."""

    context: Optional[ComplianceContextOut] = None

    @classmethod
    def of(cls, project: ProjectInput, context: Optional[ComplianceContextOut]) -> "ProjectComplianceSpec":
        return cls.model_validate({**project.model_dump(exclude={"name", "geography", "environment"}), "context": context})

    def project(self, name: str) -> ProjectInput:
        extra = {"geography": self.context.geography, "environment": self.context.environment} if self.context else {}
        return ProjectInput.model_validate({**self.model_dump(exclude={"context"}), "name": name, **extra})


class FieldSchemaEntry(InModel):
    name: str = Field(max_length=200)
    dtype: str = Field(max_length=100)
    nullable: bool = True
    description: Optional[str] = Field(None, max_length=1000)
    sensitivity: Optional[str] = Field(None, max_length=100)


class DatasetInput(InModel):
    name: str = Field(min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=2000)
    scope: e.DatasetScope
    domain: Optional[str] = Field(None, max_length=200)
    sensitivity: Optional[e.Sensitivity] = None
    n_records: Optional[int] = Field(None, ge=0)
    schema_fields: list[FieldSchemaEntry] = Field(default_factory=list, max_length=500, description="Column definitions")
    sample_records: list[dict[str, Any]] = Field(default_factory=list, max_length=3, description="Up to 3 representative rows")
    known_protected_attributes: list[str] = Field(default_factory=list, max_length=100)

    normalize_enums = field_validator("scope", "sensitivity", mode="before")(_upper)


class ModelInput(InModel):
    name: str = Field(min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=2000)
    ai_task: str = Field(min_length=1, max_length=200, description="AI task type matching the project")
    domain: Optional[str] = Field(None, max_length=200)
    framework: Optional[str] = Field(None, max_length=100, description="e.g. PYTORCH, SKLEARN, HUGGINGFACE")
    output_type: e.OutputType = "BINARY_CLASSIFICATION"
    produces_probabilities: bool = True
    trained_on_sensitive_data: bool = False
    known_affected_groups: list[str] = Field(default_factory=list, max_length=100)

    normalize_enums = field_validator("output_type", mode="before")(_upper)


# Agent requests: the entity plus optional context produced by earlier analyses.
class DatasetAnalysisRequest(InModel):
    dataset: DatasetInput
    project: Optional[ProjectInput] = None
    project_context: Optional[ComplianceContextOut] = Field(
        None, description="Result of a previous project context analysis; requirement ids are reused"
    )


class ModelAnalysisRequest(InModel):
    model: ModelInput
    project: Optional[ProjectInput] = None
    project_context: Optional[ComplianceContextOut] = None
    dataset_compliance: list[DataComplianceOut] = Field(
        default_factory=list, max_length=10, description="Results of dataset analyses for the training data"
    )
