from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.domain.audit_and_observability.models import AuditEvent
from app.domain.execution_orchestrator.models import ExecutionPlan
from app.domain.execution_orchestrator.runtime_models import ExecutionRun
from app.domain.institutional_memory.models import ExportPackage, ReusableEvidenceBlock
from app.domain.operations.models import MatchingRun, Notification, OperationalJobRun
from app.domain.opportunity_discovery.models import MatchResult, Opportunity, TargetCall
from app.domain.partner_intelligence.models import PartnerProfile
from app.domain.proposal_factory.models import Proposal


class DashboardService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def summary(self) -> dict:
        return {
            "opportunities": self.db.scalar(select(func.count()).select_from(Opportunity)) or 0,
            "matches": self.db.scalar(select(func.count()).select_from(MatchResult)) or 0,
            "proposals": self.db.scalar(select(func.count()).select_from(Proposal)) or 0,
            "execution_plans": self.db.scalar(select(func.count()).select_from(ExecutionPlan)) or 0,
            "execution_runs": self.db.scalar(select(func.count()).select_from(ExecutionRun)) or 0,
            "memory_blocks": (
                self.db.scalar(select(func.count()).select_from(ReusableEvidenceBlock)) or 0
            ),
            "export_packages": self.db.scalar(select(func.count()).select_from(ExportPackage)) or 0,
            "operational_job_runs": (
                self.db.scalar(select(func.count()).select_from(OperationalJobRun)) or 0
            ),
            "matching_runs": self.db.scalar(select(func.count()).select_from(MatchingRun)) or 0,
            "notifications": self.db.scalar(select(func.count()).select_from(Notification)) or 0,
            "partner_profiles": (
                self.db.scalar(select(func.count()).select_from(PartnerProfile)) or 0
            ),
            "target_calls": self.db.scalar(select(func.count()).select_from(TargetCall)) or 0,
        }

    def audit_timeline(self, *, limit: int = 50, offset: int = 0) -> list[AuditEvent]:
        return self.db.scalars(
            select(AuditEvent).order_by(AuditEvent.created_at.desc()).offset(offset).limit(limit)
        ).all()
