from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.common.enums import DecompositionState, TicketStatus
from app.domain.execution_orchestrator.models import (
    CodingWorkUnit,
    EngineeringTicket,
    ExecutionObjective,
    ExecutionPlan,
    TaskGraph,
    WorkPackage,
)
from app.domain.proposal_factory.models import Proposal
from app.schemas.audit import AuditEventSchema
from app.schemas.execution import (
    CodingHandoffPack,
    CodingWorkUnitRoutingPreview,
    DecompositionRequest,
    DependencyGraph,
    EngineeringTicketOutput,
    ExecutionPlanResponse,
    TaskOutput,
)
from app.services.audit_service import AuditService

_ALLOWED_TRANSITIONS: dict[DecompositionState, set[DecompositionState]] = {
    DecompositionState.NOT_STARTED: {
        DecompositionState.DRAFT_GENERATED,
        DecompositionState.ARCHIVED,
    },
    DecompositionState.DRAFT_GENERATED: {
        DecompositionState.UNDER_REVIEW,
        DecompositionState.SUPERSEDED,
    },
    DecompositionState.UNDER_REVIEW: {
        DecompositionState.APPROVED,
        DecompositionState.DRAFT_GENERATED,
        DecompositionState.SUPERSEDED,
    },
    DecompositionState.APPROVED: {DecompositionState.SUPERSEDED, DecompositionState.ARCHIVED},
    DecompositionState.SUPERSEDED: {DecompositionState.ARCHIVED},
    DecompositionState.ARCHIVED: set(),
}


class InvalidDecompositionTransitionError(ValueError):
    pass


class DecompositionService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.audit = AuditService(db)

    def create_decomposition(self, request: DecompositionRequest) -> ExecutionPlan:
        proposal = self.db.get(Proposal, request.proposal_id)
        if proposal is None:
            raise ValueError("Proposal workspace not found")

        plan = ExecutionPlan(
            proposal_id=request.proposal_id,
            plan_name=request.plan_name,
            state=DecompositionState.DRAFT_GENERATED,
            policy_json=request.policy.model_dump(mode="json"),
        )
        self.db.add(plan)
        self.db.flush()

        objective = ExecutionObjective(
            execution_plan_id=plan.id,
            objective_code="OBJ-1",
            title=request.context.title,
            description=request.context.concept_summary,
            success_metrics=["Milestone accepted", "Validation checks passing"],
        )
        wp = WorkPackage(
            execution_plan_id=plan.id,
            wp_code="WP-1",
            title="Core Implementation",
            objective_ref="OBJ-1",
            description="Initial engineering delivery package",
        )
        self.db.add_all([objective, wp])

        self.audit.emit(
            AuditEventSchema(
                event_type="decomposition_created",
                entity_type="execution_plan",
                entity_id=plan.id,
                actor_type="system",
                actor_id="decomposition_service",
                payload={"proposal_id": request.proposal_id},
            )
        )
        self.db.flush()
        return plan

    def transition_state(
        self,
        plan: ExecutionPlan,
        target_state: DecompositionState,
        *,
        actor_type: str,
        actor_id: str,
        reason: str | None = None,
    ) -> ExecutionPlan:
        if target_state not in _ALLOWED_TRANSITIONS[plan.state]:
            raise InvalidDecompositionTransitionError(
                f"Cannot transition decomposition from {plan.state} to {target_state}"
            )

        if target_state == DecompositionState.APPROVED and actor_type != "user":
            raise InvalidDecompositionTransitionError(
                "Human approval required for decomposition approval"
            )

        previous = plan.state
        plan.state = target_state
        self.db.add(plan)
        self.audit.emit(
            AuditEventSchema(
                event_type="decomposition_state_changed",
                entity_type="execution_plan",
                entity_id=plan.id,
                actor_type=actor_type,
                actor_id=actor_id,
                payload={
                    "from_state": previous.value,
                    "to_state": target_state.value,
                    "reason": reason,
                },
            )
        )
        self.db.flush()
        return plan

    def get_plan(self, plan_id: str) -> ExecutionPlan:
        plan = self.db.get(ExecutionPlan, plan_id)
        if plan is None:
            raise ValueError("Execution plan not found")
        return plan

    def list_plans_for_workspace(self, proposal_id: str) -> list[ExecutionPlan]:
        return self.db.scalars(
            select(ExecutionPlan).where(ExecutionPlan.proposal_id == proposal_id)
        ).all()

    def generate_task_graph(self, plan_id: str, tasks: list[TaskOutput]) -> TaskGraph:
        plan = self.get_plan(plan_id)
        graph = DependencyGraph(
            nodes=[task.task_code for task in tasks],
            edges=[],
        )
        for index in range(1, len(tasks)):
            graph.edges.append(
                {
                    "from_task": tasks[index - 1].task_code,
                    "to_task": tasks[index].task_code,
                    "kind": "blocks",
                }
            )

        task_graph = TaskGraph(
            execution_plan_id=plan.id,
            project_ref=plan.proposal_id,
            source_version_ref=f"plan-{plan.id}",
            graph_json=graph.model_dump(mode="json"),
        )
        self.db.add(task_graph)
        self.db.flush()
        self.audit.emit(
            AuditEventSchema(
                event_type="task_graph_generated",
                entity_type="task_graph",
                entity_id=task_graph.id,
                actor_type="system",
                actor_id="decomposition_service",
                payload={"execution_plan_id": plan.id, "node_count": len(graph.nodes)},
            )
        )
        self.db.flush()
        return task_graph

    def generate_engineering_tickets(
        self,
        plan_id: str,
        tasks: list[TaskOutput],
        *,
        repository_target: dict,
    ) -> list[EngineeringTicket]:
        plan = self.get_plan(plan_id)
        tickets: list[EngineeringTicket] = []
        for task in tasks:
            ticket = EngineeringTicket(
                execution_plan_id=plan.id,
                task_code=task.task_code,
                title=f"[{task.work_package_ref}] {task.title}",
                description=task.description,
                dependencies=[],
                acceptance_criteria=task.acceptance_criteria.criteria,
                definition_of_done=task.validation_plan.checks,
                suggested_provider_policy={"sensitivity": "restricted"},
                suggested_task_type="code_generation",
                repository_target=repository_target,
                branch_suggestion=f"feat/{plan.id[:8]}/{task.task_code.lower()}",
                context_pack_refs=task.required_context,
                status=TicketStatus.READY if not task.blocked else TicketStatus.BLOCKED,
            )
            self.db.add(ticket)
            tickets.append(ticket)

        self.db.flush()
        self.audit.emit(
            AuditEventSchema(
                event_type="engineering_tickets_generated",
                entity_type="execution_plan",
                entity_id=plan.id,
                actor_type="system",
                actor_id="decomposition_service",
                payload={"ticket_count": len(tickets)},
            )
        )
        self.db.flush()
        return tickets

    def generate_coding_handoff_pack(self, plan_id: str) -> CodingHandoffPack:
        plan = self.get_plan(plan_id)
        tickets = self.db.scalars(
            select(EngineeringTicket).where(EngineeringTicket.execution_plan_id == plan.id)
        ).all()
        work_units = []
        for ticket in tickets:
            unit = CodingWorkUnit(
                execution_plan_id=plan.id,
                engineering_ticket_id=ticket.id,
                repository_target=ticket.repository_target,
                branch_name=ticket.branch_suggestion,
                patch_scope={"files": [], "constraints": []},
                suggested_test_artifacts=ticket.definition_of_done,
                rollback_risk_label="medium",
                human_approval_required=True,
                routing_intent={
                    "task_type": ticket.suggested_task_type,
                    "provider_policy": ticket.suggested_provider_policy,
                },
            )
            self.db.add(unit)
            self.db.flush()
            work_units.append(
                {
                    "coding_work_unit_id": unit.id,
                    "ticket_id": ticket.id,
                    "branch_name": unit.branch_name,
                    "human_approval_required": unit.human_approval_required,
                }
            )

        self.audit.emit(
            AuditEventSchema(
                event_type="coding_handoff_generated",
                entity_type="execution_plan",
                entity_id=plan.id,
                actor_type="system",
                actor_id="decomposition_service",
                payload={"work_unit_count": len(work_units)},
            )
        )
        self.db.flush()
        return CodingHandoffPack(execution_plan_id=plan.id, work_units=work_units)

    def routing_intent_preview(self, coding_work_unit_id: str) -> CodingWorkUnitRoutingPreview:
        unit = self.db.get(CodingWorkUnit, coding_work_unit_id)
        if unit is None:
            raise ValueError("Coding work unit not found")
        return CodingWorkUnitRoutingPreview(
            coding_work_unit_id=unit.id,
            routing_intent=unit.routing_intent,
        )

    @staticmethod
    def to_response(plan: ExecutionPlan) -> ExecutionPlanResponse:
        return ExecutionPlanResponse.model_validate(plan)

    @staticmethod
    def ticket_to_output(ticket: EngineeringTicket) -> EngineeringTicketOutput:
        return EngineeringTicketOutput(
            task_code=ticket.task_code,
            title=ticket.title,
            description=ticket.description,
            linked_ids={"execution_plan_id": ticket.execution_plan_id},
            dependencies=ticket.dependencies,
            acceptance_criteria=ticket.acceptance_criteria,
            definition_of_done=ticket.definition_of_done,
            suggested_provider_policy=ticket.suggested_provider_policy,
            suggested_task_type=ticket.suggested_task_type,
            repository_target=ticket.repository_target,
            branch_suggestion=ticket.branch_suggestion,
            context_pack_refs=ticket.context_pack_refs,
            status=ticket.status,
        )
