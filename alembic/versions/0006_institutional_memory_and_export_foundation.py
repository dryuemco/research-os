"""institutional memory and export foundation

Revision ID: 0006_institutional_memory_and_export_foundation
Revises: 0005_execution_runtime_foundation
Create Date: 2026-04-02 01:00:00
"""

from alembic import op
import sqlalchemy as sa


revision = "0006_institutional_memory_and_export_foundation"
down_revision = "0005_execution_runtime_foundation"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "document_sources",
        sa.Column("source_name", sa.String(length=128), nullable=False),
        sa.Column("source_uri", sa.String(length=1024), nullable=False),
        sa.Column("source_type", sa.String(length=64), nullable=False),
        sa.Column("metadata_json", sa.JSON(), nullable=False),
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_document_sources_source_name"), "document_sources", ["source_name"], unique=False)

    op.create_table(
        "memory_documents",
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("category", sa.String(length=64), nullable=False),
        sa.Column("source_id", sa.String(), nullable=False),
        sa.Column("content_text", sa.Text(), nullable=False),
        sa.Column("checksum", sa.String(length=128), nullable=False),
        sa.Column("version_label", sa.String(length=64), nullable=False),
        sa.Column("provenance_json", sa.JSON(), nullable=False),
        sa.Column("sensitive", sa.Boolean(), nullable=False),
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["source_id"], ["document_sources.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_memory_documents_title"), "memory_documents", ["title"], unique=False)
    op.create_index(op.f("ix_memory_documents_category"), "memory_documents", ["category"], unique=False)
    op.create_index(op.f("ix_memory_documents_source_id"), "memory_documents", ["source_id"], unique=False)
    op.create_index(op.f("ix_memory_documents_checksum"), "memory_documents", ["checksum"], unique=False)

    op.create_table(
        "memory_chunks",
        sa.Column("document_id", sa.String(), nullable=False),
        sa.Column("chunk_index", sa.Integer(), nullable=False),
        sa.Column("chunk_text", sa.Text(), nullable=False),
        sa.Column("token_estimate", sa.Integer(), nullable=False),
        sa.Column("metadata_json", sa.JSON(), nullable=False),
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["document_id"], ["memory_documents.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_memory_chunks_document_id"), "memory_chunks", ["document_id"], unique=False)

    op.create_table(
        "reusable_evidence_blocks",
        sa.Column("document_id", sa.String(), nullable=True),
        sa.Column("block_key", sa.String(length=128), nullable=False),
        sa.Column("category", sa.String(length=64), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("body_text", sa.Text(), nullable=False),
        sa.Column("tags", sa.JSON(), nullable=False),
        sa.Column("approval_status", sa.String(length=32), nullable=False),
        sa.Column("approved_by", sa.String(length=255), nullable=True),
        sa.Column("approved_at", sa.String(length=64), nullable=True),
        sa.Column("provenance_json", sa.JSON(), nullable=False),
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["document_id"], ["memory_documents.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_reusable_evidence_blocks_document_id"), "reusable_evidence_blocks", ["document_id"], unique=False)
    op.create_index(op.f("ix_reusable_evidence_blocks_block_key"), "reusable_evidence_blocks", ["block_key"], unique=True)
    op.create_index(op.f("ix_reusable_evidence_blocks_category"), "reusable_evidence_blocks", ["category"], unique=False)
    op.create_index(op.f("ix_reusable_evidence_blocks_approval_status"), "reusable_evidence_blocks", ["approval_status"], unique=False)

    op.create_table(
        "capability_profiles",
        sa.Column("profile_name", sa.String(length=255), nullable=False),
        sa.Column("domain_focus", sa.JSON(), nullable=False),
        sa.Column("capability_summary", sa.Text(), nullable=False),
        sa.Column("evidence_block_ids", sa.JSON(), nullable=False),
        sa.Column("maturity_level", sa.String(length=64), nullable=False),
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_capability_profiles_profile_name"), "capability_profiles", ["profile_name"], unique=True)

    op.create_table(
        "export_packages",
        sa.Column("proposal_id", sa.String(), nullable=False),
        sa.Column("package_name", sa.String(length=255), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("package_manifest", sa.JSON(), nullable=False),
        sa.Column("unresolved_items", sa.JSON(), nullable=False),
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["proposal_id"], ["proposals.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_export_packages_proposal_id"), "export_packages", ["proposal_id"], unique=False)
    op.create_index(op.f("ix_export_packages_status"), "export_packages", ["status"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_export_packages_status"), table_name="export_packages")
    op.drop_index(op.f("ix_export_packages_proposal_id"), table_name="export_packages")
    op.drop_table("export_packages")

    op.drop_index(op.f("ix_capability_profiles_profile_name"), table_name="capability_profiles")
    op.drop_table("capability_profiles")

    op.drop_index(op.f("ix_reusable_evidence_blocks_approval_status"), table_name="reusable_evidence_blocks")
    op.drop_index(op.f("ix_reusable_evidence_blocks_category"), table_name="reusable_evidence_blocks")
    op.drop_index(op.f("ix_reusable_evidence_blocks_block_key"), table_name="reusable_evidence_blocks")
    op.drop_index(op.f("ix_reusable_evidence_blocks_document_id"), table_name="reusable_evidence_blocks")
    op.drop_table("reusable_evidence_blocks")

    op.drop_index(op.f("ix_memory_chunks_document_id"), table_name="memory_chunks")
    op.drop_table("memory_chunks")

    op.drop_index(op.f("ix_memory_documents_checksum"), table_name="memory_documents")
    op.drop_index(op.f("ix_memory_documents_source_id"), table_name="memory_documents")
    op.drop_index(op.f("ix_memory_documents_category"), table_name="memory_documents")
    op.drop_index(op.f("ix_memory_documents_title"), table_name="memory_documents")
    op.drop_table("memory_documents")

    op.drop_index(op.f("ix_document_sources_source_name"), table_name="document_sources")
    op.drop_table("document_sources")
