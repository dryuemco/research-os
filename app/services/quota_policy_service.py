from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.common.enums import ExecutionStatus, PauseReason
from app.domain.provider_routing.models import ProviderQuotaSnapshot
from app.schemas.audit import AuditEventSchema
from app.schemas.provider import QuotaPolicyEvaluationDecision, QuotaPolicyEvaluationRequest
from app.services.audit_service import AuditService


class QuotaPolicyService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.audit = AuditService(db)

    def evaluate(
        self,
        request: QuotaPolicyEvaluationRequest,
        *,
        actor_type: str = "system",
        actor_id: str = "quota_governor",
    ) -> QuotaPolicyEvaluationDecision:
        latest_snapshot = self.db.scalar(
            select(ProviderQuotaSnapshot)
            .where(
                ProviderQuotaSnapshot.provider_name == request.provider_name,
                ProviderQuotaSnapshot.account_ref == request.account_ref,
                ProviderQuotaSnapshot.model_name == request.model_name,
            )
            .order_by(ProviderQuotaSnapshot.created_at.desc())
        )

        rationale: list[str] = []
        if latest_snapshot and str(latest_snapshot.status).lower() not in {"ok", "active"}:
            decision = QuotaPolicyEvaluationDecision(
                status=ExecutionStatus.PAUSE,
                pause_reason=PauseReason.PROVIDER_UNAVAILABLE,
                rationale=["provider_status_not_ready"],
            )
        else:
            projected_total = (
                float(latest_snapshot.spend_used) if latest_snapshot else 0.0
            ) + request.projected_spend
            soft_limit = (
                request.budget_policy.run_budget_limit * request.budget_policy.soft_limit_ratio
            )
            hard_limit = (
                request.budget_policy.run_budget_limit * request.budget_policy.hard_stop_ratio
            )

            if projected_total >= hard_limit:
                rationale.append("projected_spend_above_hard_limit")
                decision = QuotaPolicyEvaluationDecision(
                    status=ExecutionStatus.PAUSE,
                    pause_reason=PauseReason.BUDGET_EXCEEDED,
                    rationale=rationale,
                )
            elif projected_total >= soft_limit:
                rationale.append("projected_spend_above_soft_limit")
                decision = QuotaPolicyEvaluationDecision(
                    status=ExecutionStatus.REROUTE,
                    reroute_provider="local-fallback",
                    rationale=rationale,
                )
            else:
                decision = QuotaPolicyEvaluationDecision(
                    status=ExecutionStatus.CONTINUE,
                    rationale=["within_budget_and_quota"],
                )

        self.audit.emit(
            AuditEventSchema(
                event_type="quota_policy_evaluated",
                entity_type="provider_quota",
                entity_id=f"{request.provider_name}:{request.account_ref}:{request.model_name}",
                actor_type=actor_type,
                actor_id=actor_id,
                payload={
                    "projected_spend": request.projected_spend,
                    "decision": decision.model_dump(mode="json"),
                },
            )
        )
        self.db.flush()
        return decision
