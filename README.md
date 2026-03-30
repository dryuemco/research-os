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
- `docs` - design intent plus implementation notes

## Quick start
1. Copy `.env.example` values into a local `.env` if you want local overrides.
2. Run `docker compose up --build` for the API + PostgreSQL stack.
3. Run `make migrate` to apply Alembic migrations.
4. (Optional) Run `make seed-dev` to seed one development interest profile.
5. Run `make test` for the current test suite.

## Important guardrails
- Human approval remains mandatory before proposal drafting or submission-related work.
- Human approval is required for high-risk proposal transitions (e.g., approval for export).
- Core business logic stays out of route handlers.
- Prompts remain versioned assets, not embedded orchestration logic.
- Provider routing is configuration-driven to reduce architectural drift.
- Model routing and quota decisions are policy-driven and auditable.
- Every persisted opportunity and proposal state transition emits an audit event.