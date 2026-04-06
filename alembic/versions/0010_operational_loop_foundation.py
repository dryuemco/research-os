"""operational loop foundation jobs matching runs notifications

Revision ID: 0010_operational_loop_foundation
Revises: 0009_export_delivery_hardening
Create Date: 2026-04-02 22:00:00
"""

from alembic import op
import sqlalchemy as sa


revision = "0010_operational_loop_foundation"
down_revision = "0009_export_delivery_hardening"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "operational_job_configs",
        sa.Column("job_key", sa.String(length=128), nullable=False),
        sa.Column("job_type", sa.String(length=64), nullable=False),
        sa.Column("source_name", sa.String(length=128), nullable=True),
        sa.Column("profile_id", sa.String(), nullable=True),
        sa.Column("interval_minutes", sa.Integer(), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False),
        sa.Column("trigger_policy", sa.JSON(), nullable=False),
        sa.Column("last_triggered_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("next_run_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["profile_id"], ["interest_profiles.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_operational_job_configs_job_key"), "operational_job_configs", ["job_key"], unique=True)
    op.create_index(op.f("ix_operational_job_configs_job_type"), "operational_job_configs", ["job_type"], unique=False)
    op.create_index(op.f("ix_operational_job_configs_source_name"), "operational_job_configs", ["source_name"], unique=False)
    op.create_index(op.f("ix_operational_job_configs_profile_id"), "operational_job_configs", ["profile_id"], unique=False)
    op.create_index(op.f("ix_operational_job_configs_enabled"), "operational_job_configs", ["enabled"], unique=False)

    op.create_table(
        "operational_job_runs",
        sa.Column("job_config_id", sa.String(), nullable=True),
        sa.Column("job_type", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=64), nullable=False),
        sa.Column("trigger_source", sa.String(length=64), nullable=False),
        sa.Column("source_name", sa.String(length=128), nullable=True),
        sa.Column("profile_id", sa.String(length=64), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("result_summary", sa.JSON(), nullable=False),
        sa.Column("error_summary", sa.JSON(), nullable=False),
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["job_config_id"], ["operational_job_configs.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_operational_job_runs_job_config_id"), "operational_job_runs", ["job_config_id"], unique=False)
    op.create_index(op.f("ix_operational_job_runs_job_type"), "operational_job_runs", ["job_type"], unique=False)
    op.create_index(op.f("ix_operational_job_runs_status"), "operational_job_runs", ["status"], unique=False)
    op.create_index(op.f("ix_operational_job_runs_source_name"), "operational_job_runs", ["source_name"], unique=False)
    op.create_index(op.f("ix_operational_job_runs_profile_id"), "operational_job_runs", ["profile_id"], unique=False)

    op.create_table(
        "matching_runs",
        sa.Column("operational_job_run_id", sa.String(), nullable=True),
        sa.Column("profile_id", sa.String(), nullable=False),
        sa.Column("scoring_policy_id", sa.String(length=128), nullable=False),
        sa.Column("status", sa.String(length=64), nullable=False),
        sa.Column("opportunities_scanned", sa.Integer(), nullable=False),
        sa.Column("matches_created", sa.Integer(), nullable=False),
        sa.Column("recommendations_count", sa.Integer(), nullable=False),
        sa.Column("red_flags_count", sa.Integer(), nullable=False),
        sa.Column("summary_json", sa.JSON(), nullable=False),
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["operational_job_run_id"], ["operational_job_runs.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["profile_id"], ["interest_profiles.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_matching_runs_operational_job_run_id"), "matching_runs", ["operational_job_run_id"], unique=False)
    op.create_index(op.f("ix_matching_runs_status"), "matching_runs", ["status"], unique=False)

    op.create_table(
        "notifications",
        sa.Column("notification_type", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=64), nullable=False),
        sa.Column("recipient_user_id", sa.String(length=255), nullable=False),
        sa.Column("related_entity_type", sa.String(length=64), nullable=True),
        sa.Column("related_entity_id", sa.String(length=64), nullable=True),
        sa.Column("payload_json", sa.JSON(), nullable=False),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("read_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_notifications_notification_type"), "notifications", ["notification_type"], unique=False)
    op.create_index(op.f("ix_notifications_status"), "notifications", ["status"], unique=False)
    op.create_index(op.f("ix_notifications_recipient_user_id"), "notifications", ["recipient_user_id"], unique=False)
    op.create_index(op.f("ix_notifications_related_entity_id"), "notifications", ["related_entity_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_notifications_related_entity_id"), table_name="notifications")
    op.drop_index(op.f("ix_notifications_recipient_user_id"), table_name="notifications")
    op.drop_index(op.f("ix_notifications_status"), table_name="notifications")
    op.drop_index(op.f("ix_notifications_notification_type"), table_name="notifications")
    op.drop_table("notifications")

    op.drop_index(op.f("ix_matching_runs_status"), table_name="matching_runs")
    op.drop_index(op.f("ix_matching_runs_operational_job_run_id"), table_name="matching_runs")
    op.drop_table("matching_runs")

    op.drop_index(op.f("ix_operational_job_runs_profile_id"), table_name="operational_job_runs")
    op.drop_index(op.f("ix_operational_job_runs_source_name"), table_name="operational_job_runs")
    op.drop_index(op.f("ix_operational_job_runs_status"), table_name="operational_job_runs")
    op.drop_index(op.f("ix_operational_job_runs_job_type"), table_name="operational_job_runs")
    op.drop_index(op.f("ix_operational_job_runs_job_config_id"), table_name="operational_job_runs")
    op.drop_table("operational_job_runs")

    op.drop_index(op.f("ix_operational_job_configs_enabled"), table_name="operational_job_configs")
    op.drop_index(op.f("ix_operational_job_configs_profile_id"), table_name="operational_job_configs")
    op.drop_index(op.f("ix_operational_job_configs_source_name"), table_name="operational_job_configs")
    op.drop_index(op.f("ix_operational_job_configs_job_type"), table_name="operational_job_configs")
    op.drop_index(op.f("ix_operational_job_configs_job_key"), table_name="operational_job_configs")
    op.drop_table("operational_job_configs")
