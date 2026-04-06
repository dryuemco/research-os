from pathlib import Path

from app.core.config import Settings


def test_cors_origins_parsing_from_csv():
    settings = Settings(ALLOWED_ORIGINS="https://a.example, https://b.example")
    assert settings.cors_origins() == ["https://a.example", "https://b.example"]


def test_cors_origins_empty_when_not_configured():
    settings = Settings(ALLOWED_ORIGINS="")
    assert settings.cors_origins() == []


def test_cors_origins_include_github_pages_url_and_dedupe():
    settings = Settings(
        ALLOWED_ORIGINS="https://dryuemco.github.io/,https://api.example.com",
        GITHUB_PAGES_URL="https://dryuemco.github.io",
    )
    assert settings.cors_origins() == ["https://dryuemco.github.io", "https://api.example.com"]


def test_deployed_env_rejects_local_database_fallback():
    settings = Settings(APP_ENV="pilot", DATABASE_URL="postgresql+psycopg://postgres:postgres@localhost:5432/research_os")
    try:
        settings.validate_deployment_readiness()
    except ValueError as exc:
        assert "DATABASE_URL resolves to a local host fallback" in str(exc)
    else:  # pragma: no cover
        raise AssertionError("Expected deployment readiness validation to fail in pilot mode")


def test_dockerfile_has_long_running_web_cmd():
    dockerfile = Path("Dockerfile").read_text(encoding="utf-8")
    assert 'CMD ["python", "-m", "app.main"]' in dockerfile
