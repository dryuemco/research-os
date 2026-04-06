"""partner intelligence and quality foundation

Revision ID: 0011_partner_intelligence_and_quality_foundation
Revises: 0010_operational_loop_foundation
Create Date: 2026-04-06 10:00:00
"""

from alembic import op
import sqlalchemy as sa


revision = "0011_partner_intelligence_and_quality_foundation"
down_revision = "0010_operational_loop_foundation"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "partner_profiles",
        sa.Column("partner_name", sa.String(length=255), nullable=False),
        sa.Column("legal_name", sa.String(length=255), nullable=True),
        sa.Column("country_code", sa.String(length=8), nullable=True),
        sa.Column("geography_notes", sa.Text(), nullable=True),
        sa.Column("organization_type", sa.String(length=64), nullable=False),
        sa.Column("capability_tags", sa.JSON(), nullable=False),
        sa.Column("program_participation", sa.JSON(), nullable=False),
        sa.Column("role_suitability", sa.JSON(), nullable=False),
        sa.Column("source_metadata", sa.JSON(), nullable=False),
        sa.Column("intelligence_notes", sa.Text(), nullable=True),
        sa.Column("active", sa.Boolean(), nullable=False),
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_partner_profiles_partner_name"), "partner_profiles", ["partner_name"], unique=False)
    op.create_index(op.f("ix_partner_profiles_country_code"), "partner_profiles", ["country_code"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_partner_profiles_country_code"), table_name="partner_profiles")
    op.drop_index(op.f("ix_partner_profiles_partner_name"), table_name="partner_profiles")
    op.drop_table("partner_profiles")
