"""export renderer and artifacts foundation

Revision ID: 0007_export_renderer_and_artifacts
Revises: 0006_institutional_memory_and_export_foundation
Create Date: 2026-04-02 02:00:00
"""

from alembic import op
import sqlalchemy as sa


revision = "0007_export_renderer_and_artifacts"
down_revision = "0006_institutional_memory_and_export_foundation"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("export_packages", sa.Column("proposal_version_id", sa.String(), nullable=True))
    op.add_column("export_packages", sa.Column("generated_by", sa.String(length=255), nullable=False, server_default="system"))
    op.add_column("export_packages", sa.Column("approval_actor_id", sa.String(length=255), nullable=True))
    op.add_column("export_packages", sa.Column("supersedes_package_id", sa.String(), nullable=True))
    op.create_foreign_key(
        None,
        "export_packages",
        "proposal_versions",
        ["proposal_version_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_foreign_key(
        None,
        "export_packages",
        "export_packages",
        ["supersedes_package_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index(
        op.f("ix_export_packages_proposal_version_id"),
        "export_packages",
        ["proposal_version_id"],
        unique=False,
    )

    op.create_table(
        "export_artifacts",
        sa.Column("export_package_id", sa.String(), nullable=False),
        sa.Column("artifact_type", sa.String(length=64), nullable=False),
        sa.Column("file_name", sa.String(length=255), nullable=False),
        sa.Column("media_type", sa.String(length=128), nullable=False),
        sa.Column("content_text", sa.Text(), nullable=False),
        sa.Column("checksum", sa.String(length=128), nullable=False),
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
        sa.ForeignKeyConstraint(["export_package_id"], ["export_packages.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_export_artifacts_export_package_id"), "export_artifacts", ["export_package_id"], unique=False)
    op.create_index(op.f("ix_export_artifacts_artifact_type"), "export_artifacts", ["artifact_type"], unique=False)
    op.create_index(op.f("ix_export_artifacts_checksum"), "export_artifacts", ["checksum"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_export_artifacts_checksum"), table_name="export_artifacts")
    op.drop_index(op.f("ix_export_artifacts_artifact_type"), table_name="export_artifacts")
    op.drop_index(op.f("ix_export_artifacts_export_package_id"), table_name="export_artifacts")
    op.drop_table("export_artifacts")

    op.drop_index(op.f("ix_export_packages_proposal_version_id"), table_name="export_packages")
    op.drop_constraint(None, "export_packages", type_="foreignkey")
    op.drop_constraint(None, "export_packages", type_="foreignkey")
    op.drop_column("export_packages", "supersedes_package_id")
    op.drop_column("export_packages", "approval_actor_id")
    op.drop_column("export_packages", "generated_by")
    op.drop_column("export_packages", "proposal_version_id")
