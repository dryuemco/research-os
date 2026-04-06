import pytest
from pydantic import ValidationError

from app.domain.common.enums import ApprovalStatus, MemoryCategory
from app.schemas.memory import (
    DocumentSourceCreate,
    MemoryDocumentCreate,
    RetrievalQuery,
    ReusableBlockCreate,
    ReusableBlockUpdate,
)
from app.services.memory_service import MemoryService
from app.services.retrieval_service import RetrievalService


def _seed_memory(db_session):
    service = MemoryService(db_session)
    source = service.create_source(
        DocumentSourceCreate(
            source_name="org-profile",
            source_uri="internal://org-profile",
            source_type="internal",
        )
    )
    document = service.create_document(
        MemoryDocumentCreate(
            title="Institution Profile",
            category=MemoryCategory.ORGANIZATION_PROFILE,
            source_id=source.id,
            content_text="Our infrastructure includes HPC and secure data rooms.",
        )
    )
    block = service.create_block(
        ReusableBlockCreate(
            document_id=document.id,
            block_key="org_hpc_evidence",
            category=MemoryCategory.INFRASTRUCTURE,
            title="HPC Infrastructure",
            body_text="We provide HPC clusters for reproducible AI workloads.",
            tags=["hpc", "ai"],
        )
    )
    service.update_block(
        block.id,
        ReusableBlockUpdate(
            approval_status=ApprovalStatus.APPROVED,
            approved_by="ops-user",
        ),
    )
    db_session.commit()
    return block


def test_retrieval_filters_approved_only(db_session):
    _seed_memory(db_session)
    retrieval = RetrievalService(db_session)
    results = retrieval.retrieve(RetrievalQuery(query_text="HPC reproducible AI", limit=5))
    assert results
    assert all(item.block.approval_status == ApprovalStatus.APPROVED for item in results)


def test_retrieval_schema_validation():
    with pytest.raises(ValidationError):
        RetrievalQuery(query_text="x", limit=5, filters={"unknown": True})


