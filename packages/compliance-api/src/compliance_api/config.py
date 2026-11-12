# SPDX-FileCopyrightText: © 2026 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

"""Settings for the standalone REST and LiteLLM service."""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import AliasChoices, Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

ModelRole = Literal[
    "project_context", "dataset", "model", "metric_evaluation_code", "compliance_report_code"
]


class ApiSettings(BaseSettings):
    model_config = SettingsConfigDict(extra="ignore", populate_by_name=True)

    structured_model: str | None = Field(None, validation_alias=AliasChoices("STRUCTURED_MODEL"))
    project_context_model: str | None = Field(
        None, validation_alias=AliasChoices("PROJECT_CONTEXT_AGENT_MODEL_NAME")
    )
    dataset_model: str | None = Field(
        None, validation_alias=AliasChoices("DATA_ANALYSIS_AGENT_MODEL_NAME")
    )
    model_analysis_model: str | None = Field(
        None, validation_alias=AliasChoices("MODEL_ANALYSIS_AGENT_MODEL_NAME")
    )
    llm_api_base: str | None = Field(None, validation_alias=AliasChoices("LLM_API_BASE"))
    llm_api_key: SecretStr | None = Field(None, validation_alias=AliasChoices("LLM_API_KEY"))
    structured_temperature: float | None = Field(
        None, validation_alias=AliasChoices("STRUCTURED_TEMPERATURE")
    )
    max_concurrency: int = Field(4, ge=1, validation_alias=AliasChoices("MAX_CONCURRENCY"))
    request_timeout_s: float = Field(120.0, gt=0, validation_alias=AliasChoices("REQUEST_TIMEOUT_S"))
    max_validation_retries: int = Field(
        2, ge=0, validation_alias=AliasChoices("MAX_VALIDATION_RETRIES")
    )
    api_keys: str = Field("", validation_alias=AliasChoices("API_KEYS"))
    cors_origins: str = Field("", validation_alias=AliasChoices("CORS_ORIGINS"))
    max_body_bytes: int = Field(1_000_000, gt=0, validation_alias=AliasChoices("MAX_BODY_BYTES"))
    enable_dh: bool = Field(
        True, validation_alias=AliasChoices("COMPLIANCE_ENABLE_DH"),
        description="Give analyses the DigitalHub specification and entity tools",
    )

    @property
    def api_key_list(self) -> list[str]:
        return [key.strip() for key in self.api_keys.split(",") if key.strip()]

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    def model_name_for(self, role: ModelRole) -> str:
        model = {
            "project_context": self.project_context_model,
            "dataset": self.dataset_model,
            "model": self.model_analysis_model,
            "metric_evaluation_code": None,
            "compliance_report_code": None,
        }[role] or self.structured_model
        if not model:
            hint = (
                "STRUCTURED_MODEL"
                if role in ("metric_evaluation_code", "compliance_report_code")
                else "STRUCTURED_MODEL or its per-analysis override"
            )
            raise ValueError(
                f"No model configured for '{role}'; set {hint}."
            )
        return model


@lru_cache
def get_settings() -> ApiSettings:
    return ApiSettings()


__all__ = ["ApiSettings", "ModelRole", "get_settings"]
