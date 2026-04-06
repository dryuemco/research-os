# 04 - Codex Runbook

## Purpose
This document tells Codex how to approach implementation work in this repository.

## Startup procedure
1. Read `AGENTS.md`.
2. Read:
   - `project_docs/01_IMPLEMENTATION_BLUEPRINT.md`
   - `project_docs/02_SYSTEM_CONTRACTS.md`
   - `project_docs/03_ACCEPTANCE_CRITERIA.md`
3. Inspect repository structure.
4. Summarize missing bootstrap elements.
5. Propose the smallest useful first implementation slice.

## First tasks for an empty repository
1. Scaffold backend skeleton.
2. Add config loading.
3. Add health endpoint.
4. Add SQLAlchemy or equivalent ORM setup.
5. Add migrations.
6. Add base domain models and schemas.
7. Add test harness.
8. Add Docker and local dev tooling.

## Task execution protocol
For each task:
- identify changed files
- implement minimal slice
- add tests
- run checks
- report result and next dependency

## Prompting preference
Prefer instructions such as:
- "Implement the smallest production-credible version of X"
- "Use typed schemas"
- "Do not add speculative features"
- "Add tests for state transitions and validators"
- "Keep provider logic behind interfaces"

## Review preference
When asked to review:
- inspect for architecture drift
- check schema boundaries
- verify audit logging
- verify failure handling
- verify state machine clarity
- verify tests map to acceptance criteria

## Strong preferences
- no giant monolithic service files
- no business logic in route handlers
- no direct provider calls from UI-facing layers
- no untyped dict-heavy domain logic where schema classes are feasible
- no silently swallowed exceptions
