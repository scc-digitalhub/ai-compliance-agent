"""Runtime settings, read from environment variables and adk/.env."""
from __future__ import annotations

from functools import lru_cache
from importlib.resources import files
from pathlib import Path
from typing import Literal, Optional

from pydantic import AliasChoices, Field, SecretStr
from pydantic_settings import SettingsConfigDict

from compliance_core.errors import ConfigurationError
from compliance_core.settings import CoreSettings

PACKAGE_DIR = Path(__file__).resolve().parent
ADK_DIR = PACKAGE_DIR.parent
if PACKAGE_DIR.parent.name == "src" and PACKAGE_DIR.parent.parent.name == "compliance-adk":
    ADK_DIR = PACKAGE_DIR.parents[3] / "adk"
DEFAULT_SKILLS_PATH = Path(str(files("compliance_skills").joinpath("skills")))

ModelRole = Literal[
    "project_context",
    "dataset",
    "model",
    "metric_evaluation_code",
    "compliance_report_code",
    "coordinator",
]


class Settings(CoreSettings):
    model_config = SettingsConfigDict(
        env_file=ADK_DIR / ".env", extra="ignore", populate_by_name=True
    )

    # Models are LiteLLM ids; per-agent values override the shared role default.
    structured_model: Optional[str] = Field(None, validation_alias=AliasChoices("STRUCTURED_MODEL"))
    project_context_model: Optional[str] = Field(
        None, validation_alias=AliasChoices("PROJECT_CONTEXT_AGENT_MODEL_NAME")
    )
    dataset_model: Optional[str] = Field(
        None, validation_alias=AliasChoices("DATA_ANALYSIS_AGENT_MODEL_NAME")
    )
    model_analysis_model: Optional[str] = Field(
        None, validation_alias=AliasChoices("MODEL_ANALYSIS_AGENT_MODEL_NAME")
    )
    coordinator_model: Optional[str] = Field(
        None, validation_alias=AliasChoices("COORDINATOR_MODEL", "ROOT_AGENT_MODEL_NAME")
    )
    llm_api_base: Optional[str] = Field(None, validation_alias=AliasChoices("LLM_API_BASE"))
    llm_api_key: Optional[SecretStr] = Field(None, validation_alias=AliasChoices("LLM_API_KEY"))

    structured_temperature: Optional[float] = Field(
        None, validation_alias=AliasChoices("STRUCTURED_TEMPERATURE")
    )
    # Gemini-only; leave unset for providers that do not support a thinking budget.
    structured_thinking_budget: Optional[int] = Field(
        None, validation_alias=AliasChoices("STRUCTURED_THINKING_BUDGET")
    )
    coordinator_thinking_budget: Optional[int] = Field(
        None, validation_alias=AliasChoices("COORDINATOR_THINKING_BUDGET")
    )

    skills_path: Path = Field(DEFAULT_SKILLS_PATH, validation_alias=AliasChoices("SKILLS_PATH"))

    max_concurrency: int = Field(4, ge=1, validation_alias=AliasChoices("MAX_CONCURRENCY"))
    request_timeout_s: float = Field(120.0, gt=0, validation_alias=AliasChoices("REQUEST_TIMEOUT_S"))
    max_validation_retries: int = Field(2, ge=0, validation_alias=AliasChoices("MAX_VALIDATION_RETRIES"))

    def model_name_for(self, role: ModelRole) -> str:
        specific = {
            "project_context": self.project_context_model,
            "dataset": self.dataset_model,
            "model": self.model_analysis_model,
            "metric_evaluation_code": None,
            "compliance_report_code": None,
            "coordinator": self.coordinator_model,
        }[role]
        name = specific or (None if role == "coordinator" else self.structured_model)
        if not name:
            hint = "COORDINATOR_MODEL" if role == "coordinator" else "STRUCTURED_MODEL"
            raise ConfigurationError(
                f"No model configured for '{role}'; set {hint} (see adk/.env.example)."
            )
        return name


@lru_cache
def get_settings() -> Settings:
    return Settings()
