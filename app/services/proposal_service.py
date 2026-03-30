from sqlalchemy.orm import Session

from app.domain.common.enums import ProposalState
from app.domain.proposal_factory.models import Proposal
from app.schemas.audit import AuditEventSchema
from app.services.audit_service import AuditService

_ALLOWED_TRANSITIONS: dict[ProposalState, set[ProposalState]] = {
    ProposalState.INITIALIZED: {ProposalState.OUTLINED, ProposalState.FROZEN},
    ProposalState.OUTLINED: {ProposalState.DRAFTING, ProposalState.FROZEN},
    ProposalState.DRAFTING: {ProposalState.UNDER_REVIEW, ProposalState.FROZEN},
    ProposalState.UNDER_REVIEW: {
        ProposalState.REVISION_REQUIRED,
        ProposalState.APPROVED_FOR_PACKAGING,
        ProposalState.FROZEN,
    },
    ProposalState.REVISION_REQUIRED: {ProposalState.DRAFTING, ProposalState.FROZEN},
    ProposalState.APPROVED_FOR_PACKAGING: {ProposalState.PACKAGED, ProposalState.FROZEN},
    ProposalState.PACKAGED: {ProposalState.FROZEN},
    ProposalState.FROZEN: set(),
}


class InvalidProposalTransitionError(ValueError):
    pass


class ProposalService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.audit = AuditService(db)

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
