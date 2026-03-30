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
