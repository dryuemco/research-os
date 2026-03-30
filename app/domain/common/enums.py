from enum import StrEnum


class OpportunityState(StrEnum):
    DISCOVERED = "discovered"
    NORMALIZED = "normalized"
    SCORED = "scored"
    SHORTLISTED = "shortlisted"
    APPROVED = "approved"
    REJECTED = "rejected"
    ARCHIVED = "archived"


class ProposalState(StrEnum):
    INITIALIZED = "initialized"
    OUTLINED = "outlined"
    DRAFTING = "drafting"
    UNDER_REVIEW = "under_review"
    REVISION_REQUIRED = "revision_required"
    APPROVED_FOR_PACKAGING = "approved_for_packaging"
    PACKAGED = "packaged"
    FROZEN = "frozen"


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
