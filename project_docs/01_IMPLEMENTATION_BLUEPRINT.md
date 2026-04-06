# 01 - Implementation Blueprint

## Goal
Build an MVP for a Research and Proposal Operating System that supports:

- call discovery and normalization
- user-profile-based matching
- human approval workflow
- proposal drafting and multi-round review
- project decomposition into technical tasks
- quota-aware routing across coding and writing models
- auditability, resumability, and cost control

## Recommended implementation sequence

### Phase 1 - Backend foundation
Implement:
- FastAPI app skeleton
- config management
- PostgreSQL connection
- migrations
- health endpoints
- structured logging
- audit event base model

### Phase 2 - Domain model and persistence
Implement core entities:
- user profile
- interest profile
- opportunity
- opportunity version
- match result
- proposal
- proposal section
- review round
- task graph
- coding task
- provider account
- quota snapshot
- audit event

### Phase 3 - Opportunity ingestion
Implement:
- source adapters
- fetch scheduler
- normalization pipeline
- opportunity diff/versioning
- call metadata extraction
- eligibility field extraction
- deadline parsing
- topic text storage

### Phase 4 - Matching engine
Implement:
- hard filters
- weighted soft scoring
- explanation generation
- ranking API
- approval queue API

### Phase 5 - Proposal factory
Implement:
- call parser service
- compliance extraction service
- proposal outline generator
- section draft generation
- review round orchestration
- stop-condition engine
- final pack assembler

### Phase 6 - Execution orchestrator
Implement:
- free-text project decomposition
- objective-to-task graph conversion
- coding task generation
- provider/model recommendation
- execution queue
- resume-from-checkpoint state

### Phase 7 - Provider routing and quota governor
Implement:
- provider abstraction
- model catalog
- policy-based model selection
- quota tracking
- cost tracking
- cooldown/retry handling
- fallback routing

### Phase 8 - Minimal operator UI or admin endpoints
Implement either:
- lightweight admin pages, or
- API endpoints plus OpenAPI docs

## Architectural boundaries

### Core rule
Business logic must not live inside prompt strings or controllers.

### Suggested packages
- `app/api`
- `app/core`
- `app/db`
- `app/domain`
- `app/services`
- `app/providers`
- `app/workflows`
- `app/prompts`
- `app/schemas`
- `app/tests`

## Key technical choices
- Use JSONB for flexible provider payloads and opportunity metadata.
- Use explicit workflow state enums.
- Use schema validation on all LLM outputs.
- Keep prompts as versioned assets in `prompts/`.
- Store review comments and scorecards separately from proposal text.
- Store generated code task prompts separately from execution logs.

## Non-goals for MVP
- direct auto-submit to Horizon or Erasmus portals
- full consortium CRM
- automatic PR merge
- complex frontend design system
- full billing productization
