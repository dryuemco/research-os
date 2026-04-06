# 11 - Pilot Hardening: Auth, Storage, Retrieval, Source Adapters

## What this adds
- internal API key + user context dependency
- role/permission checks for sensitive actions
- user identity model for pilot governance
- retrieval backend abstraction (lexical backend + swap boundary)
- artifact storage abstraction (local filesystem + db fallback)
- source adapter hardening with capability metadata and error taxonomy

## Pilot defaults
- `INTERNAL_API_KEY` required for protected routes
- local/test mode can use header-provided role for bootstrap (`X-User-Role`) if user seed is not yet persisted
- artifact storage defaults to local filesystem under `ARTIFACT_STORAGE_ROOT`

## Security posture
- no autonomous submission
- no unsafe default transition bypasses
- export approval still requires proposal-level human approval
