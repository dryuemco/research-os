from sqlalchemy import Boolean, Enum, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import JSON

from app.db.base import Base
from app.domain.common.enums import CodingTaskState, DecompositionState, TicketStatus
from app.domain.common.mixins import TimestampMixin, UUIDPrimaryKeyMixin

JSONType = JSON().with_variant(JSONB, "postgresql")


class ExecutionPlan(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "execution_plans"

    proposal_id: Mapped[str] = mapped_column(
        ForeignKey("proposals.id", ondelete="CASCADE"), index=True
    )
    plan_name: Mapped[str] = mapped_column(String(255), default="Execution Plan")
    state: Mapped[DecompositionState] = mapped_column(
        Enum(DecompositionState), default=DecompositionState.NOT_STARTED, index=True
    )
    policy_json: Mapped[dict] = mapped_column(JSONType, default=dict)
    ambiguity_log: Mapped[list[dict]] = mapped_column(JSONType, default=list)
    unresolved_dependency_log: Mapped[list[dict]] = mapped_column(JSONType, default=list)


class WorkPackage(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "work_packages"

    execution_plan_id: Mapped[str] = mapped_column(
        ForeignKey("execution_plans.id", ondelete="CASCADE"), index=True
    )
    wp_code: Mapped[str] = mapped_column(String(64), index=True)
    title: Mapped[str] = mapped_column(String(255))
    objective_ref: Mapped[str] = mapped_column(String(64))
    description: Mapped[str] = mapped_column(Text)


class ExecutionObjective(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "execution_objectives"

    execution_plan_id: Mapped[str] = mapped_column(
        ForeignKey("execution_plans.id", ondelete="CASCADE"), index=True
    )
    objective_code: Mapped[str] = mapped_column(String(64), index=True)
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(Text)
    success_metrics: Mapped[list[str]] = mapped_column(JSONType, default=list)


class Deliverable(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "deliverables"

    execution_plan_id: Mapped[str] = mapped_column(
        ForeignKey("execution_plans.id", ondelete="CASCADE"), index=True
    )
    work_package_id: Mapped[str] = mapped_column(ForeignKey("work_packages.id", ondelete="CASCADE"))
    code: Mapped[str] = mapped_column(String(64), index=True)
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(Text)


class Milestone(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "milestones"

    execution_plan_id: Mapped[str] = mapped_column(
        ForeignKey("execution_plans.id", ondelete="CASCADE"), index=True
    )
    code: Mapped[str] = mapped_column(String(64), index=True)
    title: Mapped[str] = mapped_column(String(255))
    due_hint: Mapped[str | None] = mapped_column(String(64), nullable=True)


class RiskItem(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "risk_items"

    execution_plan_id: Mapped[str] = mapped_column(
        ForeignKey("execution_plans.id", ondelete="CASCADE"), index=True
    )
    risk_code: Mapped[str] = mapped_column(String(64), index=True)
    description: Mapped[str] = mapped_column(Text)
    mitigation: Mapped[str] = mapped_column(Text)
    severity: Mapped[str] = mapped_column(String(32), default="medium")


class ValidationActivity(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "validation_activities"

    execution_plan_id: Mapped[str] = mapped_column(
        ForeignKey("execution_plans.id", ondelete="CASCADE"), index=True
    )
    task_code: Mapped[str] = mapped_column(String(64), index=True)
    validation_type: Mapped[str] = mapped_column(String(64))
    details: Mapped[str] = mapped_column(Text)


class TaskGraph(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "task_graphs"

    execution_plan_id: Mapped[str] = mapped_column(
        ForeignKey("execution_plans.id", ondelete="CASCADE"), index=True
    )
    project_ref: Mapped[str] = mapped_column(String(255), index=True)
    source_version_ref: Mapped[str] = mapped_column(String(255), index=True)
    graph_json: Mapped[dict] = mapped_column(JSONType)


class EngineeringTicket(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "engineering_tickets"

    execution_plan_id: Mapped[str] = mapped_column(
        ForeignKey("execution_plans.id", ondelete="CASCADE"), index=True
    )
    task_code: Mapped[str] = mapped_column(String(64), index=True)
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(Text)
    dependencies: Mapped[list[str]] = mapped_column(JSONType, default=list)
    acceptance_criteria: Mapped[list[str]] = mapped_column(JSONType, default=list)
    definition_of_done: Mapped[list[str]] = mapped_column(JSONType, default=list)
    suggested_provider_policy: Mapped[dict] = mapped_column(JSONType, default=dict)
    suggested_task_type: Mapped[str] = mapped_column(String(64))
    repository_target: Mapped[dict] = mapped_column(JSONType, default=dict)
    branch_suggestion: Mapped[str] = mapped_column(String(128))
    context_pack_refs: Mapped[list[str]] = mapped_column(JSONType, default=list)
    status: Mapped[TicketStatus] = mapped_column(Enum(TicketStatus), default=TicketStatus.CREATED)


class CodingWorkUnit(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "coding_work_units"

    execution_plan_id: Mapped[str] = mapped_column(
        ForeignKey("execution_plans.id", ondelete="CASCADE"), index=True
    )
    engineering_ticket_id: Mapped[str] = mapped_column(
        ForeignKey("engineering_tickets.id", ondelete="CASCADE"), index=True
    )
    repository_target: Mapped[dict] = mapped_column(JSONType, default=dict)
    branch_name: Mapped[str] = mapped_column(String(128))
    patch_scope: Mapped[dict] = mapped_column(JSONType, default=dict)
    suggested_test_artifacts: Mapped[list[str]] = mapped_column(JSONType, default=list)
    rollback_risk_label: Mapped[str] = mapped_column(String(32), default="medium")
    human_approval_required: Mapped[bool] = mapped_column(Boolean, default=True)
    routing_intent: Mapped[dict] = mapped_column(JSONType, default=dict)


class CodingTask(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "coding_tasks"

    task_graph_id: Mapped[str] = mapped_column(ForeignKey("task_graphs.id", ondelete="CASCADE"))
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(Text)
    acceptance_criteria: Mapped[list[str]] = mapped_column(JSONType)
    context_refs: Mapped[list[str]] = mapped_column(JSONType)
    provider_policy: Mapped[dict] = mapped_column(JSONType)
    recommended_models: Mapped[list[str]] = mapped_column(JSONType)
    estimated_cost_band: Mapped[str] = mapped_column(String(32))
    status: Mapped[CodingTaskState] = mapped_column(
        Enum(CodingTaskState), default=CodingTaskState.CREATED, index=True
    )
