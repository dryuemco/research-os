from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.schemas.health import ComponentHealth, HealthResponse


class HealthService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_health(self) -> HealthResponse:
        try:
            self.db.execute(text("SELECT 1"))
            database = ComponentHealth(status="ok")
            overall_status = "ok"
        except Exception as exc:  # pragma: no cover - exercised through tests with monkeypatch
            database = ComponentHealth(status="degraded", detail=str(exc))
            overall_status = "degraded"

        settings = get_settings()
        return HealthResponse(status=overall_status, app_env=settings.app_env, database=database)

