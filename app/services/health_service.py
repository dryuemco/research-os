from pathlib import Path

from alembic.config import Config
from alembic.script import ScriptDirectory
from sqlalchemy import inspect, text
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.schemas.health import ComponentHealth, HealthResponse
from app.services.artifact_storage.factory import build_artifact_storage


class HealthService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_health(self) -> HealthResponse:
        settings = get_settings()
        migration_dependency = self._migration_health()
        try:
            self.db.execute(text("SELECT 1"))
            database = ComponentHealth(status="ok")
            overall_status = "ok"
        except Exception as exc:  # pragma: no cover - exercised through tests with monkeypatch
            database = ComponentHealth(status="degraded", detail=str(exc))
            overall_status = "degraded"

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
        if migration_dependency["status"] != "ok":
            overall_status = "degraded"
        return HealthResponse(
            status=overall_status,
            app_env=settings.app_env,
            database=database,
            dependencies={
                "artifact_storage": {"status": storage_status, "detail": storage_detail},
                "migrations": migration_dependency,
                "config": {
                    "database_uses_local_fallback": settings.uses_local_database_fallback(),
                    "cors_origins_count": len(settings.cors_origins()),
                    "cors_origins": settings.cors_origins(),
                },
            },
        )

    def _migration_health(self) -> dict:
        required_tables = [
            "opportunity_ingestion_snapshots",
            "operational_job_configs",
            "operational_job_runs",
            "matching_runs",
            "notifications",
            "audit_events",
        ]
        inspector = inspect(self.db.bind)
        missing_tables = [name for name in required_tables if not inspector.has_table(name)]
        if missing_tables:
            return {
                "status": "degraded",
                "detail": (
                    "Missing critical tables: "
                    + ", ".join(missing_tables)
                    + ". Run 'alembic upgrade head' before enabling write endpoints."
                ),
                "missing_tables": missing_tables,
            }

        try:
            current_rev = self.db.execute(text("SELECT version_num FROM alembic_version")).scalar()
        except Exception as exc:
            settings = get_settings()
            if not settings.is_deployed_env():
                return {
                    "status": "ok",
                    "detail": "alembic_version table not present in local/test environment",
                }
            return {
                "status": "degraded",
                "detail": f"Cannot read alembic_version: {exc}",
            }

        try:
            repo_root = Path(__file__).resolve().parents[2]
            alembic_ini = repo_root / "alembic.ini"
            cfg = Config(str(alembic_ini))
            cfg.set_main_option("script_location", str(repo_root / "alembic"))
            head_rev = ScriptDirectory.from_config(cfg).get_current_head()
        except Exception as exc:
            return {
                "status": "degraded",
                "detail": f"Cannot resolve migration head: {exc}",
                "current_revision": current_rev,
            }

        if current_rev != head_rev:
            return {
                "status": "degraded",
                "detail": (
                    f"Database revision {current_rev} is behind head {head_rev}. "
                    "Run 'alembic upgrade head'."
                ),
                "current_revision": current_rev,
                "expected_revision": head_rev,
            }
        return {"status": "ok", "current_revision": current_rev, "expected_revision": head_rev}
