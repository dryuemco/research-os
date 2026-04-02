from __future__ import annotations

from typing import Protocol

from app.schemas.memory import RetrievalQuery, RetrievalResult


class RetrievalBackend(Protocol):
    backend_name: str

    def retrieve(self, request: RetrievalQuery) -> list[RetrievalResult]:
        ...
