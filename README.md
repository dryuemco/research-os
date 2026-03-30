# Research Proposal OS Starter Repository

This repository contains a production-credible backend foundation for a Research and Proposal Operating System (RPOS), now extended with the first operational opportunity workflow slice.

## Included in this iteration
- FastAPI application skeleton with dependency-injected services
- PostgreSQL-oriented SQLAlchemy setup and Alembic migrations
- audited opportunity ingestion pipeline with adapter abstraction
- normalized opportunity/version persistence with source snapshots and hash-based change detection
- matching engine v1 with hard filters, weighted scoring, rationale, red flags, recommendation persistence
- opportunity approval/rejection/monitor/ignore state machine with transition validation and audit logging
- thin API routes for ingest -> list -> match -> decision flows
- health endpoint and smoke tests

## Repository layout
- `app/api` - API routes and router wiring
- `app/core` - config and logging
- `app/db` - base metadata, model import registry, and sessions
- `app/domain` - domain-specific ORM models and shared enums/mixins
- `app/providers` - provider abstraction contracts and registry
- `app/schemas` - typed contracts for API and workflow payloads
- `app/services` - business services and policy loaders
- `app/scripts` - local development scripts
- `alembic` - migration environment and revisions
- `tests` - unit and API smoke tests
- `prompts` - versioned prompt assets kept separate from code
- `docs` - design intent plus implementation notes

## API endpoints in current slice
- `GET /health`
- `POST /opportunities/ingest/dev`
- `GET /opportunities`
- `GET /opportunities/{opportunity_id}`
- `POST /opportunities/{opportunity_id}/decision`
- `POST /matches/run`
- `GET /matches`

## Quick start
1. Copy `.env.example` values into a local `.env` if you want local overrides.
2. Run `docker compose up --build` for the API + PostgreSQL stack.
3. Run `make migrate` to apply Alembic migrations.
4. (Optional) Run `make seed-dev` to seed one development interest profile.
5. Run `make test` for the current test suite.

## Important guardrails
- Human approval remains mandatory before proposal drafting or submission-related work.
- Core business logic stays out of route handlers.
- Prompts remain versioned assets, not embedded orchestration logic.
- Provider routing is configuration-driven to reduce architectural drift.
- Every persisted opportunity state transition emits an audit event.
