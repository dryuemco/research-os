# 09 - Institutional Memory and Dashboard Foundation

## Scope of this iteration
- institutional memory entities (sources, documents, chunks, reusable evidence blocks, capability profile)
- approval-aware retrieval contracts and service
- context assembly for concept note/section drafting/decomposition
- export package preview + persisted package manifest
- internal operator dashboard API and `/ui` page

## Design notes
- Retrieval is provider-agnostic and intentionally simple (keyword scoring) behind service boundaries to allow future vector backend insertion.
- Reusable blocks are approval-gated for retrieval by default.
- Export packaging is structured-manifest first; renderer-specific DOCX/PDF generation is deferred.
- Dashboard is internal-operational and data-backed by API endpoints, not static mock content.
