from sqlalchemy.orm import Session

from app.domain.common.enums import OpportunityState, ProposalState
from app.domain.opportunity_discovery.models import Opportunity
from app.domain.proposal_factory.models import Proposal
from app.schemas.audit import AuditEventSchema
from app.schemas.proposal import ProposalWorkspaceCreateRequest
from app.services.audit_service import AuditService

_ALLOWED_TRANSITIONS: dict[ProposalState, set[ProposalState]] = {
    ProposalState.CREATED: {ProposalState.STRATEGY_PENDING, ProposalState.ARCHIVED},
    ProposalState.STRATEGY_PENDING: {ProposalState.CONCEPT_NOTE_READY, ProposalState.ARCHIVED},
    ProposalState.CONCEPT_NOTE_READY: {ProposalState.DRAFTING, ProposalState.ARCHIVED},
    ProposalState.DRAFTING: {ProposalState.IN_REVIEW, ProposalState.ARCHIVED},
    ProposalState.IN_REVIEW: {
        ProposalState.REVISION_PENDING,
        ProposalState.APPROVED_FOR_EXPORT,
        ProposalState.ARCHIVED,
    },
    ProposalState.REVISION_PENDING: {
        ProposalState.DRAFTING,
        ProposalState.IN_REVIEW,
        ProposalState.ARCHIVED,
    },
    ProposalState.APPROVED_FOR_EXPORT: {ProposalState.ARCHIVED},
    ProposalState.ARCHIVED: set(),
}


class InvalidProposalTransitionError(ValueError):
    pass


class ProposalService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.audit = AuditService(db)

    def create_workspace(self, request: ProposalWorkspaceCreateRequest) -> Proposal:
        opportunity = self.db.get(Opportunity, request.opportunity_id)
        if opportunity is None:
            raise ValueError("Opportunity not found")
        if opportunity.state != OpportunityState.APPROVED:
            raise ValueError("Opportunity must be approved before proposal workspace creation")

        proposal = Proposal(
            opportunity_id=request.opportunity_id,
            owner_id=request.owner_id,
            name=request.name,
            template_type=request.template_type,
            page_limit=request.page_limit,
            state=ProposalState.CREATED,
            mandatory_sections=request.mandatory_sections,
            compliance_rules=request.compliance_rules,
        )
        self.db.add(proposal)
        self.db.flush()

        self.audit.emit(
            AuditEventSchema(
                event_type="proposal_workspace_created",
                entity_type="proposal",
                entity_id=proposal.id,
                actor_type="user",
                actor_id=request.owner_id,
                payload={"opportunity_id": request.opportunity_id},
            )
        )
        self.db.flush()
        return proposal

    def transition_state(
        self,
        proposal: Proposal,
        target_state: ProposalState,
        *,
        actor_type: str,
        actor_id: str,
        reason: str | None = None,
    ) -> Proposal:
        if target_state not in _ALLOWED_TRANSITIONS[proposal.state]:
            raise InvalidProposalTransitionError(
                f"Cannot transition proposal from {proposal.state} to {target_state}"
            )

        previous_state = proposal.state
        proposal.state = target_state
        if target_state == ProposalState.APPROVED_FOR_EXPORT and actor_type != "user":
            raise InvalidProposalTransitionError(
                "Human approval is required for approved_for_export transition"
            )
        if target_state == ProposalState.APPROVED_FOR_EXPORT:
            proposal.human_approved_for_export = True

        self.db.add(proposal)
        self.audit.emit(
            AuditEventSchema(
                event_type="proposal_state_changed",
                entity_type="proposal",
                entity_id=proposal.id,
                actor_type=actor_type,
                actor_id=actor_id,
                payload={
                    "from_state": previous_state.value,
                    "to_state": target_state.value,
                    "reason": reason,
                },
            )
        )
        self.db.flush()
        return proposal
