from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.domain.common.enums import DecompositionState, TicketStatus


class PlanningPolicy(BaseModel):
    model_config = ConfigDict(extra="forbid")

    task_granularity: str
    decomposition_depth: int
    ticket_detail_level: str
    provider_sensitivity_classification: str
    complexity_buckets: list[str] = Field(default_factory=lambda: ["low", "medium", "high"])
    repository_risk_tier: str
    human_approval_threshold: str


class ProposalContextSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    proposal_id: str
    title: str
    concept_summary: str
    key_constraints: list[str] = Field(default_factory=list)


class DecompositionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    proposal_id: str
    plan_name: str
    context: ProposalContextSummary
    policy: PlanningPolicy


class AcceptanceCriteriaBlock(BaseModel):
    model_config = ConfigDict(extra="forbid")

    criteria: list[str] = Field(default_factory=list)


class ValidationPlanBlock(BaseModel):
    model_config = ConfigDict(extra="forbid")

    checks: list[str] = Field(default_factory=list)
    evidence_required: list[str] = Field(default_factory=list)


class ObjectiveOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    objective_code: str
    title: str
    description: str
    success_metrics: list[str] = Field(default_factory=list)


class WorkPackageOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    wp_code: str
    title: str
    objective_ref: str
    description: str


class TaskOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    task_code: str
    work_package_ref: str
    title: str
    description: str
    priority: str
    owner_role: str
    required_capabilities: list[str] = Field(default_factory=list)
    required_context: list[str] = Field(default_factory=list)
    acceptance_criteria: AcceptanceCriteriaBlock
    validation_plan: ValidationPlanBlock
    estimated_complexity: str
    blocked: bool = False


class DeliverableOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    code: str
    title: str
    description: str
    work_package_ref: str


class MilestoneOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    code: str
    title: str
    due_hint: str | None = None


class DependencyEdge(BaseModel):
    model_config = ConfigDict(extra="forbid")

    from_task: str
    to_task: str
    kind: str


class DependencyGraph(BaseModel):
    model_config = ConfigDict(extra="forbid")

    nodes: list[str] = Field(default_factory=list)
    edges: list[DependencyEdge] = Field(default_factory=list)


class AmbiguityLogItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    code: str
    detail: str


class UnresolvedDependencyLogItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    task_code: str
    dependency_code: str
    detail: str


class ExecutionPlanResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    proposal_id: str
    plan_name: str
    state: DecompositionState
    created_at: datetime
    updated_at: datetime


class EngineeringTicketOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    task_code: str
    title: str
    description: str
    linked_ids: dict
    dependencies: list[str] = Field(default_factory=list)
    acceptance_criteria: list[str] = Field(default_factory=list)
    definition_of_done: list[str] = Field(default_factory=list)
    suggested_provider_policy: dict = Field(default_factory=dict)
    suggested_task_type: str
    repository_target: dict = Field(default_factory=dict)
    branch_suggestion: str
    context_pack_refs: list[str] = Field(default_factory=list)
    status: TicketStatus = TicketStatus.CREATED


class CodingHandoffPack(BaseModel):
    model_config = ConfigDict(extra="forbid")

    execution_plan_id: str
    work_units: list[dict] = Field(default_factory=list)


class CodingWorkUnitRoutingPreview(BaseModel):
    model_config = ConfigDict(extra="forbid")

    coding_work_unit_id: str
    routing_intent: dict
