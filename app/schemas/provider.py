from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.domain.common.enums import ExecutionStatus, PauseReason


class ProviderQuotaSnapshotSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    provider_name: str
    account_ref: str
    model_name: str
    window_start: datetime
    window_end: datetime
    requests_used: int
    tokens_used: int
    spend_used: float
    status: str


class RetryPolicySchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    max_attempts: int = 2
    initial_backoff_seconds: int = 5
    max_backoff_seconds: int = 60


class BudgetPolicySchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    run_budget_limit: float
    soft_limit_ratio: float = 0.8
    hard_stop_ratio: float = 1.0


class ExecutionPolicySchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    provider_name: str
    model_name: str
    retry_policy: RetryPolicySchema
    budget_policy: BudgetPolicySchema


class QuotaPolicyEvaluationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    provider_name: str
    account_ref: str
    model_name: str
    projected_spend: float
    budget_policy: BudgetPolicySchema


class QuotaPolicyEvaluationDecision(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: ExecutionStatus
    pause_reason: PauseReason | None = None
    reroute_provider: str | None = None
    rationale: list[str] = Field(default_factory=list)
