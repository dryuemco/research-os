# 12 - Export Delivery Hardening (Pilot Iteration)

## What this iteration adds
- Policy-driven renderer selection with format preferences.
- Real DOCX generation path using OOXML package generation.
- Artifact storage hardening (byte-oriented storage, checksum verification, safer locators).
- Tokenized download support with permission checks.
- Download/audit observability for export artifacts.

## Renderer policy
`RenderRequest.render_policy` controls:
- `preferred_formats`
- section inclusion (`section_keys`)
- reviewer/decomposition/evidence toggles
- delivery manifest inclusion toggle

Current supported formats:
- `markdown`
- `docx`
- `json` (delivery manifest)

## Storage/integrity
- Artifacts are written through `ArtifactStorage` adapters.
- SHA-256 checksum is persisted and re-verified on read.
- Local filesystem adapter returns relative locators and rejects traversal attempts.
- Stale locator fallback uses persisted `content_base64` payload for pilot resiliency.

## Download flow
1. Client obtains token: `POST /memory/exports/artifacts/{artifact_id}/download-token`.
2. Client downloads file: `GET /memory/exports/artifacts/{artifact_id}/download?token=...`.
3. Service validates token scope/expiry, re-verifies checksum, returns bytes with content headers.
4. Download is emitted as `export_artifact_downloaded` audit event.

## Pilot operations
- Set `ARTIFACT_DOWNLOAD_SECRET` per environment.
- Keep `ARTIFACT_DOWNLOAD_TTL_SECONDS` short (default 300s).
- Mount persistent artifact storage for API/worker in Compose (`/workspace/artifacts`).
- Use `GET /health` to inspect DB and artifact-storage dependency status.
