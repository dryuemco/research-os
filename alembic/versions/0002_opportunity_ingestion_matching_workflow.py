"""opportunity ingestion and matching workflow foundation

Revision ID: 0002_opportunity_ingestion_matching_workflow
Revises: 0001_initial_foundation
Create Date: 2026-03-30 00:30:00
"""

from alembic import op
import sqlalchemy as sa


revision = "0002_opportunity_ingestion_matching_workflow"
down_revision = "0001_initial_foundation"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "opportunity_ingestion_snapshots",
        sa.Column("source_name", sa.String(length=100), nullable=False),
        sa.Column("source_record_id", sa.String(length=255), nullable=False),
        sa.Column("payload_hash", sa.String(length=128), nullable=False),
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
        sa.UniqueConstraint(
            "source_name", "source_record_id", "payload_hash", name="uq_ingestion_snapshot"
        ),
    )
    op.create_index(
        op.f("ix_opportunity_ingestion_snapshots_payload_hash"),
        "opportunity_ingestion_snapshots",
        ["payload_hash"],
        unique=False,
    )
    op.create_index(
        op.f("ix_opportunity_ingestion_snapshots_source_name"),
        "opportunity_ingestion_snapshots",
        ["source_name"],
        unique=False,
    )
    op.create_index(
        op.f("ix_opportunity_ingestion_snapshots_source_record_id"),
        "opportunity_ingestion_snapshots",
        ["source_record_id"],
        unique=False,
    )

    op.add_column(
        "opportunity_versions",
        sa.Column("provenance", sa.JSON(), nullable=False, server_default="{}"),
    )
    op.add_column(
        "opportunity_versions",
        sa.Column("uncertainty_notes", sa.JSON(), nullable=False, server_default="[]"),
    )

    op.add_column(
        "match_results", sa.Column("rationale", sa.JSON(), nullable=False, server_default="{}")
    )
    op.add_column(
        "match_results",
        sa.Column("recommendation", sa.String(length=64), nullable=False, server_default="reject"),
    )


def downgrade() -> None:
    op.drop_column("match_results", "recommendation")
    op.drop_column("match_results", "rationale")

    op.drop_column("opportunity_versions", "uncertainty_notes")
    op.drop_column("opportunity_versions", "provenance")

    op.drop_index(
        op.f("ix_opportunity_ingestion_snapshots_source_record_id"),
        table_name="opportunity_ingestion_snapshots",
    )
    op.drop_index(
        op.f("ix_opportunity_ingestion_snapshots_source_name"),
        table_name="opportunity_ingestion_snapshots",
    )
    op.drop_index(
        op.f("ix_opportunity_ingestion_snapshots_payload_hash"),
        table_name="opportunity_ingestion_snapshots",
    )
    op.drop_table("opportunity_ingestion_snapshots")
