"""Global settings loaded from environment or .env file."""
import logging
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # OKF bundle root (absolute or relative to CWD)
    okf_bundle_path: Path = Path(__file__).parents[2] / "okf"

    # OpenAI-compatible endpoint (works with OpenAI, Azure OpenAI, GitHub Models,
    # local models via LiteLLM proxy, etc.)
    openai_api_key: str = ""
    openai_model: str = "gpt-4o"
    # Leave empty to use the default OpenAI endpoint; set to an alternative base URL
    # e.g. https://models.inference.ai.azure.com  (GitHub Models)
    #      http://localhost:11434/v1               (Ollama)
    openai_base_url: str = ""

    # Agent behaviour
    agent_max_iterations: int = 20
    agent_verbose: bool = True

    # API server
    api_host: str = "0.0.0.0"
    api_port: int = 8000

    # Streamlit backend URL (used by UI)
    api_base_url: str = "http://localhost:8000"

    # Local JSON data store
    data_path: Path = Path(__file__).parent / "data"

    # Logging
    log_level: str = "INFO"


settings = Settings()
# Only emit logs from the tools module; silence everything else
logging.basicConfig(level=logging.WARNING)
logging.getLogger("agent.tools").setLevel(settings.log_level.upper())
