"""Import all ORM models here so Alembic can discover metadata."""

from app.domain.audit_and_observability.models import AuditEvent  # noqa: F401
from app.domain.execution_orchestrator.models import (  # noqa: F401
    CodingTask,
    CodingWorkUnit,
    Deliverable,
    EngineeringTicket,
    ExecutionObjective,
    ExecutionPlan,
    Milestone,
    RiskItem,
    TaskGraph,
    ValidationActivity,
    WorkPackage,
)
from app.domain.execution_orchestrator.runtime_models import (  # noqa: F401
    ExecutionJob,
    ExecutionRun,
    ProviderExecutionTrace,
)
from app.domain.identity_models import User  # noqa: F401
from app.domain.institutional_memory.models import (  # noqa: F401
    CapabilityProfile,
    DocumentSource,
    ExportArtifact,
    ExportPackage,
    MemoryChunk,
    MemoryDocument,
    ReusableEvidenceBlock,
)
from app.domain.opportunity_discovery.models import (  # noqa: F401
    InterestProfile,
    MatchResult,
    Opportunity,
    OpportunityIngestionSnapshot,
    OpportunityVersion,
)
from app.domain.proposal_factory.models import (  # noqa: F401
    Proposal,
    ProposalSection,
    ProposalVersion,
    ReviewComment,
    ReviewRound,
)
from app.domain.provider_routing.models import ProviderAccount, ProviderQuotaSnapshot  # noqa: F401
