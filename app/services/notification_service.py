from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.common.enums import NotificationStatus, NotificationType
from app.domain.operations.models import Notification
from app.schemas.audit import AuditEventSchema
from app.services.audit_service import AuditService


class NotificationService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.audit = AuditService(db)

    def create(
        self,
        *,
        notification_type: NotificationType,
        recipient_user_id: str,
        payload_json: dict,
        related_entity_type: str | None = None,
        related_entity_id: str | None = None,
    ) -> Notification:
        item = Notification(
            notification_type=notification_type,
            status=NotificationStatus.PENDING,
            recipient_user_id=recipient_user_id,
            related_entity_type=related_entity_type,
            related_entity_id=related_entity_id,
            payload_json=payload_json,
        )
        self.db.add(item)
        self.db.flush()
        self.dispatch(item)
        return item

    def dispatch(self, notification: Notification) -> Notification:
        notification.status = NotificationStatus.SENT
        notification.sent_at = datetime.now(UTC)
        self.db.add(notification)
        self.audit.emit(
            AuditEventSchema(
                event_type="notification_sent",
                entity_type="notification",
                entity_id=notification.id,
                actor_type="system",
                actor_id="notification_service",
                payload={
                    "notification_type": notification.notification_type.value,
                    "recipient_user_id": notification.recipient_user_id,
                },
            )
        )
        self.db.flush()
        return notification

    def list_for_user(self, user_id: str) -> list[Notification]:
        return self.db.scalars(
            select(Notification)
            .where(Notification.recipient_user_id == user_id)
            .order_by(Notification.created_at.desc())
        ).all()

    def mark_read(self, notification_id: str, user_id: str) -> Notification:
        item = self.db.get(Notification, notification_id)
        if item is None or item.recipient_user_id != user_id:
            raise ValueError("Notification not found")
        item.status = NotificationStatus.READ
        item.read_at = datetime.now(UTC)
        self.db.add(item)
        self.audit.emit(
            AuditEventSchema(
                event_type="notification_read",
                entity_type="notification",
                entity_id=item.id,
                actor_type="user",
                actor_id=user_id,
                payload={},
            )
        )
        self.db.flush()
        return item
