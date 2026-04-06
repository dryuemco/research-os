"""pilot hardening auth and artifact storage

Revision ID: 0008_pilot_hardening_auth_and_storage
Revises: 0007_export_renderer_and_artifacts
Create Date: 2026-04-02 03:00:00
"""

from alembic import op
import sqlalchemy as sa


revision = "0008_pilot_hardening_auth_and_storage"
down_revision = "0007_export_renderer_and_artifacts"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("display_name", sa.String(length=255), nullable=False),
        sa.Column("role", sa.String(length=64), nullable=False),
        sa.Column("team_name", sa.String(length=255), nullable=True),
        sa.Column("org_name", sa.String(length=255), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=True)
    op.create_index(op.f("ix_users_role"), "users", ["role"], unique=False)

    op.add_column("export_artifacts", sa.Column("storage_backend", sa.String(length=64), nullable=False, server_default="db_fallback"))
    op.add_column("export_artifacts", sa.Column("storage_locator", sa.String(length=1024), nullable=True))


def downgrade() -> None:
    op.drop_column("export_artifacts", "storage_locator")
    op.drop_column("export_artifacts", "storage_backend")

    op.drop_index(op.f("ix_users_role"), table_name="users")
    op.drop_index(op.f("ix_users_email"), table_name="users")
    op.drop_table("users")
