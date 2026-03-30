from app.domain.common.enums import OpportunityState
from app.domain.opportunity_discovery.models import InterestProfile


def test_opportunity_and_matching_api_smoke(client, db_session) -> None:
    profile = InterestProfile(
        user_id="user-1",
        name="Profile",
        parameters_json={
            "allowed_programs": ["Horizon Europe"],
            "required_keywords": ["ai"],
            "preferred_keywords": ["ai"],
            "min_budget_total": 1000,
        },
    )
    db_session.add(profile)
    db_session.flush()

    ingest_resp = client.post(
        "/opportunities/ingest/dev",
        json={
            "source_name": "funding_call_scaffold",
            "source_record_id": "source-api-1",
            "payload": {
                "source_program": "Horizon Europe",
                "external_id": "api-call-1",
                "source_url": "https://example.test/api-call-1",
                "title": "AI call",
                "summary": "ai opportunities",
                "full_text": "ai opportunities for health",
                "budget_total": 5000,
                "currency": "EUR",
            },
        },
    )
    assert ingest_resp.status_code == 200
    opportunity_id = ingest_resp.json()["id"]

    list_resp = client.get("/opportunities")
    assert list_resp.status_code == 200
    assert len(list_resp.json()) >= 1

    get_resp = client.get(f"/opportunities/{opportunity_id}")
    assert get_resp.status_code == 200

    run_match_resp = client.post(
        "/matches/run",
        json={
            "user_id": "user-1",
            "profile_id": profile.id,
            "opportunity_ids": [opportunity_id],
            "scoring_policy_id": "default-v1",
        },
    )
    assert run_match_resp.status_code == 200
    assert len(run_match_resp.json()) == 1

    decision_resp = client.post(
        f"/opportunities/{opportunity_id}/decision",
        json={"action": "monitor", "actor_id": "user-1", "actor_type": "user"},
    )
    assert decision_resp.status_code == 200
    assert decision_resp.json()["state"] in {
        OpportunityState.MONITOR_LATER.value,
        OpportunityState.SHORTLISTED.value,
        OpportunityState.SCORED.value,
    }
