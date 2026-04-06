# 06 - Security and Guardrails

## Core guardrails
- human approval for proposal submission
- human approval for protected branch merge
- secret values never logged
- provider credentials stored securely
- network access policies explicit
- audit trail for high-risk actions

## Proposal-side guardrails
- do not assert institutional commitments without human confirmation
- do not fabricate partner capacity
- do not fabricate budgets, ethics approvals, or infrastructure claims
- do not mark a package as submit-ready unless mandatory sections and rule checks pass

## Coding-side guardrails
- do not auto-merge to main
- do not delete migrations without approval
- do not rotate credentials
- do not edit infrastructure deployment settings without explicit request
- do not disable tests to make pipelines pass

## Data handling
- separate raw provider outputs from validated structured data
- mark sensitive artifacts
- log access to proposal packages and execution logs
