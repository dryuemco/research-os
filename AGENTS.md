# AGENTS.md

## Project purpose
This repository implements a multi-agent Research and Proposal Operating System with two core modules:

1. Opportunity discovery, matching, proposal drafting, review, and submission-readiness for EU Horizon and Erasmus+ calls.
2. Project-to-execution orchestration that decomposes approved or candidate projects into technical tasks, code-generation workflows, validation loops, and quota-aware coding-agent execution.

The system is human-in-the-loop by default. It may automate drafting, review, scoring, task decomposition, and code patch generation, but must not assume legal, financial, or institutional authority to submit proposals or merge risky code changes without explicit human approval.

## Primary product principles
- Human approval on high-risk actions.
- Traceability for every major decision.
- Provider-agnostic model routing.
- Compliance-first behaviour for funding calls.
- Deterministic outputs where possible via schemas and validators.
- Fallback and resume support for long-running workflows.
- Cost and quota awareness for cloud model providers.

## Working rules for Codex
- Read `project_docs/01_IMPLEMENTATION_BLUEPRINT.md` first.
- Then read `project_docs/02_SYSTEM_CONTRACTS.md` and `project_docs/03_ACCEPTANCE_CRITERIA.md`.
- Prefer incremental, testable changes over large rewrites.
- Before adding new dependencies, document why they are needed in the relevant module README or code comments.
- Keep all business logic behind clearly named services.
- Do not hardcode provider-specific assumptions into core orchestration code.
- Use typed interfaces and schema validation for all agent inputs and outputs.
- Keep prompts under version control and separate from orchestration logic.
- Every workflow step that changes persisted state must emit an audit event.
- Every external call must have retry, timeout, and structured error handling.
- Avoid hidden magic. Favour explicit configuration.
- Generate tests for new services, routers, validators, and workflow transitions.

## Engineering conventions
- Python backend with FastAPI.
- PostgreSQL as the source of truth.
- Redis for queueing/cache if needed.
- Background workflow orchestration through Temporal, Celery, or an equivalent pluggable abstraction.
- Frontend can be deferred in MVP; API-first design is preferred.
- Use Pydantic models or equivalent schema validation for all API contracts.
- Keep domain modules separate:
  - `opportunity_discovery`
  - `proposal_factory`
  - `execution_orchestrator`
  - `provider_routing`
  - `quota_governor`
  - `audit_and_observability`

## Safety and approval boundaries
Codex may implement:
- ingestion pipelines
- parsers
- ranking services
- draft generators
- review loops
- API endpoints
- data models
- orchestration logic
- dashboard backends
- coding task routers
- quota tracking

Codex must not silently implement:
- automatic proposal submission to third-party portals
- irreversible data deletion
- production credential rotation
- automatic code merge to protected branches
- uncontrolled internet access policies
- unrestricted shell execution in deployment scripts

## Delivery expectation
For each substantial task:
1. State what files will change.
2. Implement the smallest viable slice.
3. Add or update tests.
4. Run relevant checks.
5. Summarize what remains.

## Repository bootstrap expectation
If the repository is initially empty, scaffold:
- backend application skeleton
- core domain packages
- config package
- migrations folder
- tests folder
- prompts folder
- docs folder
- sample `.env.example`
- `docker-compose.yml`
- `Makefile`
- `pyproject.toml`
