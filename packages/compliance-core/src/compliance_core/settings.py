"""Framework-neutral settings shared by host adapters."""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


def _default_okf_path() -> Path:
    packaged = Path(__file__).resolve().parent / "data" / "okf"
    if packaged.is_dir():
        return packaged
    return Path(__file__).resolve().parents[2] / "okf"


class CoreSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
        populate_by_name=True,
    )

    okf_path: Path = Field(
        default_factory=_default_okf_path,
        validation_alias=AliasChoices("OKF_PATH"),
    )
    workspace_path: Path = Field(
        default_factory=Path.cwd,
        validation_alias=AliasChoices("COMPLIANCE_WORKSPACE"),
    )


@lru_cache
def get_core_settings() -> CoreSettings:
    return CoreSettings()


__all__ = ["CoreSettings", "get_core_settings"]
