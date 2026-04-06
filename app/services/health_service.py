from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.schemas.health import ComponentHealth, HealthResponse
from app.services.artifact_storage.factory import build_artifact_storage


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
        storage_status = "ok"
        storage_detail = settings.artifact_storage_backend
        try:
            storage = build_artifact_storage()
            probe = storage.store(
                package_id="_health_probe",
                file_name="probe.txt",
                content_bytes=b"ok",
                checksum="2689367b205c16ce32ed4200942b8b8b1e262dfc70d9bc9fbc77c49699a4f1df",
            )
            if not storage.verify(probe.locator, probe.checksum):
                storage_status = "degraded"
                storage_detail = "checksum verification failed"
        except Exception as exc:  # pragma: no cover
            storage_status = "degraded"
            storage_detail = str(exc)
            overall_status = "degraded"
        return HealthResponse(
            status=overall_status,
            app_env=settings.app_env,
            database=database,
            dependencies={"artifact_storage": {"status": storage_status, "detail": storage_detail}},
        )
