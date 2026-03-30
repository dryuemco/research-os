from datetime import UTC, datetime, timedelta

from app.domain.common.enums import ExecutionStatus, TaskType
from app.domain.provider_routing.models import ProviderQuotaSnapshot
from app.schemas.provider import BudgetPolicySchema, QuotaPolicyEvaluationRequest
from app.schemas.routing import ModelRoutingRequest
from app.services.model_routing_service import ModelRoutingService
from app.services.quota_policy_service import QuotaPolicyService


def test_model_routing_selects_first_eligible_provider() -> None:
    service = ModelRoutingService.from_config()
    decision = service.decide(
        ModelRoutingRequest(
            task_type=TaskType.CONCEPT_NOTE,
            sensitivity="standard",
            budget_tier="medium",
            approved_providers=["openai", "anthropic"],
        )
    )
    assert decision.selected_provider == "openai"
    assert decision.policy_version == "v2"


def test_quota_policy_triggers_pause_on_hard_limit(db_session) -> None:
    snapshot = ProviderQuotaSnapshot(
        provider_name="openai",
        account_ref="acc-1",
        model_name="writer-large",
        window_start=datetime.now(UTC),
        window_end=datetime.now(UTC) + timedelta(hours=1),
        requests_used=10,
        tokens_used=1000,
        spend_used=95,
        status="ok",
        raw_payload={},
    )
    db_session.add(snapshot)
    db_session.flush()

    decision = QuotaPolicyService(db_session).evaluate(
        QuotaPolicyEvaluationRequest(
            provider_name="openai",
            account_ref="acc-1",
            model_name="writer-large",
            projected_spend=10,
            budget_policy=BudgetPolicySchema(
                run_budget_limit=100, soft_limit_ratio=0.8, hard_stop_ratio=1.0
            ),
        )
    )

    assert decision.status == ExecutionStatus.PAUSE
