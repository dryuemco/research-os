"""Import all ORM models here so Alembic can discover metadata."""

from app.domain.audit_and_observability.models import AuditEvent  # noqa: F401
from app.domain.execution_orchestrator.models import CodingTask, TaskGraph  # noqa: F401
from app.domain.opportunity_discovery.models import (  # noqa: F401
    InterestProfile,
    MatchResult,
    Opportunity,
    OpportunityVersion,
)
from app.domain.proposal_factory.models import (  # noqa: F401
    Proposal,
    ProposalSection,
    ReviewComment,
    ReviewRound,
)
from app.domain.provider_routing.models import ProviderAccount, ProviderQuotaSnapshot  # noqa: F401
