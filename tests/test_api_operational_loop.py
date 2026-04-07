from app.domain.opportunity_discovery.models import InterestProfile
from app.services.opportunity_adapters import DEFAULT_ADAPTERS
from app.services.opportunity_adapters.base import AdapterFetchError
from app.services.opportunity_adapters.eu_funding_tenders import EUFundingTendersAdapter


def _seed_profile(db_session) -> InterestProfile:
    profile = InterestProfile(
        user_id="ops-admin",
        name="Ops API Profile",
        parameters_json={
            "allowed_programs": ["horizon"],
            "preferred_keywords": ["ai", "climate"],
            "weights": {"keyword_overlap": 0.7, "budget_fit": 0.3},
        },
    )
    db_session.add(profile)
    db_session.commit()
    return profile


def test_operational_end_to_end_api_flow(client, db_session):
    profile = _seed_profile(db_session)

    ingest = client.post(
        "/operations/jobs/ingestion",
        json={
            "source_name": "funding_call_scaffold",
            "trigger_source": "api-test",
            "run_matching_after": True,
            "records": [
                {
                    "source_record_id": "api-op-1",
                    "payload": {
                        "external_id": "api-op-1",
                        "source_program": "horizon",
                        "title": "AI for resilient health systems",
                        "summary": "AI health climate",
                        "full_text": "ai health climate",
                    },
                }
            ],
        },
    )
    assert ingest.status_code == 200

    jobs = client.get("/operations/jobs")
    assert jobs.status_code == 200
    assert jobs.json()

    matching_runs = client.get("/operations/matching-runs")
    assert matching_runs.status_code == 200
    assert matching_runs.json()

    notifications = client.get("/operations/notifications", params={"user_id": "ops-admin"})
    assert notifications.status_code == 200
    assert notifications.json()

    manual_matching = client.post(
        "/operations/jobs/matching",
        json={
            "profile_id": profile.id,
            "scoring_policy_id": "default-v1",
            "trigger_source": "manual-test",
        },
    )
    assert manual_matching.status_code == 200

    notif_id = notifications.json()[0]["id"]
    mark = client.post(f"/operations/notifications/{notif_id}/read", json={"user_id": "ops-admin"})
    assert mark.status_code == 200
    assert mark.json()["status"] == "read"


def test_live_ingestion_api_flow(client, monkeypatch):
    from app.core.config import get_settings

    monkeypatch.setenv("EU_FUNDING_LIVE_ENABLED", "true")
    get_settings.cache_clear()
    adapter = EUFundingTendersAdapter()
    monkeypatch.setattr(
        adapter,
        "_fetch_live_payload",
        lambda **kwargs: [
            {
                "source_record_id": "HORIZON-LIVE-001",
                "payload": {
                    "identifier": "HORIZON-LIVE-001",
                    "title": "Live horizon call",
                    "description": "horizon ai climate",
                    "programme": "Horizon Europe",
                    "status": "OPEN",
                },
            }
        ],
    )
    monkeypatch.setitem(DEFAULT_ADAPTERS, "eu_funding_tenders", adapter)

    response = client.post(
        "/operations/jobs/ingestion/live",
        json={"programmes": ["horizon", "erasmus+"], "limit": 10, "run_matching_after": False},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["source_name"] == "eu_funding_tenders"
    assert body["result_summary"]["created_count"] == 1
    assert len(body["sample_opportunities"]) >= 1


def test_live_ingestion_api_returns_provider_diagnostics_on_source_block(client, monkeypatch):
    from app.core.config import get_settings

    monkeypatch.setenv("EU_FUNDING_LIVE_ENABLED", "true")
    get_settings.cache_clear()
    adapter = EUFundingTendersAdapter()

    def _raise_block(**_kwargs):
        raise AdapterFetchError(
            code="source_unauthorized",
            message="EU Funding API returned HTTP 403",
            diagnostics={
                "category": "source_unauthorized",
                "status_code": 403,
                "method": "GET",
                "requested_url": "https://ec.europa.eu/info/funding-tenders/opportunities/data-api/topic/search?query=...",
                "final_url": "https://ec.europa.eu/info/funding-tenders/opportunities/data-api/topic/search?query=...",
            },
        )

    monkeypatch.setattr(adapter, "_fetch_live_payload", _raise_block)
    monkeypatch.setitem(DEFAULT_ADAPTERS, "eu_funding_tenders", adapter)

    response = client.post(
        "/operations/jobs/ingestion/live",
        json={"programmes": ["horizon"], "limit": 10, "run_matching_after": False},
    )

    assert response.status_code == 502
    detail = response.json()["detail"]
    assert detail["error_code"] == "source_unauthorized"
    assert detail["diagnostics"]["category"] == "source_unauthorized"
    assert detail["diagnostics"]["method"] == "GET"
    assert detail["diagnostics"]["requested_url"]
    assert detail["diagnostics"]["final_url"]


def test_live_ingestion_api_returns_source_unavailable_when_disabled(client, monkeypatch):
    from app.core.config import get_settings

    monkeypatch.delenv("EU_FUNDING_LIVE_ENABLED", raising=False)
    get_settings.cache_clear()

    response = client.post(
        "/operations/jobs/ingestion/live",
        json={"programmes": ["horizon"], "limit": 10, "run_matching_after": False},
    )

    assert response.status_code == 502
    detail = response.json()["detail"]
    assert detail["error_code"] == "source_unavailable"
    assert detail["diagnostics"]["category"] == "source_unavailable"
