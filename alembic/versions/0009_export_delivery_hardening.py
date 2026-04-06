"""export delivery hardening metadata and format columns

Revision ID: 0009_export_delivery_hardening
Revises: 0008_pilot_hardening_auth_and_storage
Create Date: 2026-04-02 07:00:00
"""

from alembic import op
import sqlalchemy as sa


revision = "0009_export_delivery_hardening"
down_revision = "0008_pilot_hardening_auth_and_storage"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "export_artifacts",
        sa.Column("artifact_format", sa.String(length=32), nullable=False, server_default="markdown"),
    )
    op.add_column("export_artifacts", sa.Column("content_base64", sa.Text(), nullable=True))
    op.add_column(
        "export_artifacts",
        sa.Column("size_bytes", sa.Integer(), nullable=False, server_default="0"),
    )


def downgrade() -> None:
    op.drop_column("export_artifacts", "size_bytes")
    op.drop_column("export_artifacts", "content_base64")
    op.drop_column("export_artifacts", "artifact_format")
