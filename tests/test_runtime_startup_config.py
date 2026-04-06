from fastapi.testclient import TestClient

from app.core.config import Settings, get_settings
from app.main import app


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
