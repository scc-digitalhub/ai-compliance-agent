"""Transport settings; DigitalHub credentials determine project access."""
from __future__ import annotations

from pathlib import Path

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class ProtocolSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="COMPLIANCE_PROTOCOL_", extra="ignore")

    state_dir: Path = Path(".compliance/protocols")
    allow_writes: bool = False
    bearer_token: SecretStr | None = None
    public_url: str = "http://127.0.0.1:8101"
    host: str = "127.0.0.1"
    port: int = Field(8101, ge=1, le=65535)
    timeout_s: float = Field(180, gt=0)
    max_concurrency: int = Field(4, ge=1)
    approval_ttl_s: float = Field(300, gt=0)

    def prepare_directory(self) -> Path:
        directory = self.state_dir.expanduser().resolve()
        directory.mkdir(parents=True, mode=0o700, exist_ok=True)
        return directory
