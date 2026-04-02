from sqlalchemy import Boolean, Enum, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import JSON

from app.db.base import Base
from app.domain.common.enums import (
    ExecutionJobStatus,
    ExecutionRunStatus,
    ProviderErrorType,
    ProviderTraceStatus,
)
from app.domain.common.mixins import TimestampMixin, UUIDPrimaryKeyMixin

JSONType = JSON().with_variant(JSONB, "postgresql")


class ExecutionRun(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "execution_runs"

    execution_plan_id: Mapped[str | None] = mapped_column(
        ForeignKey("execution_plans.id", ondelete="SET NULL"), nullable=True, index=True
    )
    coding_work_unit_id: Mapped[str | None] = mapped_column(
        ForeignKey("coding_work_units.id", ondelete="SET NULL"), nullable=True, index=True
    )
    task_type: Mapped[str] = mapped_column(String(64), index=True)
    purpose: Mapped[str] = mapped_column(String(255))
    status: Mapped[ExecutionRunStatus] = mapped_column(
        Enum(ExecutionRunStatus), default=ExecutionRunStatus.QUEUED, index=True
    )
    routing_policy_version: Mapped[str | None] = mapped_column(String(64), nullable=True)
    selected_provider: Mapped[str | None] = mapped_column(String(64), nullable=True)
    selected_model: Mapped[str | None] = mapped_column(String(128), nullable=True)
    fallback_chain: Mapped[list[str]] = mapped_column(JSONType, default=list)
    approved_providers: Mapped[list[str]] = mapped_column(JSONType, default=list)
    local_only: Mapped[bool] = mapped_column(Boolean, default=False)
    sensitive_data: Mapped[bool] = mapped_column(Boolean, default=False)
    requires_human_approval: Mapped[bool] = mapped_column(Boolean, default=False)
    budget_tier: Mapped[str] = mapped_column(String(32), default="standard")
    max_attempts: Mapped[int] = mapped_column(Integer, default=3)
    timeout_seconds: Mapped[int] = mapped_column(Integer, default=60)
    attempt_count: Mapped[int] = mapped_column(Integer, default=0)
    next_retry_at: Mapped[str | None] = mapped_column(String(64), nullable=True)
    pause_reason: Mapped[str | None] = mapped_column(String(64), nullable=True)
    failure_reason: Mapped[str | None] = mapped_column(String(255), nullable=True)
    last_error_type: Mapped[ProviderErrorType | None] = mapped_column(
        Enum(ProviderErrorType), nullable=True
    )
    input_payload: Mapped[dict] = mapped_column(JSONType, default=dict)
    result_payload: Mapped[dict | None] = mapped_column(JSONType, nullable=True)
    checkpoint_payload: Mapped[dict] = mapped_column(JSONType, default=dict)
    last_successful_step: Mapped[str | None] = mapped_column(String(128), nullable=True)
    retry_lineage_run_id: Mapped[str | None] = mapped_column(
        ForeignKey("execution_runs.id", ondelete="SET NULL"), nullable=True
    )


class ExecutionJob(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "execution_jobs"

    run_id: Mapped[str] = mapped_column(
        ForeignKey("execution_runs.id", ondelete="CASCADE"), index=True
    )
    status: Mapped[ExecutionJobStatus] = mapped_column(
        Enum(ExecutionJobStatus), default=ExecutionJobStatus.QUEUED, index=True
    )
    idempotency_key: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)


class ProviderExecutionTrace(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "provider_execution_traces"

    run_id: Mapped[str] = mapped_column(
        ForeignKey("execution_runs.id", ondelete="CASCADE"), index=True
    )
    attempt_number: Mapped[int] = mapped_column(Integer)
    provider_name: Mapped[str] = mapped_column(String(64), index=True)
    model_name: Mapped[str] = mapped_column(String(128), index=True)
    task_type: Mapped[str] = mapped_column(String(64), index=True)
    purpose: Mapped[str] = mapped_column(String(255))
    routing_policy_version: Mapped[str | None] = mapped_column(String(64), nullable=True)
    request_fingerprint: Mapped[str] = mapped_column(String(128), index=True)
    request_metadata: Mapped[dict] = mapped_column(JSONType, default=dict)
    latency_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    usage_metadata: Mapped[dict] = mapped_column(JSONType, default=dict)
    cost_estimate: Mapped[float | None] = mapped_column(Numeric(12, 6), nullable=True)
    status: Mapped[ProviderTraceStatus] = mapped_column(Enum(ProviderTraceStatus), index=True)
    error_type: Mapped[ProviderErrorType | None] = mapped_column(
        Enum(ProviderErrorType), nullable=True
    )
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    fallback_from_trace_id: Mapped[str | None] = mapped_column(
        ForeignKey("provider_execution_traces.id", ondelete="SET NULL"), nullable=True
    )
