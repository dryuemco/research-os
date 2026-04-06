"""execution runtime foundation

Revision ID: 0005_execution_runtime_foundation
Revises: 0004_decomposition_and_handoff_foundation
Create Date: 2026-04-02 00:00:00
"""

from alembic import op
import sqlalchemy as sa


revision = "0005_execution_runtime_foundation"
down_revision = "0004_decomposition_and_handoff_foundation"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "execution_runs",
        sa.Column("execution_plan_id", sa.String(), nullable=True),
        sa.Column("coding_work_unit_id", sa.String(), nullable=True),
        sa.Column("task_type", sa.String(length=64), nullable=False),
        sa.Column("purpose", sa.String(length=255), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("routing_policy_version", sa.String(length=64), nullable=True),
        sa.Column("selected_provider", sa.String(length=64), nullable=True),
        sa.Column("selected_model", sa.String(length=128), nullable=True),
        sa.Column("fallback_chain", sa.JSON(), nullable=False),
        sa.Column("approved_providers", sa.JSON(), nullable=False),
        sa.Column("local_only", sa.Boolean(), nullable=False),
        sa.Column("sensitive_data", sa.Boolean(), nullable=False),
        sa.Column("requires_human_approval", sa.Boolean(), nullable=False),
        sa.Column("budget_tier", sa.String(length=32), nullable=False),
        sa.Column("max_attempts", sa.Integer(), nullable=False),
        sa.Column("timeout_seconds", sa.Integer(), nullable=False),
        sa.Column("attempt_count", sa.Integer(), nullable=False),
        sa.Column("next_retry_at", sa.String(length=64), nullable=True),
        sa.Column("pause_reason", sa.String(length=64), nullable=True),
        sa.Column("failure_reason", sa.String(length=255), nullable=True),
        sa.Column("last_error_type", sa.String(length=32), nullable=True),
        sa.Column("input_payload", sa.JSON(), nullable=False),
        sa.Column("result_payload", sa.JSON(), nullable=True),
        sa.Column("checkpoint_payload", sa.JSON(), nullable=False),
        sa.Column("last_successful_step", sa.String(length=128), nullable=True),
        sa.Column("retry_lineage_run_id", sa.String(), nullable=True),
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["coding_work_unit_id"], ["coding_work_units.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["execution_plan_id"], ["execution_plans.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["retry_lineage_run_id"], ["execution_runs.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_execution_runs_execution_plan_id"), "execution_runs", ["execution_plan_id"], unique=False)
    op.create_index(op.f("ix_execution_runs_coding_work_unit_id"), "execution_runs", ["coding_work_unit_id"], unique=False)
    op.create_index(op.f("ix_execution_runs_status"), "execution_runs", ["status"], unique=False)
    op.create_index(op.f("ix_execution_runs_task_type"), "execution_runs", ["task_type"], unique=False)

    op.create_table(
        "execution_jobs",
        sa.Column("run_id", sa.String(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("idempotency_key", sa.String(length=255), nullable=False),
        sa.Column("attempts", sa.Integer(), nullable=False),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["run_id"], ["execution_runs.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_execution_jobs_run_id"), "execution_jobs", ["run_id"], unique=False)
    op.create_index(op.f("ix_execution_jobs_status"), "execution_jobs", ["status"], unique=False)
    op.create_index(op.f("ix_execution_jobs_idempotency_key"), "execution_jobs", ["idempotency_key"], unique=True)

    op.create_table(
        "provider_execution_traces",
        sa.Column("run_id", sa.String(), nullable=False),
        sa.Column("attempt_number", sa.Integer(), nullable=False),
        sa.Column("provider_name", sa.String(length=64), nullable=False),
        sa.Column("model_name", sa.String(length=128), nullable=False),
        sa.Column("task_type", sa.String(length=64), nullable=False),
        sa.Column("purpose", sa.String(length=255), nullable=False),
        sa.Column("routing_policy_version", sa.String(length=64), nullable=True),
        sa.Column("request_fingerprint", sa.String(length=128), nullable=False),
        sa.Column("request_metadata", sa.JSON(), nullable=False),
        sa.Column("latency_ms", sa.Integer(), nullable=True),
        sa.Column("usage_metadata", sa.JSON(), nullable=False),
        sa.Column("cost_estimate", sa.Numeric(12, 6), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("error_type", sa.String(length=32), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("fallback_from_trace_id", sa.String(), nullable=True),
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["fallback_from_trace_id"], ["provider_execution_traces.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["run_id"], ["execution_runs.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_provider_execution_traces_run_id"), "provider_execution_traces", ["run_id"], unique=False)
    op.create_index(op.f("ix_provider_execution_traces_provider_name"), "provider_execution_traces", ["provider_name"], unique=False)
    op.create_index(op.f("ix_provider_execution_traces_model_name"), "provider_execution_traces", ["model_name"], unique=False)
    op.create_index(op.f("ix_provider_execution_traces_task_type"), "provider_execution_traces", ["task_type"], unique=False)
    op.create_index(op.f("ix_provider_execution_traces_status"), "provider_execution_traces", ["status"], unique=False)
    op.create_index(op.f("ix_provider_execution_traces_request_fingerprint"), "provider_execution_traces", ["request_fingerprint"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_provider_execution_traces_request_fingerprint"), table_name="provider_execution_traces")
    op.drop_index(op.f("ix_provider_execution_traces_status"), table_name="provider_execution_traces")
    op.drop_index(op.f("ix_provider_execution_traces_task_type"), table_name="provider_execution_traces")
    op.drop_index(op.f("ix_provider_execution_traces_model_name"), table_name="provider_execution_traces")
    op.drop_index(op.f("ix_provider_execution_traces_provider_name"), table_name="provider_execution_traces")
    op.drop_index(op.f("ix_provider_execution_traces_run_id"), table_name="provider_execution_traces")
    op.drop_table("provider_execution_traces")

    op.drop_index(op.f("ix_execution_jobs_idempotency_key"), table_name="execution_jobs")
    op.drop_index(op.f("ix_execution_jobs_status"), table_name="execution_jobs")
    op.drop_index(op.f("ix_execution_jobs_run_id"), table_name="execution_jobs")
    op.drop_table("execution_jobs")

    op.drop_index(op.f("ix_execution_runs_task_type"), table_name="execution_runs")
    op.drop_index(op.f("ix_execution_runs_status"), table_name="execution_runs")
    op.drop_index(op.f("ix_execution_runs_coding_work_unit_id"), table_name="execution_runs")
    op.drop_index(op.f("ix_execution_runs_execution_plan_id"), table_name="execution_runs")
    op.drop_table("execution_runs")
