# 03 - Acceptance Criteria

## Platform-wide acceptance criteria
- Every persisted domain entity has a migration and a typed schema.
- Every state transition is audited.
- Every provider call is logged with timing, model, and outcome metadata.
- Every LLM output that affects workflow state is schema-validated.
- Retryable failures are distinguishable from terminal failures.
- Long-running workflows can resume from the last checkpoint.

## Module acceptance criteria

### Opportunity ingestion
- A source adapter can fetch, normalize, and version at least one call source.
- Duplicate opportunities are recognized by stable external identity or hash rules.
- Deadline and source URL are captured and queryable.
- Re-ingestion of changed source text creates a new version.

### Matching engine
- Hard filters can exclude opportunities deterministically.
- Soft scoring is reproducible with a named policy version.
- Result explanations list score drivers and red flags.
- Top-ranked calls can be approved or rejected by a user.

### Proposal factory
- The system can create a proposal shell from an approved opportunity.
- Mandatory sections are created from the template.
- At least one draft-review-revision loop completes successfully.
- Reviewer comments are stored separately from draft text.
- Stop conditions can end the loop before the maximum rounds.
- A final export package can be generated.

### Execution orchestrator
- Free-text project descriptions can be decomposed into tasks, deliverables, and milestones.
- Coding tasks include acceptance criteria and context references.
- Execution can pause on quota limits and resume later.
- Execution logs show provider, model, prompt version, and task outcome.

### Provider routing and quota governor
- Provider policies can choose models based on task type.
- Quota snapshots can block or defer tasks.
- Fallback routing can redirect a task to a secondary model policy.
- Spend and usage metrics are queryable.

## Test expectations
- Unit tests for scoring, state transitions, validators, and routing policies.
- Integration tests for at least one ingestion flow and one proposal workflow.
- Contract tests for structured LLM outputs.
- Smoke test for queue resume after simulated quota exhaustion.
