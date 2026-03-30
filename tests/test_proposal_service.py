import pytest
from sqlalchemy import text

from app.domain.common.enums import OpportunityState, ProposalState
from app.domain.opportunity_discovery.models import Opportunity
from app.domain.proposal_factory.models import Proposal
from app.services.proposal_service import InvalidProposalTransitionError, ProposalService


def _create_opportunity(db_session):
    opportunity = Opportunity(
        source_program="Horizon Europe",
        source_url="https://example.com/call",
        external_id="opp-1",
        title="Example Call",
        summary="Summary",
        deadline_at=None,
        call_status="open",
        budget_total=None,
        currency=None,
        state=OpportunityState.DISCOVERED,
        current_version_hash="hash-1",
        raw_payload={},
    )
    db_session.add(opportunity)
    db_session.flush()
    return opportunity


def test_valid_proposal_transition_emits_audit_event(db_session) -> None:
    opportunity = _create_opportunity(db_session)
    proposal = Proposal(
        opportunity_id=opportunity.id,
        owner_id="user-1",
        template_type="horizon-ria",
        state=ProposalState.INITIALIZED,
        mandatory_sections=["excellence"],
        compliance_rules=[],
    )
    db_session.add(proposal)
    db_session.flush()

    service = ProposalService(db_session)
    service.transition_state(
        proposal,
        ProposalState.OUTLINED,
        actor_type="user",
        actor_id="user-1",
        reason="outline generated",
    )
    db_session.commit()

    assert proposal.state == ProposalState.OUTLINED
    events = db_session.execute(text("SELECT event_type FROM audit_events")).fetchall()
    assert len(events) == 1
    assert events[0][0] == "proposal_state_changed"


def test_invalid_proposal_transition_is_rejected(db_session) -> None:
    opportunity = _create_opportunity(db_session)
    proposal = Proposal(
        opportunity_id=opportunity.id,
        owner_id="user-1",
        template_type="horizon-ria",
        state=ProposalState.INITIALIZED,
        mandatory_sections=["excellence"],
        compliance_rules=[],
    )
    db_session.add(proposal)
    db_session.flush()

    service = ProposalService(db_session)

    with pytest.raises(InvalidProposalTransitionError):
        service.transition_state(
            proposal,
            ProposalState.PACKAGED,
            actor_type="user",
            actor_id="user-1",
        )
