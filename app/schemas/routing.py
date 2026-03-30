from pydantic import BaseModel, ConfigDict, Field


class TaskRoutingPolicy(BaseModel):
    model_config = ConfigDict(extra="forbid")

    preferred_providers: list[str] = Field(default_factory=list)
    privacy_level: str
    max_cost_band: str


class ModelRoutingPolicy(BaseModel):
    model_config = ConfigDict(extra="forbid")

    policy_version: str
    default_fallback_provider: str
    task_policies: dict[str, TaskRoutingPolicy] = Field(default_factory=dict)
