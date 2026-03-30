# Research Proposal OS Starter Repository

This repository now contains the first production-credible backend foundation for a Research and Proposal Operating System.

## Included in this first pass
- FastAPI application skeleton
- environment-driven configuration
- PostgreSQL-oriented SQLAlchemy setup
- Alembic migration scaffold
- core domain models for opportunities, proposals, execution tasks, provider quotas, and audit events
- typed Pydantic contracts for core workflows
- provider abstraction interfaces and config-driven routing policy loader
- audited proposal state transition service
- health endpoint
- pytest test harness
- Docker/local bootstrap files

## Repository layout
- `app/api` - API routes and router wiring
- `app/core` - config and logging
- `app/db` - base metadata, model import registry, and sessions
- `app/domain` - domain-specific ORM models and shared enums/mixins
- `app/providers` - provider abstraction contracts and registry
- `app/schemas` - typed contracts for API and workflow payloads
- `app/services` - business services and policy loaders
- `alembic` - migration environment and initial revision scaffold
- `tests` - bootstrap and unit/smoke tests
- `prompts` - versioned prompt assets kept separate from code
- `docs` - design intent plus implementation foundation notes

## Quick start
1. Copy `.env.example` values into a local `.env` if you want local overrides.
2. Run `docker compose up --build` for the API + PostgreSQL stack.
3. Run `make test` for the current test suite.
4. Run `make migrate` to apply Alembic migrations.

## Important guardrails
- Human approval remains mandatory for proposal submission and protected branch merge actions.
- Core business logic stays out of route handlers.
- Prompts remain versioned assets, not embedded orchestration logic.
- Provider routing is configuration-driven to reduce architectural drift.
