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


class RetrievalService:
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
        scored: list[tuple[float, ReusableEvidenceBlock, list[str]]] = []
        for item in items:
            text = f"{item.title} {item.body_text}".lower()
            matches = [term for term in query_terms if term in text]
            if query_terms and not matches:
                continue
            score = len(matches) / max(len(query_terms), 1)
            tag_bonus = 0.1 if any(tag in item.tags for tag in filters.tags) else 0.0
            final_score = min(1.0, score + tag_bonus)
            rationale = [f"keyword_match:{term}" for term in matches]
            scored.append((final_score, item, rationale))

        scored.sort(key=lambda x: x[0], reverse=True)
        results: list[RetrievalResult] = []
        for score, item, rationale in scored[: request.limit]:
            confidence = math.sqrt(score)
            results.append(
                RetrievalResult(
                    block=ReusableBlockResponse.model_validate(item),
                    relevance_score=round(score, 4),
                    confidence=round(confidence, 4),
                    provenance=BlockProvenance(
                        block_id=item.id,
                        block_key=item.block_key,
                        category=item.category,
                        source_document_id=item.document_id,
                        provenance_json=item.provenance_json,
                    ),
                    rationale=rationale,
                )
            )
        return results
