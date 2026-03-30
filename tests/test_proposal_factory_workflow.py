from pathlib import Path

from app.domain.common.enums import OpportunityState, ProposalState
from app.domain.opportunity_discovery.models import Opportunity
from app.schemas.proposal import (
    ConceptNoteInputContext,
    ProposalWorkspaceCreateRequest,
    ReviewerFeedback,
    ReviewRoundCreateRequest,
    SectionDraftRequest,
)
from app.services.prompt_registry_service import PromptRegistryService
from app.services.proposal_factory_service import ProposalFactoryService
from app.services.proposal_service import ProposalService


def _approved_opportunity(db_session) -> Opportunity:
    opp = Opportunity(
        source_program="Horizon Europe",
        source_url="https://example.com",
        external_id="opp-proposal-factory",
        title="Example Call",
        summary="Summary",
        deadline_at=None,
        call_status="open",
        budget_total=10000,
        currency="EUR",
        state=OpportunityState.APPROVED,
        current_version_hash="hash-1",
        raw_payload={},
    )
    db_session.add(opp)
    db_session.flush()
    return opp


def test_proposal_factory_flow_and_convergence(db_session) -> None:
    opp = _approved_opportunity(db_session)
    workspace = ProposalService(db_session).create_workspace(
        ProposalWorkspaceCreateRequest(
            opportunity_id=opp.id,
            owner_id="user-1",
            name="PF Workspace",
            template_type="generic",
        )
    )

    factory = ProposalFactoryService(db_session, PromptRegistryService(Path("prompts")))
    version = factory.create_concept_note(
        ConceptNoteInputContext(
            proposal_id=workspace.id,
            problem_statement="Need climate resilience",
            objectives=["Build resilient systems"],
        )
    )
    assert version.version_number == 1

    section = factory.create_section_draft(
        SectionDraftRequest(
            proposal_id=workspace.id,
            section_key="impact",
            writer_policy_id="writer-default",
        )
    )
    assert section.status == "stubbed"

    round_model = factory.create_review_round(
        ReviewRoundCreateRequest(
            proposal_id=workspace.id,
            reviewer_roles=["scientific", "red_team"],
        )
    )
    factory.add_reviewer_feedback(
        ReviewerFeedback(
            review_round_id=round_model.id,
            reviewer_role="scientific",
            severity="major",
            blocker=False,
            comment_text="Looks acceptable",
            scores={"compliance": 0.9, "overall": 0.9},
        )
    )

    result = factory.evaluate_convergence(
        workspace.id,
        max_rounds=3,
        blocker_threshold=1,
        compliance_threshold=0.7,
        reviewer_agreement_threshold=0.6,
        minimal_improvement_threshold=0.0,
    )
    assert result.should_stop is True
    assert workspace.state == ProposalState.APPROVED_FOR_EXPORT
