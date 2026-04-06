# Research Proposal OS Starter Repository

This repository contains a production-credible backend foundation for a Research and Proposal Operating System (RPOS), including:

- opportunity ingestion, normalization, matching, and approval flows
- proposal factory workspace foundation with concept-note and review-loop orchestration skeleton
- provider-agnostic model routing decisions and quota policy evaluation scaffolding
- auditable workflow transitions and typed contracts for orchestration inputs/outputs
- project decomposition and coding-handoff planning foundation

## API endpoints in current slice
- `GET /health`
- `POST /opportunities/ingest/dev`
- `POST /opportunities/ingest/dev/fixture`
- `GET /opportunities`
- `GET /opportunities/{opportunity_id}`
- `POST /opportunities/{opportunity_id}/decision`
- `POST /matches/run`
- `GET /matches`
- `POST /proposal-factory/workspaces`
- `GET /proposal-factory/workspaces/{proposal_id}`
- `POST /proposal-factory/concept-note`
- `POST /proposal-factory/sections/draft`
- `POST /proposal-factory/review-rounds`
- `POST /proposal-factory/review-feedback`
- `GET /proposal-factory/workspaces/{proposal_id}/convergence`
- `POST /proposal-factory/routing-preview`
- `POST /proposal-factory/quota-preview`
- `POST /decomposition`
- `GET /decomposition/{plan_id}`
- `GET /decomposition/workspace/{proposal_id}`
- `POST /decomposition/{plan_id}/task-graph`
- `POST /decomposition/{plan_id}/tickets`
- `POST /decomposition/{plan_id}/handoff`
- `POST /decomposition/{plan_id}/decision`
- `GET /decomposition/work-unit/{coding_work_unit_id}/routing-intent`
- `POST /execution-runtime/tasks`
- `GET /execution-runtime/runs/{run_id}`
- `POST /execution-runtime/runs/{run_id}/retry`
- `POST /execution-runtime/runs/{run_id}/resume`
- `POST /execution-runtime/routing-quota-preview`
- `GET /execution-runtime/traces`
- `POST /execution-runtime/jobs/process-next`
- `GET /dashboard/summary`
- `GET /dashboard/opportunities`
- `GET /dashboard/matches`
- `GET /dashboard/proposals`
- `GET /dashboard/decomposition`
- `GET /dashboard/runs`
- `GET /dashboard/audit`
- `POST /memory/sources`
- `POST /memory/documents`
- `GET /memory/documents`
- `POST /memory/blocks`
- `GET /memory/blocks`
- `GET /memory/blocks/{block_id}`
- `PUT /memory/blocks/{block_id}`
- `POST /memory/retrieval/preview`
- `POST /memory/exports/generate`
- `GET /memory/exports`
- `GET /memory/exports/{package_id}`
- `POST /memory/exports/{package_id}/transition`
- `GET /memory/exports/{package_id}/artifacts`
- `POST /memory/exports/artifacts/{artifact_id}/download-token`
- `GET /memory/exports/artifacts/{artifact_id}/download`
- `GET /memory/exports/{package_id}/submission-pack`
- `GET /ui`
- `GET /operations/sources`
- `POST /operations/jobs/ingestion`
- `POST /operations/jobs/ingestion/live`
- `POST /operations/jobs/matching`
- `POST /operations/scheduler/tick`
- `GET /operations/jobs`
- `GET /operations/matching-runs`
- `GET /operations/notifications`
- `POST /operations/notifications/{notification_id}/read`
- `POST /operations/bootstrap/demo`
- `GET /intelligence/retrieval/backends`
- `POST /intelligence/retrieval/preview`
- `POST /intelligence/partners`
- `GET /intelligence/partners`
- `POST /intelligence/partners/fit`
- `GET /intelligence/proposal-quality/{proposal_id}`

## Repository layout
- `app/api` - API routes and router wiring
- `app/core` - config and logging
- `app/db` - metadata, model registry, and sessions
- `app/domain` - SQLAlchemy domain models and enums
- `app/providers` - provider abstraction contracts and registry
- `app/schemas` - typed contracts for API and workflow payloads
- `app/services` - business logic services and policy loaders
- `app/scripts` - local development scripts
- `alembic` - migration environment and revisions
- `tests` - unit and API smoke tests
- `prompts` - versioned prompt assets kept separate from code
- `project_docs` - design intent plus implementation notes
- `docs` - GitHub Pages static publishing directory (landing page only)

## Quick start
1. Copy `.env.example` values into a local `.env` if you want local overrides.
2. Run `docker compose up --build` for the API + PostgreSQL stack.
3. Run `make migrate` to apply Alembic migrations.
4. Run `make seed-dev` to load a full pilot demo dataset (opportunities, profile, partners, memory blocks, matching runs, notifications, and one demo proposal workspace when possible).
5. Run `make test` for the current test suite.

## Production migration requirement (Render)
- Deploys must run database migrations before enabling ingestion/bootstrap writes.
- Required command: `alembic upgrade head`.
- If migrations are not applied, write endpoints may fail with structured `database_schema_missing` errors and `/health/ready` will report degraded migration status.

## Internet-accessible pilot hosting (GitHub Pages + Render)
- Static public entry/dashboard is in `docs/` and published directly from the `main` branch (`/docs` folder) via GitHub Pages branch settings.
- Static dashboard API target is configured in `docs/site-config.js` and defaults to `https://rpos-api.onrender.com`.
- Dashboard frontend is modularized (`docs/app.js` + `docs/js/*`) to keep config, API client, rendering helpers, and page modules separate.
- Stateful backend/worker/database are deployed on Render using `render.yaml`.
- See `project_docs/14_PILOT_HOSTING_GITHUB_PAGES_RENDER.md` for full setup and smoke tests.
- Use `project_docs/16_POST_DEPLOY_TEST_CHECKLIST.md` for post-deploy operator verification.

### Render runtime startup notes
- Web start command should be `python -m app.main` (long-running FastAPI process).
- Docker startup runs `alembic upgrade head` before launching `python -m app.main` via `scripts/docker-entrypoint.sh`.
- The runtime resolves port from Render `PORT` automatically, with local fallback to `APP_PORT` (`8000`).
- `DATABASE_URL` is normalized for SQLAlchemy when hosted platforms provide `postgres://...` URLs.
- Docker runtime uses `CMD ["/workspace/scripts/docker-entrypoint.sh"]` from `Dockerfile`.
- Required Render env vars: `DATABASE_URL`, `INTERNAL_API_KEY`, `ARTIFACT_DOWNLOAD_SECRET` (plus optional `OPENAI_COMPATIBLE_API_KEY` when used).
- Set `APP_ENV=pilot` on Render (avoid `local` in hosted deployments).
- For this pilot Pages setup, set `ALLOWED_ORIGINS=https://dryuemco.github.io` (comma-separate additional origins if needed).
- Optional helper: set `GITHUB_PAGES_URL=https://dryuemco.github.io` to auto-include the Pages origin in CORS evaluation.
- Dashboard and intelligence list endpoints are hardened to return structured empty/degraded payloads (instead of 500) when DB-backed data is unavailable.

## Important guardrails
- Human approval remains mandatory before proposal drafting or submission-related work.
- Human approval is required for high-risk proposal transitions (e.g., approval for export).
- Core business logic stays out of route handlers.
- Prompts remain versioned assets, not embedded orchestration logic.
- Provider routing is configuration-driven to reduce architectural drift.
- Model routing and quota decisions are policy-driven and auditable.
- Every persisted opportunity and proposal state transition emits an audit event.

## Execution runtime notes
- Provider calls are executed via registered adapters (`mock-local` and optional `openai-compatible`) with policy-driven routing.
- Runtime execution is persisted as execution runs/jobs/traces and supports retry, fallback reroute, and pause/resume.
- API submission and execution are separated through a DB-backed background job queue (`execution_jobs`).


## Institutional memory and dashboard notes
- Institutional memory stores canonical documents, chunks, and reusable evidence blocks with approval status/provenance.
- Retrieval is contract-driven and backend-agnostic (currently lightweight keyword scoring).
- Context assembly endpoints provide grounded context packs for concept notes, section drafting, and decomposition.
- `/ui` is an internal operator dashboard for visual inspection; dashboard data is served from real backend endpoints (`/dashboard/*`).


## Export and submission-pack notes
- Export packages are lifecycle-managed (`draft`, `ready_for_review`, `approved`, `superseded`, `archived`, `failed`) and require explicit approval transitions.
- Renderer architecture is policy-driven and format-aware (`markdown` and real `docx` support in this slice).
- DOCX artifacts are generated as real OOXML `.docx` files (zip package with WordprocessingML), not extension-only placeholders.
- Submission pack endpoint assembles artifact metadata + checksums without external portal submission.
- Artifact delivery supports integrity verification, short-lived download tokens, and audited download events.


## Pilot auth and hardening notes
- Protected mutating/sensitive routes require `X-Internal-Api-Key` and `X-User-Id` headers.
- Role-based permission guards are enforced for export approval, runtime control, memory block mutation, and opportunity approval actions.
- Retrieval backend and artifact storage are pluggable via `RETRIEVAL_BACKEND` and `ARTIFACT_STORAGE_BACKEND` settings.
- Export download requires `EXPORT_DOWNLOAD` permission; use `/memory/exports/artifacts/{artifact_id}/download-token` for short-lived tokenized delivery.

## Pilot deployment notes (export delivery)
- Ensure `ARTIFACT_STORAGE_ROOT` exists and is writable by API + worker containers.
- Configure `ARTIFACT_DOWNLOAD_SECRET` per environment and rotate between pilot phases.
- Use `make run-api`, `make run-worker`, `make migrate`, and `make check` for repeatable pilot operations.

## Operational loop notes
- Operational loop jobs are persisted (`operational_job_runs`) and auditable.
- Scheduler can be run with `make run-ops`; due jobs are executed based on `next_run_at`.
- Source ingestion supports fixture-backed pull mode via `OPERATIONAL_SOURCE_FIXTURE_PATH`.
- Notifications are currently in-app/internal and queryable via `/operations/notifications`.

## Demo bootstrap workflow (pilot walkthrough)
Use this when the backend is healthy but mostly empty and you need dashboard-populating demo data.

### 1) Populate demo data (explicit invocation required)
- `make seed-dev` runs `python -m app.scripts.seed_dev_data --confirm`.
- It ingests fixture opportunities, ensures a demo interest profile, partner profiles, memory content, triggers matching, and creates notifications.
- It also attempts to create one proposal workspace from a shortlisted opportunity.

### 2) Reset/reload demo data (optional)
- `make seed-dev-reset` resets demo-tagged profile/matches/notifications/memory/partners and reloads from fixture.

### 3) Fixture-driven ingest from Swagger
- Endpoint: `POST /opportunities/ingest/dev/fixture`
- Default fixture path comes from `OPERATIONAL_SOURCE_FIXTURE_PATH` (default: `./config/dev_source_payloads.example.json`).
- Useful for pilot operator demos directly from API docs without building request JSON manually.

### 4) Live official-source ingestion (Funding & Tenders Portal)
- Canonical live source adapter: `eu_funding_tenders` (EU Funding & Tenders Portal).
- Official source strategy:
  - Horizon Europe and Erasmus+ calls are fetched from the EU Funding & Tenders canonical opportunity feed.
  - Erasmus+ programme pages remain supplementary context, while call discovery remains anchored to Funding & Tenders.
- Trigger endpoint: `POST /operations/jobs/ingestion/live`
- Example body:
  ```json
  {
    "programmes": ["horizon", "erasmus+"],
    "limit": 50,
    "run_matching_after": true
  }
  ```
- The API response includes created/updated/unchanged/failed counts and a sample list of ingested opportunities.

### 5) Minimal endpoint order for demo verification
1. `POST /opportunities/ingest/dev/fixture`
2. `POST /operations/jobs/ingestion/live`
3. `GET /dashboard/summary`
4. `GET /dashboard/opportunities`
5. `GET /dashboard/matches`
6. `GET /dashboard/operations/jobs`
7. `GET /dashboard/operations/notifications`
8. `GET /dashboard/proposals`

If seed data is loaded, these lists/counters should be non-empty. If no data is loaded, endpoints should continue returning clean empty/degraded payloads (not hard errors).

### 6) Swagger verification sequence (production)
1. `GET /health/ready` and confirm `dependencies.migrations.status == "ok"`.
2. `POST /operations/bootstrap/demo` with body:
   ```json
   {"confirm": true, "reset_demo_state": false, "create_demo_proposal": true}
   ```
3. `POST /opportunities/ingest/dev/fixture` (optional fixture reload).
4. `POST /operations/jobs/ingestion/live` with:
   ```json
   {"programmes": ["horizon", "erasmus+"], "limit": 50, "run_matching_after": true}
   ```
5. `GET /dashboard/summary` and `GET /dashboard/opportunities`.

## Intelligence-quality notes
- Retrieval is policy-driven and now supports hybrid orchestration (lexical + vector-ready contract backend).
- Partner intelligence provides typed partner profiles and consortium-fit preview scoring with rationale/red flags.
- Proposal quality summarization aggregates reviewer comments into prioritized evaluator-facing issue signals and next-action recommendations.

## Deployment config notes
- CORS is controlled by `ALLOWED_ORIGINS` (comma-separated); default is closed if unset.
- API docs can be disabled via `DOCS_ENABLED=false` for tighter pilot posture.
- For hosted pilot settings, use `.env.pilot.example` as the template baseline.
