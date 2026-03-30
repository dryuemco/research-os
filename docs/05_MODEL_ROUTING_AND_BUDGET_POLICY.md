# 05 - Model Routing and Budget Policy

## Goal
Support separate writer and reviewer models, provider-agnostic routing, and quota-aware execution.

## Policy dimensions
- task category
- reasoning depth
- context length need
- cost sensitivity
- latency tolerance
- privacy sensitivity
- quota availability
- fallback preference

## Example task classes
- `call_parsing`
- `compliance_extraction`
- `outline_generation`
- `section_writing`
- `critical_review`
- `red_team_review`
- `project_decomposition`
- `coding_planning`
- `code_generation`
- `test_generation`
- `doc_cleanup`

## Example policy behaviour
- Use stronger reasoning models for compliance extraction and red-team review.
- Use cheaper models for document cleanup and formatting tasks.
- Prefer local models for privacy-sensitive draft transformation where quality is acceptable.
- Prefer cloud premium models for final proposal packaging and critical evaluator-style review.

## Quota governor rules
- When quota is near exhaustion, downgrade non-critical tasks first.
- Never silently downgrade a final review pass without recording policy reason.
- When provider quota blocks a task, change task state to `waiting_for_quota`.
- Retry from checkpoint after quota refresh.
- Persist all provider selection decisions.

## Configuration expectations
Model routing must be driven by configuration, not hardcoded constants.
