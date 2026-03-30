from pydantic import BaseModel, ConfigDict, Field


class ProjectDecomposition(BaseModel):
    model_config = ConfigDict(extra="forbid")

    project_id: str
    objectives: list[str] = Field(default_factory=list)
    deliverables: list[str] = Field(default_factory=list)
    milestones: list[str] = Field(default_factory=list)
    tasks: list[dict] = Field(default_factory=list)
    dependencies: list[dict] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)
    validation_plan: list[str] = Field(default_factory=list)


class CodingTaskSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    task_id: str
    title: str
    description: str
    acceptance_criteria: list[str] = Field(default_factory=list)
    context_refs: list[str] = Field(default_factory=list)
    provider_policy: dict = Field(default_factory=dict)
    recommended_models: list[str] = Field(default_factory=list)
    estimated_cost_band: str
    status: str
