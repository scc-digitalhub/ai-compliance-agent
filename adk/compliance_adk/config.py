"""Runtime settings, read from environment variables and adk/.env."""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Literal, Optional

from pydantic import AliasChoices, Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

from .errors import ConfigError

PACKAGE_DIR = Path(__file__).resolve().parent
ADK_DIR = PACKAGE_DIR.parent
REPO_DIR = ADK_DIR.parent

ModelRole = Literal["project_context", "dataset", "model", "coordinator"]


class Settings(BaseSettings):
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

    structured_temperature: float = Field(0.2, validation_alias=AliasChoices("STRUCTURED_TEMPERATURE"))
    # Gemini-only; leave unset for providers that do not support a thinking budget.
    structured_thinking_budget: Optional[int] = Field(
        None, validation_alias=AliasChoices("STRUCTURED_THINKING_BUDGET")
    )
    coordinator_thinking_budget: Optional[int] = Field(
        None, validation_alias=AliasChoices("COORDINATOR_THINKING_BUDGET")
    )

    okf_path: Path = Field(REPO_DIR / "okf", validation_alias=AliasChoices("OKF_PATH"))
    skills_path: Path = Field(PACKAGE_DIR / "skills", validation_alias=AliasChoices("SKILLS_PATH"))

    max_concurrency: int = Field(4, ge=1, validation_alias=AliasChoices("MAX_CONCURRENCY"))
    request_timeout_s: float = Field(120.0, gt=0, validation_alias=AliasChoices("REQUEST_TIMEOUT_S"))
    max_validation_retries: int = Field(2, ge=0, validation_alias=AliasChoices("MAX_VALIDATION_RETRIES"))

    api_keys: str = Field("", validation_alias=AliasChoices("API_KEYS"))
    cors_origins: str = Field("", validation_alias=AliasChoices("CORS_ORIGINS"))
    max_body_bytes: int = Field(1_000_000, gt=0, validation_alias=AliasChoices("MAX_BODY_BYTES"))

    @property
    def api_key_list(self) -> list[str]:
        return [k.strip() for k in self.api_keys.split(",") if k.strip()]

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    def model_name_for(self, role: ModelRole) -> str:
        specific = {
            "project_context": self.project_context_model,
            "dataset": self.dataset_model,
            "model": self.model_analysis_model,
            "coordinator": self.coordinator_model,
        }[role]
        name = specific or (None if role == "coordinator" else self.structured_model)
        if not name:
            hint = "COORDINATOR_MODEL" if role == "coordinator" else "STRUCTURED_MODEL"
            raise ConfigError(f"No model configured for '{role}'; set {hint} (see adk/.env.example).")
        return name


@lru_cache
def get_settings() -> Settings:
    return Settings()
