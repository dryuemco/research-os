from enum import StrEnum


class OpportunityState(StrEnum):
    DISCOVERED = "discovered"
    NORMALIZED = "normalized"
    SCORED = "scored"
    SHORTLISTED = "shortlisted"
    APPROVED = "approved"
    REJECTED = "rejected"
    MONITOR_LATER = "monitor_later"
    IGNORED = "ignored"
    ARCHIVED = "archived"


class ProposalState(StrEnum):
    CREATED = "created"
    STRATEGY_PENDING = "strategy_pending"
    CONCEPT_NOTE_READY = "concept_note_ready"
    DRAFTING = "drafting"
    IN_REVIEW = "in_review"
    REVISION_PENDING = "revision_pending"
    APPROVED_FOR_EXPORT = "approved_for_export"
    ARCHIVED = "archived"


class TaskType(StrEnum):
    CONCEPT_NOTE = "concept_note"
    SECTION_DRAFT = "section_draft"
    SCIENTIFIC_REVIEW = "scientific_review"
    IMPACT_REVIEW = "impact_review"
    IMPLEMENTATION_REVIEW = "implementation_review"
    COMPLIANCE_REVIEW = "compliance_review"
    RED_TEAM_REVIEW = "red_team_review"


class PauseReason(StrEnum):
    QUOTA_EXHAUSTED = "quota_exhausted"
    BUDGET_EXCEEDED = "budget_exceeded"
    PROVIDER_UNAVAILABLE = "provider_unavailable"
    POLICY_BLOCKED = "policy_blocked"


class ExecutionStatus(StrEnum):
    CONTINUE = "continue"
    REROUTE = "reroute"
    PAUSE = "pause"
    FAIL = "fail"


class DecompositionState(StrEnum):
    NOT_STARTED = "not_started"
    DRAFT_GENERATED = "draft_generated"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    SUPERSEDED = "superseded"
    ARCHIVED = "archived"


class TicketStatus(StrEnum):
    CREATED = "created"
    READY = "ready"
    BLOCKED = "blocked"
    APPROVED = "approved"


class CodingTaskState(StrEnum):
    CREATED = "created"
    QUEUED = "queued"
    RUNNING = "running"
    WAITING_FOR_QUOTA = "waiting_for_quota"
    WAITING_FOR_HUMAN_INPUT = "waiting_for_human_input"
    FAILED = "failed"
    COMPLETED = "completed"
    VERIFIED = "verified"
    CLOSED = "closed"


class ActorType(StrEnum):
    SYSTEM = "system"
    USER = "user"
    PROVIDER = "provider"


class ProviderStatus(StrEnum):
    ACTIVE = "active"
    DEGRADED = "degraded"
    DISABLED = "disabled"

class ExecutionRunStatus(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    PAUSED = "paused"
    WAITING_RETRY = "waiting_retry"
    SUCCEEDED = "succeeded"
    FAILED = "failed"


class ExecutionJobStatus(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    DONE = "done"
    FAILED = "failed"


class ProviderErrorType(StrEnum):
    PROVIDER_UNAVAILABLE = "provider_unavailable"
    QUOTA_EXCEEDED = "quota_exceeded"
    TIMEOUT = "timeout"
    INVALID_RESPONSE = "invalid_response"
    VALIDATION_FAILURE = "validation_failure"
    POLICY_REJECTION = "policy_rejection"
    AUTHENTICATION = "authentication"
    UNKNOWN = "unknown"


class ProviderTraceStatus(StrEnum):
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    REROUTED = "rerouted"


class ApprovalStatus(StrEnum):
    DRAFT = "draft"
    APPROVED = "approved"
    REJECTED = "rejected"


class MemoryCategory(StrEnum):
    ORGANIZATION_PROFILE = "organization_profile"
    INFRASTRUCTURE = "infrastructure"
    STAFF_EXPERTISE = "staff_expertise"
    PRIOR_PROJECT = "prior_project"
    PUBLICATION_EVIDENCE = "publication_evidence"
    IMPACT_EVIDENCE = "impact_evidence"
    METHODOLOGY_SNIPPET = "methodology_snippet"
    PARTNER_NOTE = "partner_note"
    REUSABLE_PROPOSAL_BLOCK = "reusable_proposal_block"


class ExportPackageStatus(StrEnum):
    DRAFT = "draft"
    READY_FOR_REVIEW = "ready_for_review"
    APPROVED = "approved"
    SUPERSEDED = "superseded"
    ARCHIVED = "archived"
    FAILED = "failed"


class ExportArtifactType(StrEnum):
    PROPOSAL_NARRATIVE = "proposal_narrative"
    REVIEWER_LOG = "reviewer_log"
    REUSABLE_EVIDENCE = "reusable_evidence"
    DECOMPOSITION_SUMMARY = "decomposition_summary"
    EXPORT_MANIFEST = "export_manifest"
    DELIVERY_MANIFEST = "delivery_manifest"


class ExportArtifactFormat(StrEnum):
    MARKDOWN = "markdown"
    DOCX = "docx"
    PDF = "pdf"
    JSON = "json"



class UserRole(StrEnum):
    RESEARCH_LEAD = "research_lead"
    GRANT_WRITER = "grant_writer"
    REVIEWER = "reviewer"
    TECHNICAL_LEAD = "technical_lead"
    ADMIN = "admin"


class Permission(StrEnum):
    OPPORTUNITY_APPROVE = "opportunity_approve"
    PROPOSAL_STATE_TRANSITION = "proposal_state_transition"
    EXPORT_GENERATE = "export_generate"
    EXPORT_APPROVE = "export_approve"
    EXPORT_DOWNLOAD = "export_download"
    MEMORY_BLOCK_MUTATE = "memory_block_mutate"
    RUNTIME_CONTROL = "runtime_control"
    VIEW_SENSITIVE = "view_sensitive"
