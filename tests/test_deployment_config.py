from pathlib import Path

from app.core.config import Settings


def test_cors_origins_parsing_from_csv():
    settings = Settings(ALLOWED_ORIGINS="https://a.example, https://b.example")
    assert settings.cors_origins() == ["https://a.example", "https://b.example"]


def test_cors_origins_empty_when_not_configured():
    settings = Settings(ALLOWED_ORIGINS="")
    assert settings.cors_origins() == []


def test_dockerfile_has_long_running_web_cmd():
    dockerfile = Path("Dockerfile").read_text(encoding="utf-8")
    assert 'CMD ["python", "-m", "app.main"]' in dockerfile
