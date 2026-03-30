from pydantic import BaseModel, ConfigDict, Field

from app.domain.common.enums import TaskType


class ProviderCapabilityMetadata(BaseModel):
    model_config = ConfigDict(extra="forbid")

    provider_name: str
    model_family: str
    task_types: list[TaskType] = Field(default_factory=list)
    supports_sensitive_data: bool = False
    local_only: bool = False


class ModelRoutingRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    task_type: TaskType
    sensitivity: str
    budget_tier: str
    preferred_provider: str | None = None
    preferred_model_family: str | None = None
    approved_providers: list[str] = Field(default_factory=list)
    local_only: bool = False


class ModelRoutingDecision(BaseModel):
    model_config = ConfigDict(extra="forbid")

    policy_version: str
    selected_provider: str
    selected_model: str
    fallback_chain: list[str] = Field(default_factory=list)
    rationale: list[str] = Field(default_factory=list)


class TaskRoutingPolicy(BaseModel):
    model_config = ConfigDict(extra="forbid")

    preferred_providers: list[str] = Field(default_factory=list)
    model_family: str = "general"
    max_cost_band: str
    sensitivity_levels: list[str] = Field(default_factory=lambda: ["standard"])
    fallback_chain: list[str] = Field(default_factory=list)


class ModelRoutingPolicy(BaseModel):
    model_config = ConfigDict(extra="forbid")

    policy_version: str
    default_fallback_provider: str
    task_policies: dict[str, TaskRoutingPolicy] = Field(default_factory=dict)
