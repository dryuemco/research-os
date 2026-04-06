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
        query_with_purpose = query.model_copy(update={"task_type": purpose})
        results = self.retrieval.retrieve(query_with_purpose)
        missing: list[str] = []
        if not results:
            missing.append("No approved institutional evidence matched this query")
        if len(results) < min(query_with_purpose.limit, 3):
            missing.append("Limited evidence coverage for requested context depth")
        if query_with_purpose.filters.approved_only and any(
            r.block.approval_status.value != "approved" for r in results
        ):
            missing.append("Some context blocks are not approved evidence")
        return RetrievalContextAssembly(
            purpose=purpose,
            query=query_with_purpose,
            context_blocks=results,
            missing_context=missing,
        )
