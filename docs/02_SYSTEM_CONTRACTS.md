# 02 - System Contracts

## API design principle
All major services must expose typed contracts. Every LLM-produced structure must be validated before persistence or downstream use.

## Core contracts

### OpportunityNormalized
Required fields:
- `source_program`
- `source_url`
- `external_id`
- `title`
- `summary`
- `full_text`
- `deadline_at`
- `call_status`
- `budget_total`
- `currency`
- `eligibility_notes`
- `expected_outcomes`
- `raw_payload`
- `version_hash`

### MatchRequest
Required fields:
- `user_id`
- `profile_id`
- `opportunity_ids[]`
- `scoring_policy_id`

### MatchResult
Required fields:
- `opportunity_id`
- `hard_filter_pass`
- `hard_filter_reasons[]`
- `scores`
- `total_score`
- `explanations[]`
- `recommended_role`
- `red_flags[]`

### ProposalSpec
Required fields:
- `proposal_id`
- `opportunity_id`
- `template_type`
- `section_order[]`
- `page_limit`
- `mandatory_sections[]`
- `compliance_rules[]`

### ProposalSectionDraft
Required fields:
- `proposal_id`
- `section_key`
- `draft_text`
- `model_provider`
- `model_name`
- `prompt_version`
- `round_number`
- `status`

### ReviewScorecard
Required fields:
- `proposal_id`
- `round_number`
- `reviewer_role`
- `scores`
- `major_issues[]`
- `minor_issues[]`
- `must_fix[]`
- `decision_hint`

### ProjectDecomposition
Required fields:
- `project_id`
- `objectives[]`
- `deliverables[]`
- `milestones[]`
- `tasks[]`
- `dependencies[]`
- `assumptions[]`
- `risks[]`
- `validation_plan[]`

### CodingTask
Required fields:
- `task_id`
- `title`
- `description`
- `acceptance_criteria[]`
- `context_refs[]`
- `provider_policy`
- `recommended_models[]`
- `estimated_cost_band`
- `status`

### ProviderQuotaSnapshot
Required fields:
- `provider_name`
- `account_ref`
- `model_name`
- `window_start`
- `window_end`
- `requests_used`
- `tokens_used`
- `spend_used`
- `status`

### AuditEvent
Required fields:
- `event_type`
- `entity_type`
- `entity_id`
- `actor_type`
- `actor_id`
- `payload`
- `created_at`

## Workflow state enums

### Opportunity state
- discovered
- normalized
- scored
- shortlisted
- approved
- rejected
- archived

### Proposal state
- initialized
- outlined
- drafting
- under_review
- revision_required
- approved_for_packaging
- packaged
- frozen

### Coding task state
- created
- queued
- running
- waiting_for_quota
- waiting_for_human_input
- failed
- completed
- verified
- closed

## Contract rule
No downstream workflow may consume free-form LLM text when a structured contract exists for that step.
