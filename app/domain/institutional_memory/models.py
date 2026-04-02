from sqlalchemy import Boolean, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import JSON

from app.db.base import Base
from app.domain.common.enums import (
    ApprovalStatus,
    ExportArtifactType,
    ExportPackageStatus,
    MemoryCategory,
)
from app.domain.common.mixins import TimestampMixin, UUIDPrimaryKeyMixin

JSONType = JSON().with_variant(JSONB, "postgresql")


class DocumentSource(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "document_sources"

    source_name: Mapped[str] = mapped_column(String(128), index=True)
    source_uri: Mapped[str] = mapped_column(String(1024))
    source_type: Mapped[str] = mapped_column(String(64), default="internal")
    metadata_json: Mapped[dict] = mapped_column(JSONType, default=dict)


class MemoryDocument(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "memory_documents"

    title: Mapped[str] = mapped_column(String(255), index=True)
    category: Mapped[MemoryCategory] = mapped_column(Enum(MemoryCategory), index=True)
    source_id: Mapped[str] = mapped_column(
        ForeignKey("document_sources.id", ondelete="RESTRICT"), index=True
    )
    content_text: Mapped[str] = mapped_column(Text)
    checksum: Mapped[str] = mapped_column(String(128), index=True)
    version_label: Mapped[str] = mapped_column(String(64), default="v1")
    provenance_json: Mapped[dict] = mapped_column(JSONType, default=dict)
    sensitive: Mapped[bool] = mapped_column(Boolean, default=False)


class MemoryChunk(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "memory_chunks"

    document_id: Mapped[str] = mapped_column(
        ForeignKey("memory_documents.id", ondelete="CASCADE"), index=True
    )
    chunk_index: Mapped[int] = mapped_column(Integer)
    chunk_text: Mapped[str] = mapped_column(Text)
    token_estimate: Mapped[int] = mapped_column(Integer, default=0)
    metadata_json: Mapped[dict] = mapped_column(JSONType, default=dict)


class ReusableEvidenceBlock(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "reusable_evidence_blocks"

    document_id: Mapped[str | None] = mapped_column(
        ForeignKey("memory_documents.id", ondelete="SET NULL"), nullable=True, index=True
    )
    block_key: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    category: Mapped[MemoryCategory] = mapped_column(Enum(MemoryCategory), index=True)
    title: Mapped[str] = mapped_column(String(255))
    body_text: Mapped[str] = mapped_column(Text)
    tags: Mapped[list[str]] = mapped_column(JSONType, default=list)
    approval_status: Mapped[ApprovalStatus] = mapped_column(
        Enum(ApprovalStatus),
        default=ApprovalStatus.DRAFT,
        index=True,
    )
    approved_by: Mapped[str | None] = mapped_column(String(255), nullable=True)
    approved_at: Mapped[str | None] = mapped_column(String(64), nullable=True)
    provenance_json: Mapped[dict] = mapped_column(JSONType, default=dict)


class CapabilityProfile(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "capability_profiles"

    profile_name: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    domain_focus: Mapped[list[str]] = mapped_column(JSONType, default=list)
    capability_summary: Mapped[str] = mapped_column(Text)
    evidence_block_ids: Mapped[list[str]] = mapped_column(JSONType, default=list)
    maturity_level: Mapped[str] = mapped_column(String(64), default="emerging")


class ExportPackage(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "export_packages"

    proposal_id: Mapped[str] = mapped_column(
        ForeignKey("proposals.id", ondelete="CASCADE"), index=True
    )
    proposal_version_id: Mapped[str | None] = mapped_column(
        ForeignKey("proposal_versions.id", ondelete="SET NULL"), nullable=True, index=True
    )
    package_name: Mapped[str] = mapped_column(String(255))
    status: Mapped[ExportPackageStatus] = mapped_column(
        Enum(ExportPackageStatus),
        default=ExportPackageStatus.DRAFT,
        index=True,
    )
    package_manifest: Mapped[dict] = mapped_column(JSONType, default=dict)
    unresolved_items: Mapped[list[dict]] = mapped_column(JSONType, default=list)
    generated_by: Mapped[str] = mapped_column(String(255), default="system")
    approval_actor_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    supersedes_package_id: Mapped[str | None] = mapped_column(
        ForeignKey("export_packages.id", ondelete="SET NULL"), nullable=True
    )


class ExportArtifact(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "export_artifacts"

    export_package_id: Mapped[str] = mapped_column(
        ForeignKey("export_packages.id", ondelete="CASCADE"), index=True
    )
    artifact_type: Mapped[ExportArtifactType] = mapped_column(Enum(ExportArtifactType), index=True)
    file_name: Mapped[str] = mapped_column(String(255))
    media_type: Mapped[str] = mapped_column(String(128), default="text/markdown")
    content_text: Mapped[str] = mapped_column(Text)
    checksum: Mapped[str] = mapped_column(String(128), index=True)
    metadata_json: Mapped[dict] = mapped_column(JSONType, default=dict)
