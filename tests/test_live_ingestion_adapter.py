import httpx
import pytest
from sqlalchemy import select

from app.domain.common.enums import OperationalJobStatus
from app.domain.operations.models import OperationalJobRun
from app.services.operational_loop_service import OperationalLoopService
from app.services.opportunity_adapters import DEFAULT_ADAPTERS
from app.services.opportunity_adapters.eu_funding_tenders import EUFundingTendersAdapter


def test_eu_funding_adapter_fetch_records_and_normalize_from_live_payload():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "POST"
        return httpx.Response(
            200,
            json={
                "results": [
                    {
                        "identifier": "HORIZON-CL6-001",
                        "title": "AI for climate adaptation",
                        "description": "horizon climate ai",
                        "programme": "Horizon Europe",
                        "status": "OPEN",
                        "deadlineDate": "2026-11-15T17:00:00+00:00",
                        "budgetTotal": 3500000,
                        "url": "https://example.eu/horizon/HORIZON-CL6-001",
                    }
                ]
            },
        )

    adapter = EUFundingTendersAdapter(transport=httpx.MockTransport(handler))
    records = adapter.fetch_records(programmes=["horizon"], limit=10)

    assert len(records) == 1
    normalized = adapter.normalize(records[0].source_record_id, records[0].payload)
    assert normalized.source_program == "horizon"
    assert normalized.external_id == "HORIZON-CL6-001"
    assert normalized.call_status == "open"
    assert normalized.budget_total == 3500000


def test_live_ingestion_created_updated_unchanged_classification(db_session, monkeypatch):
    adapter = EUFundingTendersAdapter()
    responses = [
        [
            {
                "source_record_id": "ERASMUS-001",
                "payload": {
                    "identifier": "ERASMUS-001",
                    "title": "Erasmus digital collaboration",
                    "description": "erasmus digital exchange",
                    "programme": "Erasmus+",
                    "status": "OPEN",
                },
            }
        ],
        [
            {
                "source_record_id": "ERASMUS-001",
                "payload": {
                    "identifier": "ERASMUS-001",
                    "title": "Erasmus digital collaboration",
                    "description": "erasmus digital exchange updated",
                    "programme": "Erasmus+",
                    "status": "OPEN",
                },
            }
        ],
        [
            {
                "source_record_id": "ERASMUS-001",
                "payload": {
                    "identifier": "ERASMUS-001",
                    "title": "Erasmus digital collaboration",
                    "description": "erasmus digital exchange updated",
                    "programme": "Erasmus+",
                    "status": "OPEN",
                },
            }
        ],
    ]

    def fake_fetch(**kwargs):
        return responses.pop(0)

    monkeypatch.setattr(adapter, "_fetch_live_payload", fake_fetch)
    monkeypatch.setitem(DEFAULT_ADAPTERS, "eu_funding_tenders", adapter)

    service = OperationalLoopService(db_session)
    first = service.run_ingestion_job(
        source_name="eu_funding_tenders",
        trigger_source="test-live",
        run_matching_after=False,
        records=None,
    )
    second = service.run_ingestion_job(
        source_name="eu_funding_tenders",
        trigger_source="test-live",
        run_matching_after=False,
        records=None,
    )
    third = service.run_ingestion_job(
        source_name="eu_funding_tenders",
        trigger_source="test-live",
        run_matching_after=False,
        records=None,
    )

    assert first.result_summary["created_count"] == 1
    assert second.result_summary["updated_count"] == 1
    assert third.result_summary["unchanged_count"] == 1


def test_live_ingestion_empty_and_error_paths_are_tracked(db_session, monkeypatch):
    adapter = EUFundingTendersAdapter()

    monkeypatch.setattr(adapter, "_fetch_live_payload", lambda **kwargs: [])
    monkeypatch.setitem(DEFAULT_ADAPTERS, "eu_funding_tenders", adapter)

    service = OperationalLoopService(db_session)
    empty_run = service.run_ingestion_job(
        source_name="eu_funding_tenders",
        trigger_source="test-live",
        run_matching_after=False,
        records=None,
    )
    assert empty_run.status == OperationalJobStatus.SUCCEEDED
    assert empty_run.result_summary["total_records"] == 0

    def raise_upstream(**kwargs):
        raise RuntimeError("upstream unavailable")

    monkeypatch.setattr(adapter, "_fetch_live_payload", raise_upstream)
    with pytest.raises(RuntimeError):
        service.run_ingestion_job(
            source_name="eu_funding_tenders",
            trigger_source="test-live",
            run_matching_after=False,
            records=None,
        )

    runs = db_session.scalars(select(OperationalJobRun)).all()
    failed_runs = [run for run in runs if run.status == OperationalJobStatus.FAILED]
    assert failed_runs
    assert failed_runs[-1].result_summary["failed_count"] == 1
