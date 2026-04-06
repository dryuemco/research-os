from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.domain.common.enums import ExecutionRunStatus, ProviderErrorType, ProviderTraceStatus
from app.schemas.provider import BudgetPolicySchema, RetryPolicySchema


class ExecutionTaskRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    task_type: str
    purpose: str
    prompt: str
    approved_providers: list[str] = Field(default_factory=list)
    preferred_provider: str | None = None
    preferred_model: str | None = None
    fallback_chain: list[str] = Field(default_factory=list)
    local_only: bool = False
    sensitive_data: bool = False
    requires_human_approval: bool = False
    human_approved: bool = False
    budget_tier: str = "standard"
    execution_plan_id: str | None = None
    coding_work_unit_id: str | None = None
    retry_policy: RetryPolicySchema = Field(default_factory=RetryPolicySchema)
    budget_policy: BudgetPolicySchema
    metadata: dict = Field(default_factory=dict)


class ExecutionRunResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    status: ExecutionRunStatus
    task_type: str
    purpose: str
    selected_provider: str | None = None
    selected_model: str | None = None
    attempt_count: int
    max_attempts: int
    pause_reason: str | None = None
    failure_reason: str | None = None
    last_error_type: ProviderErrorType | None = None
    next_retry_at: str | None = None
    checkpoint_payload: dict
    last_successful_step: str | None = None
    created_at: datetime
    updated_at: datetime


class RetryRunRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    reason: str = "manual_retry"


class ResumeRunRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    reason: str = "manual_resume"


class RoutingQuotaPreviewRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    task_type: str
    purpose: str
    approved_providers: list[str] = Field(default_factory=list)
    preferred_provider: str | None = None
    preferred_model: str | None = None
    fallback_chain: list[str] = Field(default_factory=list)
    local_only: bool = False
    sensitive_data: bool = False
    budget_tier: str = "standard"
    projected_spend: float = 0.0
    budget_policy: BudgetPolicySchema


class RoutingQuotaPreviewResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    selected_provider: str
    selected_model: str
    fallback_chain: list[str]
    quota_status: str
    pause_reason: str | None = None
    reroute_provider: str | None = None
    rationale: list[str] = Field(default_factory=list)


class ProviderTraceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    run_id: str
    attempt_number: int
    provider_name: str
    model_name: str
    task_type: str
    purpose: str
    latency_ms: int | None
    status: ProviderTraceStatus
    error_type: ProviderErrorType | None
    error_message: str | None
    created_at: datetime
