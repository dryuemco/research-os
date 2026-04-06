from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db_session
from app.domain.audit_and_observability.models import AuditEvent
from app.domain.execution_orchestrator.models import ExecutionPlan
from app.domain.execution_orchestrator.runtime_models import ExecutionRun
from app.domain.institutional_memory.models import ExportPackage, ReusableEvidenceBlock
from app.domain.operations.models import MatchingRun, Notification, OperationalJobRun
from app.domain.opportunity_discovery.models import MatchResult, Opportunity
from app.domain.proposal_factory.models import Proposal, ReviewRound
from app.schemas.audit import AuditEventSchema
from app.services.dashboard_service import DashboardService
from app.services.partner_intelligence_service import PartnerIntelligenceService
from app.services.proposal_quality_service import ProposalQualityService

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


@router.get("/opportunities/{opportunity_id}")
def dashboard_opportunity_detail(
    opportunity_id: str,
    db: Annotated[Session, Depends(get_db_session)],
) -> dict:
    item = db.get(Opportunity, opportunity_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Opportunity not found")
    return {
        "id": item.id,
        "title": item.title,
        "summary": item.summary,
        "state": item.state.value,
        "budget_total": item.budget_total,
        "deadline_at": item.deadline_at,
    }


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
                "explanations": m.explanations,
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


@router.get("/proposals/{proposal_id}")
def dashboard_proposal_detail(
    proposal_id: str,
    db: Annotated[Session, Depends(get_db_session)],
) -> dict:
    proposal = db.get(Proposal, proposal_id)
    if proposal is None:
        raise HTTPException(status_code=404, detail="Proposal not found")

    rounds_stmt = select(ReviewRound).where(ReviewRound.proposal_id == proposal_id)
    exports_stmt = select(ExportPackage).where(ExportPackage.proposal_id == proposal_id)
    rounds = db.scalars(rounds_stmt).all()
    exports = db.scalars(exports_stmt).all()

    return {
        "id": proposal.id,
        "name": proposal.name,
        "state": proposal.state.value,
        "human_approved_for_export": proposal.human_approved_for_export,
        "review_rounds": [
            {"id": r.id, "status": r.status, "round_number": r.round_number} for r in rounds
        ],
        "export_packages": [{"id": e.id, "status": e.status.value} for e in exports],
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
            {"id": p.id, "state": p.state.value, "proposal_id": p.proposal_id, "name": p.plan_name}
            for p in plans
        ]
    }


@router.get("/decomposition/{plan_id}")
def dashboard_decomposition_detail(
    plan_id: str,
    db: Annotated[Session, Depends(get_db_session)],
) -> dict:
    plan = db.get(ExecutionPlan, plan_id)
    if plan is None:
        raise HTTPException(status_code=404, detail="Execution plan not found")
    return {
        "id": plan.id,
        "proposal_id": plan.proposal_id,
        "state": plan.state.value,
        "policy_json": plan.policy_json,
    }


@router.get("/runs")
def dashboard_runs(
    db: Annotated[Session, Depends(get_db_session)],
    limit: int = Query(default=20, ge=1, le=200),
) -> dict:
    runs = db.scalars(
        select(ExecutionRun).order_by(ExecutionRun.created_at.desc()).limit(limit)
    ).all()
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


@router.get("/runs/{run_id}")
def dashboard_run_detail(run_id: str, db: Annotated[Session, Depends(get_db_session)]) -> dict:
    run = db.get(ExecutionRun, run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="Execution run not found")
    return {
        "id": run.id,
        "status": run.status.value,
        "task_type": run.task_type,
        "checkpoint_payload": run.checkpoint_payload,
        "failure_reason": run.failure_reason,
        "attempt_count": run.attempt_count,
    }


@router.get("/exports/{package_id}")
def dashboard_export_detail(
    package_id: str,
    db: Annotated[Session, Depends(get_db_session)],
) -> dict:
    package = db.get(ExportPackage, package_id)
    if package is None:
        raise HTTPException(status_code=404, detail="Export package not found")
    return {
        "id": package.id,
        "status": package.status.value,
        "proposal_id": package.proposal_id,
        "proposal_version_id": package.proposal_version_id,
        "unresolved_items": package.unresolved_items,
    }


@router.get("/blocks/{block_id}")
def dashboard_block_detail(block_id: str, db: Annotated[Session, Depends(get_db_session)]) -> dict:
    block = db.get(ReusableEvidenceBlock, block_id)
    if block is None:
        raise HTTPException(status_code=404, detail="Reusable block not found")
    return {
        "id": block.id,
        "title": block.title,
        "approval_status": block.approval_status.value,
        "provenance_json": block.provenance_json,
    }


@router.get("/audit", response_model=list[AuditEventSchema])
def dashboard_audit_timeline(
    db: Annotated[Session, Depends(get_db_session)],
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    entity_type: str | None = Query(default=None),
    entity_id: str | None = Query(default=None),
) -> list[AuditEventSchema]:
    if entity_type and entity_id:
        events = db.scalars(
            select(AuditEvent)
            .where(AuditEvent.entity_type == entity_type, AuditEvent.entity_id == entity_id)
            .order_by(AuditEvent.created_at.desc())
            .offset(offset)
            .limit(limit)
        ).all()
        return [AuditEventSchema.model_validate(event) for event in events]

    events = DashboardService(db).audit_timeline(limit=limit, offset=offset)
    return [AuditEventSchema.model_validate(event) for event in events]


@router.get("/operations/jobs")
def dashboard_operational_jobs(
    db: Annotated[Session, Depends(get_db_session)],
    limit: int = Query(default=20, ge=1, le=200),
) -> dict:
    items = db.scalars(
        select(OperationalJobRun).order_by(OperationalJobRun.created_at.desc()).limit(limit)
    ).all()
    return {
        "items": [
            {
                "id": i.id,
                "job_type": i.job_type.value,
                "status": i.status.value,
                "trigger_source": i.trigger_source,
                "result_summary": i.result_summary,
                "error_summary": i.error_summary,
            }
            for i in items
        ]
    }


@router.get("/operations/matching-runs")
def dashboard_matching_runs(
    db: Annotated[Session, Depends(get_db_session)],
    limit: int = Query(default=20, ge=1, le=200),
) -> dict:
    items = db.scalars(
        select(MatchingRun).order_by(MatchingRun.created_at.desc()).limit(limit)
    ).all()
    return {
        "items": [
            {
                "id": i.id,
                "profile_id": i.profile_id,
                "status": i.status.value,
                "opportunities_scanned": i.opportunities_scanned,
                "matches_created": i.matches_created,
                "recommendations_count": i.recommendations_count,
                "red_flags_count": i.red_flags_count,
            }
            for i in items
        ]
    }


@router.get("/operations/notifications")
def dashboard_notifications(
    db: Annotated[Session, Depends(get_db_session)],
    user_id: str = Query(default="ops-admin"),
    limit: int = Query(default=20, ge=1, le=200),
) -> dict:
    items = db.scalars(
        select(Notification)
        .where(Notification.recipient_user_id == user_id)
        .order_by(Notification.created_at.desc())
        .limit(limit)
    ).all()
    return {
        "items": [
            {
                "id": n.id,
                "type": n.notification_type.value,
                "status": n.status.value,
                "related_entity_type": n.related_entity_type,
                "related_entity_id": n.related_entity_id,
                "payload_json": n.payload_json,
            }
            for n in items
        ]
    }


@router.get("/intelligence/partners")
def dashboard_partner_intelligence(
    db: Annotated[Session, Depends(get_db_session)],
    active_only: bool = Query(default=True),
) -> dict:
    items = PartnerIntelligenceService(db).list_partners(active_only=active_only)
    return {
        "items": [
            {
                "id": p.id,
                "partner_name": p.partner_name,
                "country_code": p.country_code,
                "capability_tags": p.capability_tags,
            }
            for p in items
        ]
    }


@router.get("/intelligence/proposals/{proposal_id}/quality")
def dashboard_proposal_quality(
    proposal_id: str,
    db: Annotated[Session, Depends(get_db_session)],
    round_number: int | None = Query(default=None),
) -> dict:
    try:
        summary = ProposalQualityService(db).summarize(proposal_id, round_number=round_number)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return summary.model_dump()
