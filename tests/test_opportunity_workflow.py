from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import text

from app.domain.common.enums import OpportunityState
from app.domain.opportunity_discovery.models import InterestProfile, Opportunity
from app.schemas.matching import MatchRequest
from app.schemas.opportunity import OpportunityIngestRequest
from app.services.matching_service import MatchingService
from app.services.opportunity_ingestion_service import OpportunityIngestionService
from app.services.opportunity_state_service import (
    InvalidOpportunityTransitionError,
    OpportunityStateService,
)


def _seed_profile(db_session) -> InterestProfile:
    profile = InterestProfile(
        user_id="user-1",
        name="EU AI profile",
        parameters_json={
            "allowed_programs": ["Horizon Europe"],
            "required_keywords": ["ai"],
            "preferred_keywords": ["ai", "health"],
            "min_budget_total": 1000,
            "target_roles": ["coordinator"],
        },
    )
    db_session.add(profile)
    db_session.flush()
    return profile


def test_ingestion_creates_version_and_normalized_state(db_session) -> None:
    deadline = (datetime.now(UTC) + timedelta(days=30)).isoformat()
    service = OpportunityIngestionService(db_session)
    opportunity = service.ingest_dev_payload(
        OpportunityIngestRequest(
            source_name="funding_call_scaffold",
            source_record_id="src-1",
            payload={
                "source_program": "Horizon Europe",
                "external_id": "call-001",
                "source_url": "https://example.test/call-001",
                "title": "AI for health",
                "summary": "Looking for AI and health innovation",
                "full_text": "AI for health innovation and pilots",
                "deadline_at": deadline,
                "budget_total": 5000,
                "currency": "EUR",
            },
        )
    )
    db_session.commit()

    assert opportunity.state == OpportunityState.NORMALIZED
    versions = db_session.execute(text("SELECT count(*) FROM opportunity_versions")).scalar_one()
    snapshots = db_session.execute(
        text("SELECT count(*) FROM opportunity_ingestion_snapshots")
    ).scalar_one()
    assert versions == 1
    assert snapshots == 1


def test_matching_shortlists_high_score_opportunity(db_session) -> None:
    profile = _seed_profile(db_session)
    ingestion = OpportunityIngestionService(db_session)
    opportunity = ingestion.ingest_dev_payload(
        OpportunityIngestRequest(
            source_name="funding_call_scaffold",
            source_record_id="src-2",
            payload={
                "source_program": "Horizon Europe",
                "external_id": "call-002",
                "source_url": "https://example.test/call-002",
                "title": "AI health mission",
                "summary": "AI health consortium",
                "full_text": "AI and health impact",
                "budget_total": 20000,
                "currency": "EUR",
            },
        )
    )
    db_session.flush()

    service = MatchingService(db_session)
    results = service.run_match(
        MatchRequest(
            user_id="user-1",
            profile_id=profile.id,
            opportunity_ids=[opportunity.id],
            scoring_policy_id="default-v1",
        )
    )
    db_session.commit()

    assert len(results) == 1
    assert results[0].recommendation in {"pursue", "monitor"}
    assert opportunity.state in {OpportunityState.SCORED, OpportunityState.SHORTLISTED}


def test_approval_transition_emits_audit_event(db_session) -> None:
    opportunity = Opportunity(
        source_program="Horizon Europe",
        source_url="https://example.com",
        external_id="call-003",
        title="Example",
        summary="Summary",
        deadline_at=None,
        call_status="open",
        budget_total=10000,
        currency="EUR",
        state=OpportunityState.SHORTLISTED,
        current_version_hash="hash-1",
        raw_payload={},
    )
    db_session.add(opportunity)
    db_session.flush()

    service = OpportunityStateService(db_session)
    service.apply_decision(opportunity, "approve", actor_type="user", actor_id="user-1")
    db_session.commit()

    assert opportunity.state == OpportunityState.APPROVED
    events = db_session.execute(
        text("SELECT event_type FROM audit_events WHERE entity_id = :entity_id"),
        {"entity_id": opportunity.id},
    ).fetchall()
    assert events[-1][0] == "opportunity_state_changed"


def test_invalid_approval_transition_rejected(db_session) -> None:
    opportunity = Opportunity(
        source_program="Horizon Europe",
        source_url="https://example.com",
        external_id="call-004",
        title="Example",
        summary="Summary",
        deadline_at=None,
        call_status="open",
        budget_total=10000,
        currency="EUR",
        state=OpportunityState.REJECTED,
        current_version_hash="hash-1",
        raw_payload={},
    )
    db_session.add(opportunity)
    db_session.flush()

    service = OpportunityStateService(db_session)
    with pytest.raises(InvalidOpportunityTransitionError):
        service.apply_decision(opportunity, "approve", actor_type="user", actor_id="user-1")
