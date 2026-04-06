import json
from pathlib import Path

from sqlalchemy import func, select

from app.domain.institutional_memory.models import ReusableEvidenceBlock
from app.domain.operations.models import Notification
from app.domain.opportunity_discovery.models import MatchResult, Opportunity
from app.domain.partner_intelligence.models import PartnerProfile
from app.domain.proposal_factory.models import Proposal
from app.services.demo_seed_service import DemoSeedService


def test_demo_seed_service_bootstrap_populates_minimum_workflow(db_session):
    fixture_path = str(Path("config/dev_source_payloads.example.json"))

    result = DemoSeedService(db_session).bootstrap(fixture_path=fixture_path)
    db_session.commit()

    assert result.opportunities_loaded >= 3
    assert result.matches_created >= 1
    assert result.notifications_created >= 1

    assert db_session.scalar(select(func.count()).select_from(Opportunity)) >= 3
    assert db_session.scalar(select(func.count()).select_from(MatchResult)) >= 1
    assert db_session.scalar(select(func.count()).select_from(Notification)) >= 1
    assert db_session.scalar(select(func.count()).select_from(PartnerProfile)) >= 2
    assert db_session.scalar(select(func.count()).select_from(ReusableEvidenceBlock)) >= 1
    assert db_session.scalar(select(func.count()).select_from(Proposal)) >= 1


def test_ingest_dev_fixture_endpoint_runs_ingestion_and_matching(client, db_session, tmp_path):
    fixture = {
        "source_name": "funding_call_scaffold",
        "records": [
            {
                "source_record_id": "fixture-api-1",
                "payload": {
                    "external_id": "fixture-api-1",
                    "source_program": "horizon",
                    "source_url": "https://example.org/fixture-api-1",
                    "title": "AI resilience mission",
                    "summary": "AI climate resilience and health preparedness",
                    "full_text": "AI climate resilience and health preparedness",
                    "budget_total": 2200000,
                    "currency": "EUR",
                    "deadline_at": "2026-12-01T17:00:00+00:00",
                },
            }
        ],
    }
    fixture_path = tmp_path / "fixture.json"
    fixture_path.write_text(json.dumps(fixture), encoding="utf-8")

    DemoSeedService(db_session).bootstrap(
        fixture_path=str(Path("config/dev_source_payloads.example.json")),
        create_demo_proposal=False,
    )
    db_session.commit()

    response = client.post(
        "/opportunities/ingest/dev/fixture",
        params={"fixture_path": str(fixture_path), "run_matching_after": True},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["job_status"] == "succeeded"
    assert body["result_summary"]["total_records"] == 1

    summary = client.get("/dashboard/summary")
    assert summary.status_code == 200
    assert summary.json()["opportunities"] >= 1
    assert summary.json()["matches"] >= 1
