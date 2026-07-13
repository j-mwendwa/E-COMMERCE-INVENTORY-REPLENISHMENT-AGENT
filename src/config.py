from pathlib import Path
from typing import Any

import yaml
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT_DIR = Path(__file__).resolve().parent.parent
CONFIG_PATH = ROOT_DIR / "configs" / "config.yaml"


def load_config_yaml() -> dict[str, Any]:
    with open(CONFIG_PATH) as f:
        return yaml.safe_load(f)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    anthropic_api_key: str = Field(default="")
    google_api_key: str = Field(default="")
    app_env: str = Field(default="development")
    vector_backend: str = Field(default="")
    qdrant_url: str = Field(default="")
    qdrant_api_key: str = Field(default="")
    memory_encryption_key: str = Field(default="")
    langsmith_api_key: str = Field(default="")
    langsmith_tracing: bool = Field(default=False)
    allowed_api_keys: str = Field(default="dev-local-key")
    database_url: str = Field(default="")
    slack_webhook_url: str = Field(default="")
    use_mock_supplier_api: bool = Field(default=True)

    @property
    def allowed_api_keys_list(self) -> list[str]:
        return [k.strip() for k in self.allowed_api_keys.split(",") if k.strip()]


settings = Settings()
cfg: dict[str, Any] = load_config_yaml()
