# 15 - Intelligence Layer: Retrieval, Partner Intelligence, Proposal Quality

## Retrieval quality architecture
- Backends:
  - lexical (`LexicalRetrievalBackend`)
  - vector-ready contract (`VectorReadyRetrievalBackend`)
- Orchestrator:
  - `RetrievalService` supports `lexical`, `vector`, and `hybrid` policy modes.
  - Hybrid fusion applies configurable lexical/vector weights and normalized fusion rationale.
- Policy controls (`RetrievalPolicy`):
  - backend mode
  - blending weights
  - category weighting
  - context budget (`max_context_chars`)
  - per-category cap (`max_per_category`)
  - confidence threshold
  - optional approved-only override

## Context assembly improvements
- Purpose-specific task type tagging (`concept_note`, `section_draft`, `decomposition`).
- Missing-context reporting remains explicit and now includes approval-coverage checks.

## Partner intelligence foundation
- `PartnerProfile` stores:
  - capability tags
  - geography metadata
  - programme participation
  - role suitability hints
  - provenance/source metadata
- `PartnerIntelligenceService.fit_preview` provides:
  - capability overlap
  - role suitability
  - geography compatibility
  - complementarity signal
  - rationale + red flags

## Proposal quality foundation
- `ProposalQualityService` aggregates review comments into:
  - grouped/prioritized issue list
  - category-level dimension scores
  - blocker/disagreement summaries
  - persistent red-team blocker detection
  - next-action recommendation (`revise`, `escalate`, `accept_for_export`)

## Extension points
- Plug pgvector/FAISS backend into `VectorReadyRetrievalBackend` contract.
- Add external partner-source adapters while preserving typed partner profile contract.
- Extend quality issue classification with richer evaluator rubric mappings.
