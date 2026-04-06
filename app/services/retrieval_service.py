from __future__ import annotations

from collections import defaultdict

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.schemas.memory import (
    RetrievalBackendMode,
    RetrievalPolicy,
    RetrievalQuery,
    RetrievalResult,
)
from app.services.retrieval_backends.lexical import LexicalRetrievalBackend
from app.services.retrieval_backends.vector_ready import VectorReadyRetrievalBackend


class RetrievalService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.settings = get_settings()
        self.lexical = LexicalRetrievalBackend(db)
        self.vector = VectorReadyRetrievalBackend()

    def backend_capabilities(self) -> list[dict]:
        return [
            {
                "backend_name": backend.backend_name,
                "supports_semantic": backend.supports_semantic,
                "supports_filters": backend.supports_filters,
                "supports_hybrid_fusion": backend.supports_hybrid_fusion,
            }
            for backend in [self.lexical, self.vector]
        ]

    def retrieve(self, request: RetrievalQuery) -> list[RetrievalResult]:
        policy = request.policy or RetrievalPolicy(
            backend_mode=RetrievalBackendMode(self.settings.retrieval_default_mode),
            lexical_weight=self.settings.retrieval_lexical_weight,
            vector_weight=self.settings.retrieval_vector_weight,
        )
        filters = request.filters.model_copy(
            update={
                "approved_only": (
                    policy.approved_only_override
                    if policy.approved_only_override is not None
                    else request.filters.approved_only
                )
            }
        )
        query = request.model_copy(update={"filters": filters})

        if policy.backend_mode == RetrievalBackendMode.LEXICAL:
            return self._post_process(self.lexical.retrieve(query), query, policy)
        if policy.backend_mode == RetrievalBackendMode.VECTOR:
            return self._post_process(self.vector.retrieve(query), query, policy)

        fused = self._fuse(
            lexical=self.lexical.retrieve(query),
            vector=self.vector.retrieve(query),
            policy=policy,
        )
        return self._post_process(fused, query, policy)

    def _fuse(
        self,
        *,
        lexical: list[RetrievalResult],
        vector: list[RetrievalResult],
        policy: RetrievalPolicy,
    ) -> list[RetrievalResult]:
        fused: dict[str, RetrievalResult] = {}
        backend_scores: defaultdict[str, dict[str, float]] = defaultdict(dict)

        for item in lexical:
            backend_scores[item.block.id]["lexical"] = item.relevance_score
            item.backend_name = "lexical"
            fused[item.block.id] = item

        for item in vector:
            backend_scores[item.block.id]["vector"] = item.relevance_score
            if item.block.id not in fused:
                item.backend_name = "vector_ready"
                fused[item.block.id] = item

        for block_id, item in fused.items():
            lex = backend_scores[block_id].get("lexical", 0.0)
            vec = backend_scores[block_id].get("vector", 0.0)
            blended = (lex * policy.lexical_weight) + (vec * policy.vector_weight)
            item.normalized_score = round(blended, 4)
            item.rationale.append(
                f"fusion:lexical={lex:.3f},vector={vec:.3f},blend={item.normalized_score:.3f}"
            )

        return sorted(fused.values(), key=lambda v: v.normalized_score, reverse=True)

    def _post_process(
        self, items: list[RetrievalResult], request: RetrievalQuery, policy: RetrievalPolicy
    ) -> list[RetrievalResult]:
        selected: list[RetrievalResult] = []
        seen_signatures: set[str] = set()
        by_category: defaultdict = defaultdict(int)
        used_chars = 0

        ranked = sorted(
            items,
            key=lambda v: v.normalized_score or v.relevance_score,
            reverse=True,
        )
        for item in ranked:
            if item.confidence < policy.min_confidence:
                continue
            signature = self._signature(item.block.body_text)
            if signature in seen_signatures:
                item.rationale.append("dedup_skipped")
                continue
            if by_category[item.block.category] >= policy.max_per_category:
                continue
            category_weight = policy.category_weights.get(item.block.category, 1.0)
            weighted_score = (item.normalized_score or item.relevance_score) * category_weight
            item.normalized_score = round(weighted_score, 4)

            projected = used_chars + len(item.block.body_text)
            if projected > policy.max_context_chars:
                continue

            item.selected_reason = (
                f"selected_for_{request.task_type}:score={item.normalized_score:.3f},"
                f"category={item.block.category.value}"
            )
            selected.append(item)
            seen_signatures.add(signature)
            by_category[item.block.category] += 1
            used_chars = projected

            if len(selected) >= request.limit:
                break

        return sorted(selected, key=lambda v: v.normalized_score, reverse=True)

    @staticmethod
    def _signature(text: str) -> str:
        return " ".join(text.lower().split())[:120]
