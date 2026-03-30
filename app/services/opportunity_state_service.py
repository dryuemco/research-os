from sqlalchemy.orm import Session

from app.domain.common.enums import OpportunityState
from app.domain.opportunity_discovery.models import Opportunity
from app.schemas.audit import AuditEventSchema
from app.services.audit_service import AuditService

_ALLOWED_TRANSITIONS: dict[OpportunityState, set[OpportunityState]] = {
    OpportunityState.DISCOVERED: {OpportunityState.NORMALIZED, OpportunityState.ARCHIVED},
    OpportunityState.NORMALIZED: {
        OpportunityState.SCORED,
        OpportunityState.SHORTLISTED,
        OpportunityState.REJECTED,
        OpportunityState.MONITOR_LATER,
        OpportunityState.IGNORED,
        OpportunityState.ARCHIVED,
    },
    OpportunityState.SCORED: {
        OpportunityState.SHORTLISTED,
        OpportunityState.REJECTED,
        OpportunityState.MONITOR_LATER,
        OpportunityState.IGNORED,
        OpportunityState.ARCHIVED,
    },
    OpportunityState.SHORTLISTED: {
        OpportunityState.APPROVED,
        OpportunityState.REJECTED,
        OpportunityState.MONITOR_LATER,
        OpportunityState.IGNORED,
    },
    OpportunityState.MONITOR_LATER: {
        OpportunityState.SHORTLISTED,
        OpportunityState.REJECTED,
        OpportunityState.IGNORED,
    },
    OpportunityState.REJECTED: set(),
    OpportunityState.IGNORED: set(),
    OpportunityState.APPROVED: {OpportunityState.ARCHIVED},
    OpportunityState.ARCHIVED: set(),
}


class InvalidOpportunityTransitionError(ValueError):
    pass


class OpportunityStateService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.audit = AuditService(db)

    def transition_state(
        self,
        opportunity: Opportunity,
        target_state: OpportunityState,
        *,
        actor_type: str,
        actor_id: str,
        reason: str | None = None,
    ) -> Opportunity:
        if target_state not in _ALLOWED_TRANSITIONS[opportunity.state]:
            raise InvalidOpportunityTransitionError(
                f"Cannot transition opportunity from {opportunity.state} to {target_state}"
            )

        previous_state = opportunity.state
        opportunity.state = target_state
        self.db.add(opportunity)
        self.audit.emit(
            AuditEventSchema(
                event_type="opportunity_state_changed",
                entity_type="opportunity",
                entity_id=opportunity.id,
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
        return opportunity

    def apply_decision(
        self,
        opportunity: Opportunity,
        action: str,
        *,
        actor_type: str,
        actor_id: str,
        reason: str | None = None,
    ) -> Opportunity:
        action_map = {
            "approve": OpportunityState.APPROVED,
            "reject": OpportunityState.REJECTED,
            "monitor": OpportunityState.MONITOR_LATER,
            "ignore": OpportunityState.IGNORED,
            "shortlist": OpportunityState.SHORTLISTED,
        }
        if action not in action_map:
            raise InvalidOpportunityTransitionError(f"Unknown action: {action}")
        return self.transition_state(
            opportunity,
            action_map[action],
            actor_type=actor_type,
            actor_id=actor_id,
            reason=reason,
        )
