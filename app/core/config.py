import os
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
    app_public_url: str | None = Field(default=None, alias="APP_PUBLIC_URL")
    docs_enabled: bool = Field(default=True, alias="DOCS_ENABLED")
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

    internal_api_key: str | None = Field(default="dev-internal-key", alias="INTERNAL_API_KEY")
    retrieval_backend: str = Field(default="lexical", alias="RETRIEVAL_BACKEND")
    retrieval_default_mode: str = Field(default="hybrid", alias="RETRIEVAL_DEFAULT_MODE")
    retrieval_lexical_weight: float = Field(default=0.6, alias="RETRIEVAL_LEXICAL_WEIGHT")
    retrieval_vector_weight: float = Field(default=0.4, alias="RETRIEVAL_VECTOR_WEIGHT")
    artifact_storage_backend: str = Field(default="local_fs", alias="ARTIFACT_STORAGE_BACKEND")
    artifact_storage_root: str = Field(default="./artifacts", alias="ARTIFACT_STORAGE_ROOT")
    artifact_download_secret: str = Field(
        default="dev-artifact-download-secret",
        alias="ARTIFACT_DOWNLOAD_SECRET",
    )
    artifact_download_ttl_seconds: int = Field(default=300, alias="ARTIFACT_DOWNLOAD_TTL_SECONDS")
    operational_scheduler_enabled: bool = Field(
        default=True, alias="OPERATIONAL_SCHEDULER_ENABLED"
    )
    operational_scheduler_tick_seconds: int = Field(
        default=60, alias="OPERATIONAL_SCHEDULER_TICK_SECONDS"
    )
    operational_source_fixture_path: str = Field(
        default="./config/dev_source_payloads.example.json",
        alias="OPERATIONAL_SOURCE_FIXTURE_PATH",
    )
    eu_funding_api_url: str = Field(
        default="https://ec.europa.eu/info/funding-tenders/opportunities/data/topicSearch",
        alias="EU_FUNDING_API_URL",
    )
    eu_funding_timeout_seconds: int = Field(default=20, alias="EU_FUNDING_TIMEOUT_SECONDS")
    allowed_origins: str = Field(default="", alias="ALLOWED_ORIGINS")
    github_pages_url: str | None = Field(
        default="https://dryuemco.github.io",
        alias="GITHUB_PAGES_URL",
    )

    def cors_origins(self) -> list[str]:
        origins: list[str] = []
        if self.allowed_origins.strip():
            origins.extend(item.strip().rstrip("/") for item in self.allowed_origins.split(","))
        if self.github_pages_url:
            origins.append(self.github_pages_url.strip().rstrip("/"))
        deduped = [item for item in dict.fromkeys(origins) if item]
        return deduped

    def cors_enabled(self) -> bool:
        return len(self.cors_origins()) > 0

    def sqlalchemy_database_url(self) -> str:
        """
        Normalize common hosted Postgres URL variants for SQLAlchemy.

        Render often provides URLs using `postgres://...`, while SQLAlchemy 2.x
        with psycopg expects `postgresql+psycopg://...`.
        """
        url = self.database_url.strip()
        if url.startswith("postgres://"):
            return "postgresql+psycopg://" + url[len("postgres://") :]
        if url.startswith("postgresql://") and "+psycopg" not in url:
            return "postgresql+psycopg://" + url[len("postgresql://") :]
        return url

    def uses_local_database_fallback(self) -> bool:
        url = self.sqlalchemy_database_url()
        return (
            "@localhost:" in url
            or "@127.0.0.1:" in url
            or "@db:" in url
        )

    def is_deployed_env(self) -> bool:
        if self.app_env.lower() in {"pilot", "staging", "prod", "production"}:
            return True
        render_flag = os.getenv("RENDER") or os.getenv("RENDER_EXTERNAL_URL")
        if render_flag:
            return True
        if self.app_public_url and "onrender.com" in self.app_public_url:
            return True
        return False

    def validate_deployment_readiness(self) -> None:
        if self.is_deployed_env() and self.uses_local_database_fallback():
            raise ValueError(
                "DATABASE_URL resolves to a local host fallback "
                "while APP_ENV indicates a deployed environment. "
                "Set DATABASE_URL to the managed external database URL."
            )

    def runtime_host(self) -> str:
        return self.app_host or "0.0.0.0"

    def runtime_port(self) -> int:
        raw = os.getenv("PORT")
        if raw and raw.isdigit():
            return int(raw)
        return self.app_port or 8000


@lru_cache
def get_settings() -> Settings:
    return Settings()
