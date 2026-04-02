from __future__ import annotations

from app.schemas.memory import RetrievalContextAssembly, RetrievalQuery
from app.services.retrieval_service import RetrievalService


class ContextAssemblyService:
    def __init__(self, retrieval: RetrievalService) -> None:
        self.retrieval = retrieval

    def assemble_for_concept_note(self, query: RetrievalQuery) -> RetrievalContextAssembly:
        return self._assemble("concept_note", query)

    def assemble_for_section_draft(self, query: RetrievalQuery) -> RetrievalContextAssembly:
        return self._assemble("section_draft", query)

    def assemble_for_decomposition(self, query: RetrievalQuery) -> RetrievalContextAssembly:
        return self._assemble("decomposition", query)

    def _assemble(self, purpose: str, query: RetrievalQuery) -> RetrievalContextAssembly:
        results = self.retrieval.retrieve(query)
        missing: list[str] = []
        if not results:
            missing.append("No approved institutional evidence matched this query")
        if len(results) < min(query.limit, 3):
            missing.append("Limited evidence coverage for requested context depth")
        return RetrievalContextAssembly(
            purpose=purpose,
            query=query,
            context_blocks=results,
            missing_context=missing,
        )
