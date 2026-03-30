from sqlalchemy.orm import Session

from app.domain.audit_and_observability.models import AuditEvent
from app.schemas.audit import AuditEventSchema


class AuditService:
    """Thin audit writer used by workflow services.

    A dedicated outbox/event bus can be introduced later without changing callers.
    """

    def __init__(self, db: Session) -> None:
        self.db = db

    def emit(self, event: AuditEventSchema) -> AuditEvent:
        model = AuditEvent(
            event_type=event.event_type,
            entity_type=event.entity_type,
            entity_id=event.entity_id,
            actor_type=event.actor_type,
            actor_id=event.actor_id,
            payload=event.payload,
        )
        self.db.add(model)
        self.db.flush()
        return model
