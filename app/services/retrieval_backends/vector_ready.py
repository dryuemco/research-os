from __future__ import annotations

from app.schemas.memory import RetrievalQuery, RetrievalResult


class VectorReadyRetrievalBackend:
    """Vector-ready contract backend.

    This backend currently returns no results by default, but keeps a stable
    interface for future pgvector/FAISS integrations.
    """

    backend_name = "vector_ready"
    supports_semantic = True
    supports_filters = True
    supports_hybrid_fusion = True

    def retrieve(self, request: RetrievalQuery) -> list[RetrievalResult]:
        return []
