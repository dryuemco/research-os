# 14 - Pilot Hosting Guide (GitHub Pages + Render)

## Architecture
- **GitHub Pages** hosts a static public landing page (`pages/`) with links only.
- **Render Web Service** runs FastAPI API/UI.
- **Render Worker Service** runs `run_operational_loop` scheduler worker.
- **Render PostgreSQL** stores application state.

## Files introduced
- `render.yaml` (Render Blueprint)
- `pages/index.html`
- `pages/site-config.example.js`
- `.github/workflows/deploy-pages.yml`

## Render setup
1. In Render, create a Blueprint from repository root (`render.yaml`).
2. Set required secret env vars in Render dashboard:
   - `INTERNAL_API_KEY`
   - `ARTIFACT_DOWNLOAD_SECRET`
   - `OPENAI_COMPATIBLE_API_KEY` (if used)
   - `ALLOWED_ORIGINS` (comma-separated, include your GitHub Pages origin)
3. Ensure API predeploy migration runs: `alembic upgrade head`.
4. Confirm health check passes at `/health/ready`.

## GitHub Pages setup
1. Ensure workflow permissions allow Pages deploy.
2. Keep `pages/site-config.js` updated with the Render API URL.
3. Enable Pages in repository settings to use GitHub Actions deployment source.

## CORS and split-hosting
- Configure `ALLOWED_ORIGINS` explicitly (no wildcard by default).
- Suggested value format:
  - `https://<org>.github.io,https://<custom-domain-if-any>`

## Smoke test after deploy
1. Open GitHub Pages landing URL.
2. Open “Internal UI” link to Render API `/ui`.
3. Open “API Docs” link to `/docs`.
4. Open “Health” link to `/health/ready`.
5. Trigger operational flow from API docs:
   - `POST /operations/jobs/ingestion`
   - verify `GET /operations/jobs`
   - verify `GET /operations/matching-runs`
   - verify `GET /operations/notifications?user_id=ops-admin`

## Free-tier limitations
- Web/worker cold starts may delay responses.
- Single worker is assumed; scheduler concurrency controls are basic.
- Persistent disk is not guaranteed for local artifact storage on free plans; prefer DB fallback or managed object storage in next phase.

## Recommended next hardening
- Add dedicated object storage adapter (S3-compatible).
- Add notification channels (email/webhook).
- Add readiness probes for worker liveness and queue lag.
