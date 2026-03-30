# Research Proposal OS Starter Repository

This repository contains a production-credible backend foundation for a Research and Proposal Operating System (RPOS), including:

- opportunity ingestion, normalization, matching, and approval flows
- proposal factory workspace foundation with concept-note and review-loop orchestration skeleton
- provider-agnostic model routing decisions and quota policy evaluation scaffolding
- auditable workflow transitions and typed contracts for orchestration inputs/outputs

## API slices currently available
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

## Repository layout
- `app/api` - API routes and router wiring
- `app/core` - config and logging
- `app/db` - metadata, model registry, and sessions
- `app/domain` - SQLAlchemy domain models and enums
- `app/schemas` - typed contracts
- `app/services` - business logic services
- `app/providers` - provider interfaces and registry
- `alembic` - migrations
- `prompts` - versioned prompt assets
- `tests` - unit and API smoke tests

## Quick start
1. Copy `.env.example` into `.env` if needed.
2. Run `docker compose up --build`.
3. Run `make migrate`.
4. Run `make seed-dev` (optional).
5. Run `make test`.

## Guardrails
- Human approval is required for high-risk proposal transitions (e.g., approval for export).
- Business logic is service-layer only; routes remain thin.
- Prompt content is loaded from `prompts/` (not hardcoded into orchestration services).
- Model routing and quota decisions are policy-driven and auditable.
