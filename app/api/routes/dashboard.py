from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db_session
from app.domain.execution_orchestrator.models import ExecutionPlan
from app.domain.execution_orchestrator.runtime_models import ExecutionRun
from app.domain.opportunity_discovery.models import MatchResult, Opportunity
from app.domain.proposal_factory.models import Proposal
from app.schemas.audit import AuditEventSchema
from app.services.dashboard_service import DashboardService

router = APIRouter()


@router.get("/summary")
def dashboard_summary(db: Annotated[Session, Depends(get_db_session)]) -> dict:
    return DashboardService(db).summary()


@router.get("/opportunities")
def dashboard_opportunities(
    db: Annotated[Session, Depends(get_db_session)],
    limit: int = Query(default=20, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> dict:
    items = db.scalars(
        select(Opportunity).order_by(Opportunity.created_at.desc()).offset(offset).limit(limit)
    ).all()
    return {"items": [{"id": o.id, "title": o.title, "state": o.state.value} for o in items]}


@router.get("/matches")
def dashboard_matches(
    db: Annotated[Session, Depends(get_db_session)],
    limit: int = Query(default=20, ge=1, le=200),
) -> dict:
    stmt = select(MatchResult).order_by(MatchResult.created_at.desc()).limit(limit)
    items = db.scalars(stmt).all()
    return {
        "items": [
            {
                "id": m.id,
                "opportunity_id": m.opportunity_id,
                "total_score": m.total_score,
                "recommendation": m.recommendation,
            }
            for m in items
        ]
    }


@router.get("/proposals")
def dashboard_proposals(
    db: Annotated[Session, Depends(get_db_session)],
    limit: int = Query(default=20, ge=1, le=200),
) -> dict:
    proposals = db.scalars(select(Proposal).order_by(Proposal.created_at.desc()).limit(limit)).all()
    return {
        "items": [
            {"id": p.id, "name": p.name, "state": p.state.value, "opportunity_id": p.opportunity_id}
            for p in proposals
        ]
    }


@router.get("/decomposition")
def dashboard_decomposition(
    db: Annotated[Session, Depends(get_db_session)],
    limit: int = Query(default=20, ge=1, le=200),
) -> dict:
    stmt = select(ExecutionPlan).order_by(ExecutionPlan.created_at.desc()).limit(limit)
    plans = db.scalars(stmt).all()
    return {
        "items": [
            {"id": p.id, "state": p.state.value, "proposal_id": p.proposal_id} for p in plans
        ]
    }


@router.get("/runs")
def dashboard_runs(
    db: Annotated[Session, Depends(get_db_session)],
    limit: int = Query(default=20, ge=1, le=200),
) -> dict:
    stmt = select(ExecutionRun).order_by(ExecutionRun.created_at.desc()).limit(limit)
    runs = db.scalars(stmt).all()
    return {
        "items": [
            {
                "id": r.id,
                "task_type": r.task_type,
                "status": r.status.value,
                "selected_provider": r.selected_provider,
                "attempt_count": r.attempt_count,
            }
            for r in runs
        ]
    }


@router.get("/audit", response_model=list[AuditEventSchema])
def dashboard_audit_timeline(
    db: Annotated[Session, Depends(get_db_session)],
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> list[AuditEventSchema]:
    events = DashboardService(db).audit_timeline(limit=limit, offset=offset)
    return [AuditEventSchema.model_validate(event) for event in events]
