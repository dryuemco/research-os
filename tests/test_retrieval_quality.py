from app.domain.common.enums import ApprovalStatus, MemoryCategory
from app.schemas.memory import (
    DocumentSourceCreate,
    MemoryDocumentCreate,
    RetrievalBackendMode,
    RetrievalPolicy,
    RetrievalQuery,
    ReusableBlockCreate,
    ReusableBlockUpdate,
)
from app.services.memory_service import MemoryService
from app.services.retrieval_service import RetrievalService


def _seed_blocks(db_session):
    service = MemoryService(db_session)
    source = service.create_source(
        DocumentSourceCreate(
            source_name="retrieval",
            source_uri="internal://r",
            source_type="internal",
        )
    )
    doc = service.create_document(
        MemoryDocumentCreate(
            title="Partner Evidence",
            category=MemoryCategory.IMPACT_EVIDENCE,
            source_id=source.id,
            content_text="Evidence baseline",
        )
    )
    b1 = service.create_block(
        ReusableBlockCreate(
            document_id=doc.id,
            block_key="b1",
            category=MemoryCategory.IMPACT_EVIDENCE,
            title="Impact KPI",
            body_text="KPI evidence for climate and AI impact outcomes",
            tags=["impact", "kpi"],
        )
    )
    b2 = service.create_block(
        ReusableBlockCreate(
            document_id=doc.id,
            block_key="b2",
            category=MemoryCategory.INFRASTRUCTURE,
            title="HPC Cluster",
            body_text="HPC cluster and secure infra for ai workloads",
            tags=["hpc", "ai"],
        )
    )
    service.update_block(
        b1.id,
        ReusableBlockUpdate(
            approval_status=ApprovalStatus.APPROVED,
            approved_by="ops-admin",
        ),
    )
    service.update_block(
        b2.id,
        ReusableBlockUpdate(
            approval_status=ApprovalStatus.APPROVED,
            approved_by="ops-admin",
        ),
    )
    db_session.commit()


def test_hybrid_retrieval_policy_respects_budget_and_category_caps(db_session):
    _seed_blocks(db_session)
    retrieval = RetrievalService(db_session)
    query = RetrievalQuery(
        query_text="ai impact kpi infrastructure",
        limit=5,
        task_type="section_draft",
        policy=RetrievalPolicy(
            backend_mode=RetrievalBackendMode.HYBRID,
            max_context_chars=120,
            max_per_category=1,
            min_confidence=0.1,
        ),
    )
    items = retrieval.retrieve(query)
    assert items
    categories = [item.block.category for item in items]
    assert len(categories) == len(set(categories))
    assert all(item.selected_reason for item in items)
