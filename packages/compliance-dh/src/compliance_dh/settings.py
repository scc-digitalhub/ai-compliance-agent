"""DigitalHub integration settings independent of Google ADK."""
from __future__ import annotations

from functools import lru_cache

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class DhSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
        populate_by_name=True,
    )

    dh_project: str | None = Field(
        None,
        validation_alias=AliasChoices("DH_PROJECT", "PROJECT_NAME"),
    )


@lru_cache
def get_dh_settings() -> DhSettings:
    return DhSettings()


__all__ = ["DhSettings", "get_dh_settings"]
