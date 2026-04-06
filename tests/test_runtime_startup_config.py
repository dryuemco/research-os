from fastapi.middleware.cors import CORSMiddleware
from fastapi.testclient import TestClient

from app.core.config import Settings, get_settings
from app.main import _startup_summary, app


def test_database_url_normalization_for_render_style_url():
    settings = Settings(DATABASE_URL="postgres://user:pass@db.example.com:5432/rpos")
    assert settings.sqlalchemy_database_url().startswith("postgresql+psycopg://")


def test_runtime_port_prefers_render_port(monkeypatch):
    monkeypatch.setenv("PORT", "18000")
    settings = Settings(APP_PORT=8000)
    assert settings.runtime_port() == 18000


def test_runtime_port_falls_back_to_app_port(monkeypatch):
    monkeypatch.delenv("PORT", raising=False)
    settings = Settings(APP_PORT=8123)
    assert settings.runtime_port() == 8123


def test_app_bootstrap_serves_ready_and_docs_routes():
    get_settings.cache_clear()
    client = TestClient(app)

    ready = client.get("/health/ready")
    assert ready.status_code == 200

    docs = client.get("/docs")
    assert docs.status_code == 200


def test_startup_summary_includes_non_secret_runtime_fields():
    summary = _startup_summary()
    assert "host" in summary
    assert "port" in summary
    assert "database_url_scheme" in summary
    assert "database_uses_local_fallback" in summary
    assert "cors_enabled" in summary
    assert "cors_origins" in summary
    assert "using_default_internal_api_key" in summary


def test_cors_middleware_is_registered():
    middleware_types = [item.cls for item in app.user_middleware]
    assert CORSMiddleware in middleware_types
