from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.common.enums import ActorType, TargetCallStatus
from app.domain.opportunity_discovery.models import TargetCall
from app.schemas.audit import AuditEventSchema
from app.schemas.target_call import TargetCallCreateRequest, TargetCallUpdateRequest
from app.services.audit_service import AuditService


class TargetCallService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.audit = AuditService(db)

    def create(self, request: TargetCallCreateRequest, *, actor_user_id: str) -> TargetCall:
        item = TargetCall(
            title=request.title,
            programme=request.programme,
            call_url=request.call_url,
            call_identifier=request.call_identifier,
            deadline_at=request.deadline_at,
            raw_call_text=request.raw_call_text,
            summary=request.summary,
            status=request.status,
            created_by_user_id=actor_user_id,
        )
        self.db.add(item)
        self.db.flush()
        self.audit.emit(
            AuditEventSchema(
                event_type="target_call_created",
                entity_type="target_call",
                entity_id=item.id,
                actor_type=ActorType.USER.value,
                actor_id=actor_user_id,
                payload={"status": item.status.value, "programme": item.programme},
            )
        )
        self.db.flush()
        return item

    def list_all(self) -> list[TargetCall]:
        return self.db.scalars(select(TargetCall).order_by(TargetCall.created_at.desc())).all()

    def get_or_raise(self, target_call_id: str) -> TargetCall:
        item = self.db.get(TargetCall, target_call_id)
        if item is None:
            raise ValueError("Target call not found")
        return item

    def update(
        self,
        target_call_id: str,
        request: TargetCallUpdateRequest,
        *,
        actor_user_id: str,
    ) -> TargetCall:
        item = self.get_or_raise(target_call_id)
        for field_name in request.model_fields_set:
            setattr(item, field_name, getattr(request, field_name))
        if not item.call_url and not item.raw_call_text:
            raise ValueError("Either call_url or raw_call_text must be provided")
        self.db.flush()
        self.audit.emit(
            AuditEventSchema(
                event_type="target_call_updated",
                entity_type="target_call",
                entity_id=item.id,
                actor_type=ActorType.USER.value,
                actor_id=actor_user_id,
                payload={"updated_fields": sorted(request.model_fields_set)},
            )
        )
        self.db.flush()
        return item

    def archive(self, target_call_id: str, *, actor_user_id: str) -> TargetCall:
        item = self.get_or_raise(target_call_id)
        item.status = TargetCallStatus.ARCHIVED
        self.db.flush()
        self.audit.emit(
            AuditEventSchema(
                event_type="target_call_archived",
                entity_type="target_call",
                entity_id=item.id,
                actor_type=ActorType.USER.value,
                actor_id=actor_user_id,
                payload={"status": item.status.value},
            )
        )
        self.db.flush()
        return item
