# 08 - Architecture Foundation for the First Build

## What exists in the starter pack
The repository began as an intent pack: design constraints, workflow contracts, prompt assets, and milestone guidance. It did not include executable application code, configuration, persistence setup, migrations, provider abstractions, or tests.

## What this first implementation adds
- FastAPI backend bootstrap
- environment-driven configuration
- SQLAlchemy data layer
- Alembic migration scaffold
- explicit domain packages aligned to the original design intent
- typed Pydantic contracts for core workflow entities
- provider abstraction interfaces and routing-policy loader
- audited proposal state transition service
- health endpoint
- test harness and local Docker bootstrap

## Architectural stance
This codebase is intentionally shaped as a modular backend foundation rather than a feature-complete product. The design optimises for future extension in the following dimensions:

1. **Funding-program expansion**  
   Opportunity ingestion and normalized schemas are not hardwired to Horizon-only semantics.

2. **Provider expansion**  
   Core provider logic depends on interface contracts and config-driven routing policy rather than vendor-specific conditionals in business services.

3. **Workflow expansion**  
   Explicit workflow enums and audit plumbing are in place so future orchestration engines can add richer state machines without breaking traceability.

4. **Prompt and policy expansion**  
   Prompt assets remain outside business logic. Routing and policy decisions are loaded from config so they can evolve independently.

## Recommended near-term next slices
1. Implement one real opportunity adapter plus normalization/versioning service.
2. Add repository layer abstractions and transactional service methods per domain.
3. Introduce background workflow abstraction (e.g. Celery or Temporal adapter layer) without coupling domain logic to the queue library.
4. Add match scoring policy objects and deterministic scoring engine.
5. Add proposal shell creation API and audited approval endpoints.
6. Add provider call log entity and structured retry/failure model.
