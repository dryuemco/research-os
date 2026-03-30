"""proposal factory foundation

Revision ID: 0003_proposal_factory_foundation
Revises: 0002_opportunity_ingestion_matching_workflow
Create Date: 2026-03-30 02:00:00
"""

from alembic import op
import sqlalchemy as sa


revision = "0003_proposal_factory_foundation"
down_revision = "0002_opportunity_ingestion_matching_workflow"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "proposals",
        sa.Column(
            "name", sa.String(length=255), nullable=False, server_default="Proposal Workspace"
        ),
    )
    op.add_column(
        "proposals",
        sa.Column("latest_version_number", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "proposals",
        sa.Column("unresolved_issues_json", sa.JSON(), nullable=False, server_default="[]"),
    )
    op.add_column(
        "proposals",
        sa.Column("stage_metadata", sa.JSON(), nullable=False, server_default="{}"),
    )
    op.add_column(
        "proposals",
        sa.Column(
            "human_approved_for_export", sa.Boolean(), nullable=False, server_default=sa.false()
        ),
    )

    op.add_column(
        "proposal_sections",
        sa.Column("source_request_json", sa.JSON(), nullable=False, server_default="{}"),
    )
    op.add_column(
        "proposal_sections",
        sa.Column("review_status", sa.String(length=64), nullable=False, server_default="pending"),
    )

    op.add_column(
        "review_rounds",
        sa.Column("convergence_decision", sa.String(length=64), nullable=True),
    )

    op.add_column(
        "review_comments",
        sa.Column("blocker", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.add_column(
        "review_comments",
        sa.Column("issue_code", sa.String(length=64), nullable=True),
    )

    op.create_table(
        "proposal_versions",
        sa.Column("proposal_id", sa.String(), nullable=False),
        sa.Column("version_number", sa.Integer(), nullable=False),
        sa.Column("concept_note_json", sa.JSON(), nullable=False),
        sa.Column("section_plan_json", sa.JSON(), nullable=False),
        sa.Column("status", sa.String(length=64), nullable=False),
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
        op.f("ix_proposal_versions_proposal_id"), "proposal_versions", ["proposal_id"], unique=False
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_proposal_versions_proposal_id"), table_name="proposal_versions")
    op.drop_table("proposal_versions")

    op.drop_column("review_comments", "issue_code")
    op.drop_column("review_comments", "blocker")

    op.drop_column("review_rounds", "convergence_decision")

    op.drop_column("proposal_sections", "review_status")
    op.drop_column("proposal_sections", "source_request_json")

    op.drop_column("proposals", "human_approved_for_export")
    op.drop_column("proposals", "stage_metadata")
    op.drop_column("proposals", "unresolved_issues_json")
    op.drop_column("proposals", "latest_version_number")
    op.drop_column("proposals", "name")
