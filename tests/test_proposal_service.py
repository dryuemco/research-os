import pytest
from sqlalchemy import text

from app.domain.common.enums import OpportunityState, ProposalState
from app.domain.opportunity_discovery.models import Opportunity
from app.schemas.proposal import ProposalWorkspaceCreateRequest
from app.services.proposal_service import InvalidProposalTransitionError, ProposalService


def _create_opportunity(db_session, *, state: OpportunityState = OpportunityState.APPROVED):
    opportunity = Opportunity(
        source_program="Horizon Europe",
        source_url="https://example.com/call",
        external_id=f"opp-{state.value}",
        title="Example Call",
        summary="Summary",
        deadline_at=None,
        call_status="open",
        budget_total=None,
        currency=None,
        state=state,
        current_version_hash="hash-1",
        raw_payload={},
    )
    db_session.add(opportunity)
    db_session.flush()
    return opportunity


def test_workspace_creation_requires_approved_opportunity(db_session) -> None:
    opportunity = _create_opportunity(db_session, state=OpportunityState.SHORTLISTED)
    service = ProposalService(db_session)

    with pytest.raises(ValueError):
        service.create_workspace(
            ProposalWorkspaceCreateRequest(
                opportunity_id=opportunity.id,
                owner_id="user-1",
                name="Workspace",
                template_type="horizon-ria",
            )
        )


def test_valid_proposal_transition_emits_audit_event(db_session) -> None:
    opportunity = _create_opportunity(db_session)
    service = ProposalService(db_session)
    proposal = service.create_workspace(
        ProposalWorkspaceCreateRequest(
            opportunity_id=opportunity.id,
            owner_id="user-1",
            name="Workspace",
            template_type="horizon-ria",
        )
    )

    service.transition_state(
        proposal,
        ProposalState.STRATEGY_PENDING,
        actor_type="user",
        actor_id="user-1",
        reason="strategy intake",
    )
    db_session.commit()

    assert proposal.state == ProposalState.STRATEGY_PENDING
    events = db_session.execute(text("SELECT event_type FROM audit_events")).fetchall()
    event_types = {row[0] for row in events}
    assert event_types == {"proposal_workspace_created", "proposal_state_changed"}


def test_invalid_proposal_transition_is_rejected(db_session) -> None:
    opportunity = _create_opportunity(db_session)
    service = ProposalService(db_session)
    proposal = service.create_workspace(
        ProposalWorkspaceCreateRequest(
            opportunity_id=opportunity.id,
            owner_id="user-1",
            name="Workspace",
            template_type="horizon-ria",
        )
    )

    with pytest.raises(InvalidProposalTransitionError):
        service.transition_state(
            proposal,
            ProposalState.APPROVED_FOR_EXPORT,
            actor_type="user",
            actor_id="user-1",
        )
