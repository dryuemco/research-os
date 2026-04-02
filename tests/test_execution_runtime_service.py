from app.domain.common.enums import ExecutionRunStatus, ProviderErrorType
from app.domain.execution_orchestrator.runtime_models import ProviderExecutionTrace
from app.schemas.provider import BudgetPolicySchema, RetryPolicySchema
from app.schemas.runtime_execution import ExecutionTaskRequest, RoutingQuotaPreviewRequest
from app.services.execution_runtime_service import ExecutionRuntimeService


def _request(**overrides):
    payload = {
        "task_type": "section_draft",
        "purpose": "draft section",
        "prompt": "Write section draft.",
        "approved_providers": ["mock-local"],
        "preferred_provider": "mock-local",
        "fallback_chain": ["mock-local"],
        "budget_policy": BudgetPolicySchema(run_budget_limit=10.0),
        "retry_policy": RetryPolicySchema(max_attempts=2, max_backoff_seconds=10),
    }
    payload.update(overrides)
    return ExecutionTaskRequest(**payload)


def test_submit_and_execute_success(db_session):
    service = ExecutionRuntimeService(db_session)
    run = service.submit_task(_request())
    db_session.commit()

    service.process_next_job()
    db_session.commit()

    refreshed = service._get_run(run.id)
    assert refreshed.status == ExecutionRunStatus.SUCCEEDED
    traces = db_session.query(ProviderExecutionTrace).filter_by(run_id=run.id).all()
    assert len(traces) == 1
    assert traces[0].status.value == "succeeded"


def test_retryable_error_transitions_to_waiting_retry(db_session):
    service = ExecutionRuntimeService(db_session)
    run = service.submit_task(_request(metadata={"force_error": "quota"}))
    db_session.commit()

    service.process_next_job()
    db_session.commit()

    refreshed = service._get_run(run.id)
    assert refreshed.status == ExecutionRunStatus.WAITING_RETRY
    assert refreshed.last_error_type == ProviderErrorType.QUOTA_EXCEEDED


def test_fallback_decision_after_non_retryable_error(db_session):
    service = ExecutionRuntimeService(db_session)
    run = service.submit_task(
        _request(
            metadata={"force_error": "invalid_response"},
            approved_providers=["mock-local", "openai-compatible"],
            fallback_chain=["openai-compatible"],
        )
    )
    db_session.commit()

    service.process_next_job()
    db_session.commit()

    refreshed = service._get_run(run.id)
    assert refreshed.status == ExecutionRunStatus.QUEUED
    assert refreshed.selected_provider == "openai-compatible"


def test_preview_routing_and_quota(db_session):
    service = ExecutionRuntimeService(db_session)
    preview = service.preview_routing_and_quota(
        RoutingQuotaPreviewRequest(
            task_type="section_draft",
            purpose="x",
            approved_providers=["mock-local"],
            preferred_provider="mock-local",
            budget_policy=BudgetPolicySchema(run_budget_limit=1.0),
            projected_spend=0.1,
        )
    )
    assert preview.selected_provider == "mock-local"
    assert preview.quota_status in {"continue", "reroute", "pause"}
