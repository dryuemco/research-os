"""initial foundation

Revision ID: 0001_initial_foundation
Revises:
Create Date: 2026-03-30 00:00:00
"""

from alembic import op
import sqlalchemy as sa


revision = "0001_initial_foundation"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "audit_events",
        sa.Column("event_type", sa.String(length=128), nullable=False),
        sa.Column("entity_type", sa.String(length=128), nullable=False),
        sa.Column("entity_id", sa.String(length=255), nullable=False),
        sa.Column("actor_type", sa.String(length=64), nullable=False),
        sa.Column("actor_id", sa.String(length=255), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("id", sa.String(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_audit_events_actor_id"), "audit_events", ["actor_id"], unique=False)
    op.create_index(
        op.f("ix_audit_events_actor_type"), "audit_events", ["actor_type"], unique=False
    )
    op.create_index(op.f("ix_audit_events_entity_id"), "audit_events", ["entity_id"], unique=False)
    op.create_index(
        op.f("ix_audit_events_entity_type"), "audit_events", ["entity_type"], unique=False
    )
    op.create_index(
        op.f("ix_audit_events_event_type"), "audit_events", ["event_type"], unique=False
    )

    op.create_table(
        "interest_profiles",
        sa.Column("user_id", sa.String(length=255), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("parameters_json", sa.JSON(), nullable=False),
        sa.Column("active_version", sa.Integer(), nullable=False),
        sa.Column("id", sa.String(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_interest_profiles_user_id"), "interest_profiles", ["user_id"], unique=False
    )

    op.create_table(
        "opportunities",
        sa.Column("source_program", sa.String(length=100), nullable=False),
        sa.Column("source_url", sa.String(length=1024), nullable=False),
        sa.Column("external_id", sa.String(length=255), nullable=False),
        sa.Column("title", sa.String(length=512), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("deadline_at", sa.String(length=64), nullable=True),
        sa.Column("call_status", sa.String(length=64), nullable=False),
        sa.Column("budget_total", sa.Float(), nullable=True),
        sa.Column("currency", sa.String(length=16), nullable=True),
        sa.Column("state", sa.String(length=32), nullable=False),
        sa.Column("current_version_hash", sa.String(length=128), nullable=False),
        sa.Column("raw_payload", sa.JSON(), nullable=False),
        sa.Column("id", sa.String(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_opportunities_current_version_hash"),
        "opportunities",
        ["current_version_hash"],
        unique=False,
    )
    op.create_index(
        op.f("ix_opportunities_external_id"), "opportunities", ["external_id"], unique=True
    )
    op.create_index(
        op.f("ix_opportunities_source_program"), "opportunities", ["source_program"], unique=False
    )
    op.create_index(op.f("ix_opportunities_state"), "opportunities", ["state"], unique=False)

    op.create_table(
        "provider_accounts",
        sa.Column("provider_name", sa.String(length=64), nullable=False),
        sa.Column("account_ref", sa.String(length=255), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("config_json", sa.JSON(), nullable=False),
        sa.Column("id", sa.String(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("account_ref"),
    )
    op.create_index(
        op.f("ix_provider_accounts_provider_name"),
        "provider_accounts",
        ["provider_name"],
        unique=False,
    )
    op.create_index(
        op.f("ix_provider_accounts_status"), "provider_accounts", ["status"], unique=False
    )

    op.create_table(
        "provider_quota_snapshots",
        sa.Column("provider_name", sa.String(length=64), nullable=False),
        sa.Column("account_ref", sa.String(length=255), nullable=False),
        sa.Column("model_name", sa.String(length=128), nullable=False),
        sa.Column("window_start", sa.DateTime(timezone=True), nullable=False),
        sa.Column("window_end", sa.DateTime(timezone=True), nullable=False),
        sa.Column("requests_used", sa.Integer(), nullable=False),
        sa.Column("tokens_used", sa.Integer(), nullable=False),
        sa.Column("spend_used", sa.Numeric(precision=12, scale=4), nullable=False),
        sa.Column("status", sa.String(length=64), nullable=False),
        sa.Column("raw_payload", sa.JSON(), nullable=False),
        sa.Column("id", sa.String(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_provider_quota_snapshots_account_ref"),
        "provider_quota_snapshots",
        ["account_ref"],
        unique=False,
    )
    op.create_index(
        op.f("ix_provider_quota_snapshots_model_name"),
        "provider_quota_snapshots",
        ["model_name"],
        unique=False,
    )
    op.create_index(
        op.f("ix_provider_quota_snapshots_provider_name"),
        "provider_quota_snapshots",
        ["provider_name"],
        unique=False,
    )

    op.create_table(
        "task_graphs",
        sa.Column("project_ref", sa.String(length=255), nullable=False),
        sa.Column("source_version_ref", sa.String(length=255), nullable=False),
        sa.Column("graph_json", sa.JSON(), nullable=False),
        sa.Column("id", sa.String(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_task_graphs_project_ref"), "task_graphs", ["project_ref"], unique=False
    )
    op.create_index(
        op.f("ix_task_graphs_source_version_ref"),
        "task_graphs",
        ["source_version_ref"],
        unique=False,
    )

    op.create_table(
        "opportunity_versions",
        sa.Column("opportunity_id", sa.String(), nullable=False),
        sa.Column("version_hash", sa.String(length=128), nullable=False),
        sa.Column("full_text", sa.Text(), nullable=False),
        sa.Column("eligibility_notes", sa.JSON(), nullable=False),
        sa.Column("expected_outcomes", sa.JSON(), nullable=False),
        sa.Column("raw_payload", sa.JSON(), nullable=False),
        sa.Column("is_latest", sa.Boolean(), nullable=False),
        sa.Column("id", sa.String(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["opportunity_id"], ["opportunities.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_opportunity_versions_version_hash"),
        "opportunity_versions",
        ["version_hash"],
        unique=False,
    )

    op.create_table(
        "match_results",
        sa.Column("opportunity_id", sa.String(), nullable=False),
        sa.Column("profile_id", sa.String(), nullable=False),
        sa.Column("scoring_policy_id", sa.String(length=255), nullable=False),
        sa.Column("hard_filter_pass", sa.Boolean(), nullable=False),
        sa.Column("hard_filter_reasons", sa.JSON(), nullable=False),
        sa.Column("scores", sa.JSON(), nullable=False),
        sa.Column("total_score", sa.Float(), nullable=False),
        sa.Column("explanations", sa.JSON(), nullable=False),
        sa.Column("recommended_role", sa.String(length=64), nullable=True),
        sa.Column("red_flags", sa.JSON(), nullable=False),
        sa.Column("id", sa.String(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["opportunity_id"], ["opportunities.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["profile_id"], ["interest_profiles.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "proposals",
        sa.Column("opportunity_id", sa.String(), nullable=False),
        sa.Column("owner_id", sa.String(length=255), nullable=False),
        sa.Column("template_type", sa.String(length=100), nullable=False),
        sa.Column("page_limit", sa.Integer(), nullable=True),
        sa.Column("state", sa.String(length=32), nullable=False),
        sa.Column("mandatory_sections", sa.JSON(), nullable=False),
        sa.Column("compliance_rules", sa.JSON(), nullable=False),
        sa.Column("id", sa.String(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["opportunity_id"], ["opportunities.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_proposals_owner_id"), "proposals", ["owner_id"], unique=False)
    op.create_index(op.f("ix_proposals_state"), "proposals", ["state"], unique=False)

    op.create_table(
        "coding_tasks",
        sa.Column("task_graph_id", sa.String(), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("acceptance_criteria", sa.JSON(), nullable=False),
        sa.Column("context_refs", sa.JSON(), nullable=False),
        sa.Column("provider_policy", sa.JSON(), nullable=False),
        sa.Column("recommended_models", sa.JSON(), nullable=False),
        sa.Column("estimated_cost_band", sa.String(length=32), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("id", sa.String(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["task_graph_id"], ["task_graphs.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_coding_tasks_status"), "coding_tasks", ["status"], unique=False)

    op.create_table(
        "proposal_sections",
        sa.Column("proposal_id", sa.String(), nullable=False),
        sa.Column("section_key", sa.String(length=128), nullable=False),
        sa.Column("draft_text", sa.Text(), nullable=False),
        sa.Column("model_provider", sa.String(length=64), nullable=False),
        sa.Column("model_name", sa.String(length=128), nullable=False),
        sa.Column("prompt_version", sa.String(length=64), nullable=False),
        sa.Column("round_number", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=64), nullable=False),
        sa.Column("compliance_score", sa.Float(), nullable=True),
        sa.Column("id", sa.String(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["proposal_id"], ["proposals.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_proposal_sections_proposal_id"), "proposal_sections", ["proposal_id"], unique=False
    )
    op.create_index(
        op.f("ix_proposal_sections_section_key"), "proposal_sections", ["section_key"], unique=False
    )

    op.create_table(
        "review_rounds",
        sa.Column("proposal_id", sa.String(), nullable=False),
        sa.Column("round_number", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=64), nullable=False),
        sa.Column("reviewer_roles", sa.JSON(), nullable=False),
        sa.Column("stop_reason", sa.String(length=255), nullable=True),
        sa.Column("id", sa.String(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["proposal_id"], ["proposals.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_review_rounds_proposal_id"), "review_rounds", ["proposal_id"], unique=False
    )

    op.create_table(
        "review_comments",
        sa.Column("review_round_id", sa.String(), nullable=False),
        sa.Column("reviewer_role", sa.String(length=128), nullable=False),
        sa.Column("severity", sa.String(length=32), nullable=False),
        sa.Column("comment_text", sa.Text(), nullable=False),
        sa.Column("metadata_json", sa.JSON(), nullable=False),
        sa.Column("id", sa.String(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["review_round_id"], ["review_rounds.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_review_comments_review_round_id"),
        "review_comments",
        ["review_round_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_review_comments_review_round_id"), table_name="review_comments")
    op.drop_table("review_comments")
    op.drop_index(op.f("ix_review_rounds_proposal_id"), table_name="review_rounds")
    op.drop_table("review_rounds")
    op.drop_index(op.f("ix_proposal_sections_section_key"), table_name="proposal_sections")
    op.drop_index(op.f("ix_proposal_sections_proposal_id"), table_name="proposal_sections")
    op.drop_table("proposal_sections")
    op.drop_index(op.f("ix_coding_tasks_status"), table_name="coding_tasks")
    op.drop_table("coding_tasks")
    op.drop_index(op.f("ix_proposals_state"), table_name="proposals")
    op.drop_index(op.f("ix_proposals_owner_id"), table_name="proposals")
    op.drop_table("proposals")
    op.drop_table("match_results")
    op.drop_index(op.f("ix_opportunity_versions_version_hash"), table_name="opportunity_versions")
    op.drop_table("opportunity_versions")
    op.drop_index(op.f("ix_task_graphs_source_version_ref"), table_name="task_graphs")
    op.drop_index(op.f("ix_task_graphs_project_ref"), table_name="task_graphs")
    op.drop_table("task_graphs")
    op.drop_index(
        op.f("ix_provider_quota_snapshots_provider_name"), table_name="provider_quota_snapshots"
    )
    op.drop_index(
        op.f("ix_provider_quota_snapshots_model_name"), table_name="provider_quota_snapshots"
    )
    op.drop_index(
        op.f("ix_provider_quota_snapshots_account_ref"), table_name="provider_quota_snapshots"
    )
    op.drop_table("provider_quota_snapshots")
    op.drop_index(op.f("ix_provider_accounts_status"), table_name="provider_accounts")
    op.drop_index(op.f("ix_provider_accounts_provider_name"), table_name="provider_accounts")
    op.drop_table("provider_accounts")
    op.drop_index(op.f("ix_opportunities_state"), table_name="opportunities")
    op.drop_index(op.f("ix_opportunities_source_program"), table_name="opportunities")
    op.drop_index(op.f("ix_opportunities_external_id"), table_name="opportunities")
    op.drop_index(op.f("ix_opportunities_current_version_hash"), table_name="opportunities")
    op.drop_table("opportunities")
    op.drop_index(op.f("ix_interest_profiles_user_id"), table_name="interest_profiles")
    op.drop_table("interest_profiles")
    op.drop_index(op.f("ix_audit_events_event_type"), table_name="audit_events")
    op.drop_index(op.f("ix_audit_events_entity_type"), table_name="audit_events")
    op.drop_index(op.f("ix_audit_events_entity_id"), table_name="audit_events")
    op.drop_index(op.f("ix_audit_events_actor_type"), table_name="audit_events")
    op.drop_index(op.f("ix_audit_events_actor_id"), table_name="audit_events")
    op.drop_table("audit_events")
