from __future__ import annotations

import math

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.common.enums import ApprovalStatus
from app.domain.institutional_memory.models import ReusableEvidenceBlock
from app.schemas.memory import (
    BlockProvenance,
    RetrievalQuery,
    RetrievalResult,
    ReusableBlockResponse,
)


class LexicalRetrievalBackend:
    backend_name = "lexical"
    supports_semantic = False
    supports_filters = True
    supports_hybrid_fusion = True

    def __init__(self, db: Session) -> None:
        self.db = db

    def retrieve(self, request: RetrievalQuery) -> list[RetrievalResult]:
        stmt = select(ReusableEvidenceBlock)
        filters = request.filters
        if filters.approved_only:
            stmt = stmt.where(ReusableEvidenceBlock.approval_status == ApprovalStatus.APPROVED)
        if filters.categories:
            stmt = stmt.where(ReusableEvidenceBlock.category.in_(filters.categories))
        if filters.tags:
            for tag in filters.tags:
                stmt = stmt.where(ReusableEvidenceBlock.tags.contains([tag]))

        items = self.db.scalars(stmt).all()
        query_terms = [term.lower() for term in request.query_text.split() if term.strip()]
        scored = []
        for item in items:
            text = f"{item.title} {item.body_text}".lower()
            matches = [term for term in query_terms if term in text]
            if query_terms and not matches:
                continue
            score = len(matches) / max(len(query_terms), 1)
            scored.append((min(1.0, score), item, [f"keyword_match:{term}" for term in matches]))

        scored.sort(key=lambda v: v[0], reverse=True)
        results: list[RetrievalResult] = []
        for score, item, rationale in scored[: request.limit]:
            results.append(
                RetrievalResult(
                    block=ReusableBlockResponse.model_validate(item),
                    relevance_score=round(score, 4),
                    confidence=round(math.sqrt(score), 4),
                    backend_name=self.backend_name,
                    normalized_score=round(score, 4),
                    provenance=BlockProvenance(
                        block_id=item.id,
                        block_key=item.block_key,
                        category=item.category,
                        source_document_id=item.document_id,
                        provenance_json={**item.provenance_json, "backend": self.backend_name},
                    ),
                    rationale=rationale,
                )
            )
        return results
