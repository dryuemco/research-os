from __future__ import annotations

import hashlib
from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.common.enums import (
    ExecutionJobStatus,
    ExecutionRunStatus,
    ExecutionStatus,
    ProviderErrorType,
    ProviderTraceStatus,
    TaskType,
)
from app.domain.execution_orchestrator.runtime_models import (
    ExecutionJob,
    ExecutionRun,
    ProviderExecutionTrace,
)
from app.providers.base import ProviderExecutionContext, ProviderExecutionError, ProviderRequest
from app.providers.registry import ProviderRegistry, build_default_provider_registry
from app.schemas.audit import AuditEventSchema
from app.schemas.provider import QuotaPolicyEvaluationRequest
from app.schemas.routing import ModelRoutingRequest
from app.schemas.runtime_execution import (
    ExecutionTaskRequest,
    RoutingQuotaPreviewRequest,
    RoutingQuotaPreviewResponse,
)
from app.services.audit_service import AuditService
from app.services.model_routing_service import ModelRoutingService
from app.services.quota_policy_service import QuotaPolicyService


class ExecutionRuntimeService:
    def __init__(
        self,
        db: Session,
        provider_registry: ProviderRegistry | None = None,
        routing_service: ModelRoutingService | None = None,
    ) -> None:
        self.db = db
        self.audit = AuditService(db)
        self.provider_registry = provider_registry or build_default_provider_registry()
        self.routing_service = routing_service or ModelRoutingService.from_config()
        self.quota_service = QuotaPolicyService(db)

    def submit_task(self, request: ExecutionTaskRequest) -> ExecutionRun:
        if request.requires_human_approval and not request.human_approved:
            raise ValueError("Human approval required before runtime execution")

        routing = self._resolve_routing(
            task_type=request.task_type,
            approved_providers=request.approved_providers,
            preferred_provider=request.preferred_provider,
            preferred_model=request.preferred_model,
            local_only=request.local_only,
            sensitive_data=request.sensitive_data,
            budget_tier=request.budget_tier,
        )
        run = ExecutionRun(
            execution_plan_id=request.execution_plan_id,
            coding_work_unit_id=request.coding_work_unit_id,
            task_type=request.task_type,
            purpose=request.purpose,
            status=ExecutionRunStatus.QUEUED,
            routing_policy_version=routing.policy_version,
            selected_provider=routing.selected_provider,
            selected_model=routing.selected_model,
            fallback_chain=request.fallback_chain or routing.fallback_chain,
            approved_providers=request.approved_providers,
            local_only=request.local_only,
            sensitive_data=request.sensitive_data,
            requires_human_approval=request.requires_human_approval,
            budget_tier=request.budget_tier,
            max_attempts=request.retry_policy.max_attempts,
            timeout_seconds=request.retry_policy.max_backoff_seconds,
            input_payload={
                "prompt": request.prompt,
                "metadata": request.metadata,
                "budget_policy": request.budget_policy.model_dump(mode="json"),
                "retry_policy": request.retry_policy.model_dump(mode="json"),
            },
            checkpoint_payload={"step": "submitted"},
            last_successful_step="submitted",
        )
        self.db.add(run)
        self.db.flush()

        job = ExecutionJob(
            run_id=run.id,
            status=ExecutionJobStatus.QUEUED,
            idempotency_key=f"run:{run.id}:attempt:0",
        )
        self.db.add(job)
        self._emit_transition(run, "execution_run_submitted", {"job_id": job.id})
        self.db.flush()
        return run

    def execute_run(self, run_id: str) -> ExecutionRun:
        run = self._get_run(run_id)
        if run.status in {ExecutionRunStatus.SUCCEEDED, ExecutionRunStatus.RUNNING}:
            return run

        run.status = ExecutionRunStatus.RUNNING
        run.attempt_count += 1
        run.checkpoint_payload = {"step": "provider_invocation_started"}
        self._emit_transition(run, "execution_run_started", {"attempt": run.attempt_count})
        self.db.flush()

        provider_name = run.selected_provider or ""
        prompt = str(run.input_payload.get("prompt", ""))
        metadata = dict(run.input_payload.get("metadata", {}))
        budget_policy = run.input_payload.get("budget_policy", {})

        quota_decision = self.quota_service.evaluate(
            QuotaPolicyEvaluationRequest(
                provider_name=provider_name,
                account_ref="default",
                model_name=run.selected_model or "general",
                projected_spend=0.0,
                budget_policy=budget_policy,
            ),
            actor_id="execution_runtime",
        )
        if quota_decision.status == ExecutionStatus.PAUSE:
            run.status = ExecutionRunStatus.PAUSED
            run.pause_reason = (
                quota_decision.pause_reason.value if quota_decision.pause_reason else None
            )
            run.last_error_type = ProviderErrorType.QUOTA_EXCEEDED
            run.checkpoint_payload = {"step": "paused_before_provider_call"}
            self._emit_transition(
                run,
                "execution_run_paused",
                {"reason": run.pause_reason, "rationale": quota_decision.rationale},
            )
            self.db.flush()
            return run
        if quota_decision.status == ExecutionStatus.REROUTE and quota_decision.reroute_provider:
            run.selected_provider = quota_decision.reroute_provider

        try:
            result = self._invoke_provider(run, prompt, metadata)
            run.result_payload = {
                "content": result.content,
                "usage": result.usage,
                "raw_payload": result.raw_payload,
            }
            self._write_trace(
                run,
                status=ProviderTraceStatus.SUCCEEDED,
                prompt=prompt,
                metadata=metadata,
                response=result,
            )
            run.status = ExecutionRunStatus.SUCCEEDED
            run.last_successful_step = "provider_response_persisted"
            run.checkpoint_payload = {"step": "provider_response_persisted"}
            self._emit_transition(
                run,
                "execution_run_succeeded",
                {"provider": result.provider_name},
            )
            self._mark_job_done(run.id)
        except ProviderExecutionError as exc:
            self._handle_provider_error(run, exc, prompt, metadata)

        self.db.flush()
        return run

    def retry_run(self, run_id: str, reason: str) -> ExecutionRun:
        run = self._get_run(run_id)
        if run.status not in {ExecutionRunStatus.FAILED, ExecutionRunStatus.PAUSED}:
            raise ValueError("Only failed or paused runs can be retried")
        run.status = ExecutionRunStatus.QUEUED
        run.pause_reason = None
        run.failure_reason = reason
        job = ExecutionJob(
            run_id=run.id,
            status=ExecutionJobStatus.QUEUED,
            idempotency_key=f"run:{run.id}:attempt:{run.attempt_count}",
        )
        self.db.add(job)
        self._emit_transition(run, "execution_run_retried", {"reason": reason})
        self.db.flush()
        return run

    def resume_run(self, run_id: str, reason: str) -> ExecutionRun:
        run = self._get_run(run_id)
        if run.status != ExecutionRunStatus.PAUSED:
            raise ValueError("Only paused runs can be resumed")
        run.status = ExecutionRunStatus.QUEUED
        run.pause_reason = None
        run.failure_reason = reason
        job = ExecutionJob(
            run_id=run.id,
            status=ExecutionJobStatus.QUEUED,
            idempotency_key=f"run:{run.id}:resume:{run.attempt_count}",
        )
        self.db.add(job)
        self._emit_transition(run, "execution_run_resumed", {"reason": reason})
        self.db.flush()
        return run

    def preview_routing_and_quota(
        self, request: RoutingQuotaPreviewRequest
    ) -> RoutingQuotaPreviewResponse:
        routing = self._resolve_routing(
            task_type=request.task_type,
            approved_providers=request.approved_providers,
            preferred_provider=request.preferred_provider,
            preferred_model=request.preferred_model,
            local_only=request.local_only,
            sensitive_data=request.sensitive_data,
            budget_tier=request.budget_tier,
        )
        decision = self.quota_service.evaluate(
            QuotaPolicyEvaluationRequest(
                provider_name=routing.selected_provider,
                account_ref="default",
                model_name=routing.selected_model,
                projected_spend=request.projected_spend,
                budget_policy=request.budget_policy,
            ),
            actor_id="execution_runtime_preview",
        )
        return RoutingQuotaPreviewResponse(
            selected_provider=routing.selected_provider,
            selected_model=routing.selected_model,
            fallback_chain=routing.fallback_chain,
            quota_status=decision.status.value,
            pause_reason=decision.pause_reason.value if decision.pause_reason else None,
            reroute_provider=decision.reroute_provider,
            rationale=decision.rationale,
        )

    def list_traces(self, run_id: str | None = None) -> list[ProviderExecutionTrace]:
        stmt = select(ProviderExecutionTrace).order_by(ProviderExecutionTrace.created_at.desc())
        if run_id:
            stmt = stmt.where(ProviderExecutionTrace.run_id == run_id)
        return self.db.scalars(stmt.limit(100)).all()

    def process_next_job(self) -> ExecutionJob | None:
        job = self.db.scalar(
            select(ExecutionJob)
            .where(ExecutionJob.status == ExecutionJobStatus.QUEUED)
            .order_by(ExecutionJob.created_at.asc())
        )
        if job is None:
            return None

        job.status = ExecutionJobStatus.RUNNING
        job.attempts += 1
        self.db.add(job)
        self.db.flush()
        try:
            self.execute_run(job.run_id)
            job.status = ExecutionJobStatus.DONE
            job.last_error = None
        except ValueError as exc:
            job.status = ExecutionJobStatus.FAILED
            job.last_error = str(exc)
        self.db.add(job)
        self.db.flush()
        return job

    def _invoke_provider(self, run: ExecutionRun, prompt: str, metadata: dict) -> object:
        provider = self.provider_registry.get(run.selected_provider or "")
        if run.local_only and not provider.capabilities.local_only:
            raise ProviderExecutionError(
                ProviderErrorType.POLICY_REJECTION,
                "selected provider does not satisfy local_only restriction",
                False,
            )
        if run.sensitive_data and not provider.capabilities.supports_sensitive_data:
            raise ProviderExecutionError(
                ProviderErrorType.POLICY_REJECTION,
                "selected provider disallowed for sensitive data",
                False,
            )

        request = ProviderRequest(
            task_type=run.task_type,
            purpose=run.purpose,
            prompt=prompt,
            model_name=run.selected_model or "general",
            timeout_seconds=run.timeout_seconds,
            metadata=metadata,
        )
        context = ProviderExecutionContext(
            run_id=run.id,
            attempt_number=run.attempt_count,
            approved_providers=run.approved_providers,
            sensitive_data=run.sensitive_data,
            local_only=run.local_only,
        )
        return provider.generate(request, context)

    def _handle_provider_error(
        self,
        run: ExecutionRun,
        exc: ProviderExecutionError,
        prompt: str,
        metadata: dict,
    ) -> None:
        fallback_trace_id = self._write_trace(
            run,
            status=ProviderTraceStatus.FAILED,
            prompt=prompt,
            metadata=metadata,
            error=exc,
        )
        run.last_error_type = exc.error_type
        run.failure_reason = str(exc)

        can_retry = exc.retryable and run.attempt_count < run.max_attempts
        if can_retry:
            run.status = ExecutionRunStatus.WAITING_RETRY
            run.next_retry_at = (datetime.now(UTC) + timedelta(seconds=5)).isoformat()
            self._emit_transition(
                run,
                "execution_run_retry_scheduled",
                {"error_type": exc.error_type.value},
            )
            return

        fallback_provider = next(
            (
                provider
                for provider in run.fallback_chain
                if provider and provider != run.selected_provider
            ),
            None,
        )
        if fallback_provider:
            run.selected_provider = fallback_provider
            run.status = ExecutionRunStatus.QUEUED
            self._emit_transition(
                run,
                "execution_run_rerouted",
                {"fallback_provider": fallback_provider, "from_trace_id": fallback_trace_id},
            )
            return

        run.status = ExecutionRunStatus.FAILED
        run.checkpoint_payload = {"step": "terminal_failure"}
        self._emit_transition(run, "execution_run_failed", {"error_type": exc.error_type.value})
        self._mark_job_failed(run.id, str(exc))

    def _write_trace(
        self,
        run: ExecutionRun,
        *,
        status: ProviderTraceStatus,
        prompt: str,
        metadata: dict,
        response: object | None = None,
        error: ProviderExecutionError | None = None,
    ) -> str:
        fingerprint = hashlib.sha256(f"{run.id}:{run.attempt_count}:{prompt}".encode()).hexdigest()
        trace = ProviderExecutionTrace(
            run_id=run.id,
            attempt_number=run.attempt_count,
            provider_name=run.selected_provider or "unknown",
            model_name=run.selected_model or "general",
            task_type=run.task_type,
            purpose=run.purpose,
            routing_policy_version=run.routing_policy_version,
            request_fingerprint=fingerprint,
            request_metadata=metadata,
            latency_ms=getattr(response, "latency_ms", None),
            usage_metadata=getattr(response, "usage", {}) if response else {},
            cost_estimate=getattr(response, "cost_estimate", None),
            status=status,
            error_type=error.error_type if error else None,
            error_message=str(error) if error else None,
        )
        self.db.add(trace)
        self.db.flush()
        return trace.id

    def _resolve_routing(
        self,
        *,
        task_type: str,
        approved_providers: list[str],
        preferred_provider: str | None,
        preferred_model: str | None,
        local_only: bool,
        sensitive_data: bool,
        budget_tier: str,
    ):
        try:
            enum_task_type = TaskType(task_type)
        except ValueError:
            enum_task_type = TaskType.SECTION_DRAFT

        routing_request = ModelRoutingRequest(
            task_type=enum_task_type,
            sensitivity="sensitive" if sensitive_data else "standard",
            budget_tier=budget_tier,
            preferred_provider=preferred_provider,
            preferred_model_family=preferred_model,
            approved_providers=approved_providers,
            local_only=local_only,
        )
        decision = self.routing_service.decide(routing_request)
        if decision.selected_provider not in self.provider_registry.list_provider_names():
            decision.selected_provider = "mock-local"
        return decision

    def _emit_transition(self, run: ExecutionRun, event_type: str, payload: dict) -> None:
        self.audit.emit(
            AuditEventSchema(
                event_type=event_type,
                entity_type="execution_run",
                entity_id=run.id,
                actor_type="system",
                actor_id="execution_runtime_service",
                payload=payload,
            )
        )

    def _mark_job_done(self, run_id: str) -> None:
        jobs = self.db.scalars(
            select(ExecutionJob).where(
                ExecutionJob.run_id == run_id,
                ExecutionJob.status == ExecutionJobStatus.RUNNING,
            )
        ).all()
        for job in jobs:
            job.status = ExecutionJobStatus.DONE
            job.last_error = None
            self.db.add(job)

    def _mark_job_failed(self, run_id: str, message: str) -> None:
        jobs = self.db.scalars(
            select(ExecutionJob).where(
                ExecutionJob.run_id == run_id,
                ExecutionJob.status == ExecutionJobStatus.RUNNING,
            )
        ).all()
        for job in jobs:
            job.status = ExecutionJobStatus.FAILED
            job.last_error = message
            self.db.add(job)

    def _get_run(self, run_id: str) -> ExecutionRun:
        run = self.db.get(ExecutionRun, run_id)
        if run is None:
            raise ValueError("Execution run not found")
        return run
