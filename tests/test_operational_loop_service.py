from app.domain.common.enums import NotificationType, OperationalJobStatus, OperationalJobType
from app.domain.operations.models import Notification
from app.domain.opportunity_discovery.models import InterestProfile
from app.services.operational_loop_service import OperationalLoopService


def _seed_profile(db_session) -> InterestProfile:
    profile = InterestProfile(
        user_id="ops-admin",
        name="Ops Profile",
        parameters_json={
            "allowed_programs": ["horizon"],
            "preferred_keywords": ["ai", "climate"],
            "weights": {"keyword_overlap": 0.7, "budget_fit": 0.3},
        },
    )
    db_session.add(profile)
    db_session.commit()
    return profile


def test_ingestion_run_persists_summary_and_triggers_matching(db_session):
    profile = _seed_profile(db_session)
    service = OperationalLoopService(db_session)

    run = service.run_ingestion_job(
        source_name="funding_call_scaffold",
        trigger_source="test",
        run_matching_after=True,
        records=[
            {
                "source_record_id": "op-1",
                "payload": {
                    "external_id": "op-1",
                    "source_program": "horizon",
                    "title": "AI climate tool",
                    "summary": "AI and climate adaptation",
                    "full_text": "AI, climate, resilience",
                },
            }
        ],
    )
    db_session.commit()

    assert run.job_type == OperationalJobType.SOURCE_INGESTION
    assert run.status == OperationalJobStatus.SUCCEEDED
    assert run.result_summary["created_count"] == 1

    matching_runs = service.list_matching_runs()
    assert matching_runs
    assert matching_runs[0].profile_id == profile.id


def test_matching_run_creates_new_match_notifications(db_session):
    profile = _seed_profile(db_session)
    service = OperationalLoopService(db_session)
    service.run_ingestion_job(
        source_name="funding_call_scaffold",
        trigger_source="test",
        run_matching_after=False,
        records=[
            {
                "source_record_id": "op-2",
                "payload": {
                    "external_id": "op-2",
                    "source_program": "horizon",
                    "title": "AI climate impact",
                    "summary": "ai climate",
                    "full_text": "ai climate",
                },
            }
        ],
    )
    run = service.run_matching_job(
        profile_id=profile.id,
        scoring_policy_id="default-v1",
        trigger_source="test",
    )
    db_session.commit()

    assert run.status == OperationalJobStatus.SUCCEEDED
    notifications = db_session.query(Notification).all()
    assert any(n.notification_type == NotificationType.NEW_MATCH for n in notifications)


def test_scheduler_runs_due_jobs(db_session):
    _seed_profile(db_session)
    service = OperationalLoopService(db_session)
    service.ensure_default_jobs()
    runs = service.run_due_jobs()
    db_session.commit()

    assert runs
    assert any(
        r.status in {OperationalJobStatus.SUCCEEDED, OperationalJobStatus.FAILED}
        for r in runs
    )
