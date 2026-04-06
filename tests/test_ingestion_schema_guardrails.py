from pathlib import Path

from sqlalchemy import text
from sqlalchemy.exc import ProgrammingError

from app.services.demo_seed_service import DemoSeedService
from app.services.opportunity_import_service import OpportunityImportService


def _missing_table_error() -> ProgrammingError:
    return ProgrammingError(
        "INSERT INTO operational_job_runs ...",
        {},
        Exception('relation "operational_job_runs" does not exist'),
    )


def test_fixture_ingest_returns_structured_schema_error(client, monkeypatch):
    monkeypatch.setattr(
        OpportunityImportService,
        "import_fixture",
        lambda *args, **kwargs: (_ for _ in ()).throw(_missing_table_error()),
    )

    response = client.post("/opportunities/ingest/dev/fixture")
    assert response.status_code == 503
    detail = response.json()["detail"]
    assert detail["error_code"] == "database_schema_missing"
    assert "alembic upgrade head" in detail["remediation"]


def test_bootstrap_returns_structured_schema_error(client, monkeypatch):
    monkeypatch.setattr(
        DemoSeedService,
        "bootstrap",
        lambda *args, **kwargs: (_ for _ in ()).throw(_missing_table_error()),
    )

    response = client.post(
        "/operations/bootstrap/demo",
        json={"confirm": True, "reset_demo_state": False, "create_demo_proposal": False},
    )
    assert response.status_code == 503
    detail = response.json()["detail"]
    assert detail["error_code"] == "database_schema_missing"


def test_live_ingestion_returns_structured_schema_error(client, monkeypatch):
    monkeypatch.setattr(
        OpportunityImportService,
        "ingest_live_eu_funding",
        lambda *args, **kwargs: (_ for _ in ()).throw(_missing_table_error()),
    )

    response = client.post(
        "/operations/jobs/ingestion/live",
        json={"programmes": ["horizon"], "limit": 10, "run_matching_after": False},
    )
    assert response.status_code == 503
    detail = response.json()["detail"]
    assert detail["error_code"] == "database_schema_missing"


def test_readiness_reports_missing_critical_tables(client, db_session):
    db_session.execute(text("DROP TABLE operational_job_runs"))
    db_session.commit()

    response = client.get("/health/ready")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "degraded"
    assert body["dependencies"]["migrations"]["status"] == "degraded"
    assert "operational_job_runs" in body["dependencies"]["migrations"]["missing_tables"]


def test_repair_migration_file_is_present():
    migration = Path("alembic/versions/0012_repair_operational_tables_if_missing.py")
    assert migration.exists()
    content = migration.read_text(encoding="utf-8")
    assert "operational_job_runs" in content
    assert "0012_repair_operational_tables_if_missing" in content
