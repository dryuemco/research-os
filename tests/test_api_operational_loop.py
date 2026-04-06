from app.domain.opportunity_discovery.models import InterestProfile


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
