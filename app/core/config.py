from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = Field(default="Research Proposal OS", alias="APP_NAME")
    app_env: str = Field(default="local", alias="APP_ENV")
    app_host: str = Field(default="0.0.0.0", alias="APP_HOST")
    app_port: int = Field(default=8000, alias="APP_PORT")
    app_debug: bool = Field(default=False, alias="APP_DEBUG")
    database_url: str = Field(
        default="postgresql+psycopg://postgres:postgres@localhost:5432/research_os",
        alias="DATABASE_URL",
    )
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    default_timezone: str = Field(default="UTC", alias="DEFAULT_TIMEZONE")
    model_routing_policy_path: str = Field(
        default="./config/model_routing_policy.example.json",
        alias="MODEL_ROUTING_POLICY_PATH",
    )

    openai_compatible_base_url: str = Field(
        default="https://api.openai.com/v1",
        alias="OPENAI_COMPATIBLE_BASE_URL",
    )
    openai_compatible_api_key: str | None = Field(
        default=None,
        alias="OPENAI_COMPATIBLE_API_KEY",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
