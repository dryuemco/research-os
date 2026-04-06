from __future__ import annotations

import hashlib
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.common.enums import ApprovalStatus
from app.domain.institutional_memory.models import (
    DocumentSource,
    MemoryChunk,
    MemoryDocument,
    ReusableEvidenceBlock,
)
from app.schemas.audit import AuditEventSchema
from app.schemas.memory import (
    DocumentSourceCreate,
    MemoryDocumentCreate,
    ReusableBlockCreate,
    ReusableBlockUpdate,
)
from app.services.audit_service import AuditService


class MemoryService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.audit = AuditService(db)

    def create_source(self, request: DocumentSourceCreate) -> DocumentSource:
        source = DocumentSource(**request.model_dump(mode="json"))
        self.db.add(source)
        self.db.flush()
        self.audit.emit(
            AuditEventSchema(
                event_type="memory_source_created",
                entity_type="document_source",
                entity_id=source.id,
                actor_type="system",
                actor_id="memory_service",
                payload={"source_name": source.source_name},
            )
        )
        self.db.flush()
        return source

    def create_document(self, request: MemoryDocumentCreate) -> MemoryDocument:
        source = self.db.get(DocumentSource, request.source_id)
        if source is None:
            raise ValueError("Document source not found")
        checksum = hashlib.sha256(request.content_text.encode()).hexdigest()
        document = MemoryDocument(
            title=request.title,
            category=request.category,
            source_id=request.source_id,
            content_text=request.content_text,
            checksum=checksum,
            version_label=request.version_label,
            provenance_json=request.provenance_json,
            sensitive=request.sensitive,
        )
        self.db.add(document)
        self.db.flush()
        self._chunk_document(document)
        self.audit.emit(
            AuditEventSchema(
                event_type="memory_document_created",
                entity_type="memory_document",
                entity_id=document.id,
                actor_type="system",
                actor_id="memory_service",
                payload={"checksum": checksum, "category": document.category.value},
            )
        )
        self.db.flush()
        return document

    def create_block(self, request: ReusableBlockCreate) -> ReusableEvidenceBlock:
        if request.document_id:
            document = self.db.get(MemoryDocument, request.document_id)
            if document is None:
                raise ValueError("Memory document not found")

        block = ReusableEvidenceBlock(
            **request.model_dump(mode="json"),
            approval_status=ApprovalStatus.DRAFT,
        )
        self.db.add(block)
        self.db.flush()
        self.audit.emit(
            AuditEventSchema(
                event_type="memory_block_created",
                entity_type="reusable_evidence_block",
                entity_id=block.id,
                actor_type="system",
                actor_id="memory_service",
                payload={"block_key": block.block_key},
            )
        )
        self.db.flush()
        return block

    def update_block(self, block_id: str, request: ReusableBlockUpdate) -> ReusableEvidenceBlock:
        block = self.db.get(ReusableEvidenceBlock, block_id)
        if block is None:
            raise ValueError("Reusable block not found")

        payload = request.model_dump(exclude_none=True, mode="json")
        for key, value in payload.items():
            setattr(block, key, value)

        if request.approval_status == ApprovalStatus.APPROVED:
            if not request.approved_by:
                raise ValueError("approved_by must be provided when approving")
            block.approved_at = datetime.now(UTC).isoformat()

        self.db.add(block)
        self.audit.emit(
            AuditEventSchema(
                event_type="memory_block_updated",
                entity_type="reusable_evidence_block",
                entity_id=block.id,
                actor_type="system",
                actor_id="memory_service",
                payload={"changes": list(payload.keys())},
            )
        )
        self.db.flush()
        return block

    def list_blocks(self, *, approved_only: bool = False) -> list[ReusableEvidenceBlock]:
        stmt = select(ReusableEvidenceBlock).order_by(ReusableEvidenceBlock.created_at.desc())
        if approved_only:
            stmt = stmt.where(ReusableEvidenceBlock.approval_status == ApprovalStatus.APPROVED)
        return self.db.scalars(stmt).all()

    def get_block(self, block_id: str) -> ReusableEvidenceBlock:
        block = self.db.get(ReusableEvidenceBlock, block_id)
        if block is None:
            raise ValueError("Reusable block not found")
        return block

    def _chunk_document(self, document: MemoryDocument) -> None:
        chunks = [c.strip() for c in document.content_text.split("\n\n") if c.strip()]
        if not chunks:
            chunks = [document.content_text]
        for idx, chunk in enumerate(chunks):
            self.db.add(
                MemoryChunk(
                    document_id=document.id,
                    chunk_index=idx,
                    chunk_text=chunk,
                    token_estimate=max(1, len(chunk.split())),
                    metadata_json={"strategy": "double_newline"},
                )
            )
