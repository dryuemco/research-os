from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import JSON

from app.db.base import Base
from app.domain.common.enums import (
    NotificationStatus,
    NotificationType,
    OperationalJobStatus,
    OperationalJobType,
)
from app.domain.common.mixins import TimestampMixin, UUIDPrimaryKeyMixin

JSONType = JSON().with_variant(JSONB, "postgresql")


class OperationalJobConfig(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "operational_job_configs"

    job_key: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    job_type: Mapped[OperationalJobType] = mapped_column(Enum(OperationalJobType), index=True)
    source_name: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    profile_id: Mapped[str | None] = mapped_column(
        ForeignKey("interest_profiles.id", ondelete="SET NULL"), nullable=True, index=True
    )
    interval_minutes: Mapped[int] = mapped_column(Integer, default=60)
    enabled: Mapped[bool] = mapped_column(default=True, index=True)
    trigger_policy: Mapped[dict] = mapped_column(JSONType, default=dict)
    last_triggered_at: Mapped[DateTime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    next_run_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class OperationalJobRun(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "operational_job_runs"

    job_config_id: Mapped[str | None] = mapped_column(
        ForeignKey("operational_job_configs.id", ondelete="SET NULL"), nullable=True, index=True
    )
    job_type: Mapped[OperationalJobType] = mapped_column(Enum(OperationalJobType), index=True)
    status: Mapped[OperationalJobStatus] = mapped_column(
        Enum(OperationalJobStatus), default=OperationalJobStatus.QUEUED, index=True
    )
    trigger_source: Mapped[str] = mapped_column(String(64), default="manual")
    source_name: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    profile_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    started_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    result_summary: Mapped[dict] = mapped_column(JSONType, default=dict)
    error_summary: Mapped[dict] = mapped_column(JSONType, default=dict)


class MatchingRun(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "matching_runs"

    operational_job_run_id: Mapped[str | None] = mapped_column(
        ForeignKey("operational_job_runs.id", ondelete="SET NULL"), nullable=True, index=True
    )
    profile_id: Mapped[str] = mapped_column(ForeignKey("interest_profiles.id", ondelete="CASCADE"))
    scoring_policy_id: Mapped[str] = mapped_column(String(128))
    status: Mapped[OperationalJobStatus] = mapped_column(
        Enum(OperationalJobStatus), default=OperationalJobStatus.QUEUED, index=True
    )
    opportunities_scanned: Mapped[int] = mapped_column(Integer, default=0)
    matches_created: Mapped[int] = mapped_column(Integer, default=0)
    recommendations_count: Mapped[int] = mapped_column(Integer, default=0)
    red_flags_count: Mapped[int] = mapped_column(Integer, default=0)
    summary_json: Mapped[dict] = mapped_column(JSONType, default=dict)


class Notification(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "notifications"

    notification_type: Mapped[NotificationType] = mapped_column(Enum(NotificationType), index=True)
    status: Mapped[NotificationStatus] = mapped_column(
        Enum(NotificationStatus), default=NotificationStatus.PENDING, index=True
    )
    recipient_user_id: Mapped[str] = mapped_column(String(255), index=True)
    related_entity_type: Mapped[str | None] = mapped_column(String(64), nullable=True)
    related_entity_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    payload_json: Mapped[dict] = mapped_column(JSONType, default=dict)
    sent_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    read_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), nullable=True)
