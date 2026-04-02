from __future__ import annotations

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.schemas.memory import RetrievalQuery, RetrievalResult
from app.services.retrieval_backends.base import RetrievalBackend
from app.services.retrieval_backends.lexical import LexicalRetrievalBackend


class RetrievalService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.backend = self._resolve_backend(db)

    def retrieve(self, request: RetrievalQuery) -> list[RetrievalResult]:
        return self.backend.retrieve(request)

    @staticmethod
    def _resolve_backend(db: Session) -> RetrievalBackend:
        settings = get_settings()
        if settings.retrieval_backend == "lexical":
            return LexicalRetrievalBackend(db)
        # fallback to lexical for pilot reliability
        return LexicalRetrievalBackend(db)
