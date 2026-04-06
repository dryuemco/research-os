from app.domain.opportunity_discovery.models import InterestProfile
from app.services.operational_loop_service import OperationalLoopService


def test_dashboard_operations_visibility(client, db_session):
    profile = InterestProfile(
        user_id="ops-admin",
        name="Ops Dashboard Profile",
        parameters_json={"allowed_programs": ["horizon"], "preferred_keywords": ["ai"]},
    )
    db_session.add(profile)
    db_session.commit()

    OperationalLoopService(db_session).run_ingestion_job(
        source_name="funding_call_scaffold",
        trigger_source="dashboard-test",
        run_matching_after=True,
        records=[
            {
                "source_record_id": "dash-op-1",
                "payload": {
                    "external_id": "dash-op-1",
                    "source_program": "horizon",
                    "title": "AI dashboard opportunity",
                    "summary": "AI",
                    "full_text": "AI",
                },
            }
        ],
    )
    db_session.commit()

    jobs = client.get("/dashboard/operations/jobs")
    assert jobs.status_code == 200
    assert jobs.json()["items"]

    matching = client.get("/dashboard/operations/matching-runs")
    assert matching.status_code == 200
    assert matching.json()["items"]

    notifications = client.get(
        "/dashboard/operations/notifications",
        params={"user_id": "ops-admin"},
    )
    assert notifications.status_code == 200
    assert notifications.json()["items"]
