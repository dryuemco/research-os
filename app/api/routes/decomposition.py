from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db_session
from app.domain.common.enums import DecompositionState
from app.schemas.execution import (
    CodingHandoffPack,
    CodingWorkUnitRoutingPreview,
    DecompositionRequest,
    EngineeringTicketOutput,
    ExecutionPlanResponse,
    TaskOutput,
)
from app.services.decomposition_service import (
    DecompositionService,
    InvalidDecompositionTransitionError,
)

router = APIRouter()


@router.post("", response_model=ExecutionPlanResponse)
def create_decomposition(
    request: DecompositionRequest,
    db: Annotated[Session, Depends(get_db_session)],
) -> ExecutionPlanResponse:
    service = DecompositionService(db)
    try:
        plan = service.create_decomposition(request)
        db.commit()
    except ValueError as exc:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return service.to_response(plan)


@router.get("/{plan_id}", response_model=ExecutionPlanResponse)
def get_decomposition(
    plan_id: str,
    db: Annotated[Session, Depends(get_db_session)],
) -> ExecutionPlanResponse:
    service = DecompositionService(db)
    try:
        plan = service.get_plan(plan_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return service.to_response(plan)


@router.get("/workspace/{proposal_id}", response_model=list[ExecutionPlanResponse])
def list_decompositions(
    proposal_id: str,
    db: Annotated[Session, Depends(get_db_session)],
) -> list[ExecutionPlanResponse]:
    service = DecompositionService(db)
    plans = service.list_plans_for_workspace(proposal_id)
    return [service.to_response(plan) for plan in plans]


@router.post("/{plan_id}/task-graph")
def generate_task_graph(
    plan_id: str,
    tasks: list[TaskOutput],
    db: Annotated[Session, Depends(get_db_session)],
) -> dict:
    service = DecompositionService(db)
    graph = service.generate_task_graph(plan_id, tasks)
    db.commit()
    return {"task_graph_id": graph.id, "nodes": graph.graph_json.get("nodes", [])}


@router.post("/{plan_id}/tickets", response_model=list[EngineeringTicketOutput])
def generate_tickets(
    plan_id: str,
    tasks: list[TaskOutput],
    db: Annotated[Session, Depends(get_db_session)],
) -> list[EngineeringTicketOutput]:
    service = DecompositionService(db)
    tickets = service.generate_engineering_tickets(
        plan_id,
        tasks,
        repository_target={"repository": "placeholder/repo", "risk_tier": "medium"},
    )
    db.commit()
    return [service.ticket_to_output(ticket) for ticket in tickets]


@router.post("/{plan_id}/handoff", response_model=CodingHandoffPack)
def generate_handoff(
    plan_id: str,
    db: Annotated[Session, Depends(get_db_session)],
) -> CodingHandoffPack:
    service = DecompositionService(db)
    handoff = service.generate_coding_handoff_pack(plan_id)
    db.commit()
    return handoff


@router.post("/{plan_id}/decision", response_model=ExecutionPlanResponse)
def decision(
    plan_id: str,
    target_state: DecompositionState,
    actor_id: str,
    db: Annotated[Session, Depends(get_db_session)],
) -> ExecutionPlanResponse:
    service = DecompositionService(db)
    plan = service.get_plan(plan_id)
    try:
        updated = service.transition_state(
            plan,
            target_state,
            actor_type="user",
            actor_id=actor_id,
            reason="manual decision",
        )
        db.commit()
    except InvalidDecompositionTransitionError as exc:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return service.to_response(updated)


@router.get(
    "/work-unit/{coding_work_unit_id}/routing-intent", response_model=CodingWorkUnitRoutingPreview
)
def routing_preview(
    coding_work_unit_id: str,
    db: Annotated[Session, Depends(get_db_session)],
) -> CodingWorkUnitRoutingPreview:
    service = DecompositionService(db)
    try:
        return service.routing_intent_preview(coding_work_unit_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
