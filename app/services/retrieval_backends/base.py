from __future__ import annotations

from typing import Protocol

from app.schemas.memory import RetrievalQuery, RetrievalResult


class RetrievalBackendCapability(Protocol):
    backend_name: str
    supports_semantic: bool
    supports_filters: bool
    supports_hybrid_fusion: bool


class RetrievalBackend(Protocol):
    backend_name: str
    supports_semantic: bool
    supports_filters: bool
    supports_hybrid_fusion: bool

    def retrieve(self, request: RetrievalQuery) -> list[RetrievalResult]:
        ...
