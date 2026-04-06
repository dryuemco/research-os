import json
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.session import get_db_session
from app.domain.common.enums import Permission
from app.domain.opportunity_discovery.models import Opportunity
from app.schemas.opportunity import (
    OpportunityDecisionRequest,
    OpportunityIngestRequest,
    OpportunityResponse,
)
from app.security.auth import require_permissions
from app.services.operational_loop_service import OperationalLoopService
from app.services.opportunity_ingestion_service import OpportunityIngestionService
from app.services.opportunity_state_service import (
    InvalidOpportunityTransitionError,
    OpportunityStateService,
)

router = APIRouter()


@router.post("/ingest/dev", response_model=OpportunityResponse)
def ingest_dev_payload(
    request: OpportunityIngestRequest,
    db: Annotated[Session, Depends(get_db_session)],
    _: Annotated[object, Depends(require_permissions(Permission.OPPORTUNITY_APPROVE))],
) -> OpportunityResponse:
    try:
        opportunity = OpportunityIngestionService(db).ingest_dev_payload(request)
        db.commit()
    except ValueError as exc:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return OpportunityResponse.model_validate(opportunity)


@router.post("/ingest/dev/fixture")
def ingest_dev_fixture(
    db: Annotated[Session, Depends(get_db_session)],
    _: Annotated[object, Depends(require_permissions(Permission.OPPORTUNITY_APPROVE))],
    fixture_path: str = Query(
        default=get_settings().operational_source_fixture_path,
        description="Server-side JSON fixture file containing records[]",
    ),
    run_matching_after: bool = Query(
        default=True,
        description="Run matching after ingestion using the default operational profile.",
    ),
) -> dict:
    try:
        payload = json.loads(Path(fixture_path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise HTTPException(status_code=400, detail=f"Invalid fixture file: {exc}") from exc

    records = payload.get("records", [])
    if not isinstance(records, list) or not records:
        raise HTTPException(status_code=400, detail="Fixture file must contain non-empty records[]")

    try:
        run = OperationalLoopService(db).run_ingestion_job(
            source_name=payload.get("source_name", "funding_call_scaffold"),
            trigger_source="opportunities_ingest_dev_fixture",
            run_matching_after=run_matching_after,
            records=records,
        )
        db.commit()
    except ValueError as exc:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return {
        "job_run_id": run.id,
        "job_status": run.status.value,
        "result_summary": run.result_summary,
        "fixture_path": fixture_path,
    }


@router.get("", response_model=list[OpportunityResponse])
def list_opportunities(
    db: Annotated[Session, Depends(get_db_session)],
) -> list[OpportunityResponse]:
    items = db.scalars(select(Opportunity).order_by(Opportunity.created_at.desc())).all()
    return [OpportunityResponse.model_validate(item) for item in items]


@router.get("/{opportunity_id}", response_model=OpportunityResponse)
def get_opportunity(
    opportunity_id: str,
    db: Annotated[Session, Depends(get_db_session)],
    _: Annotated[object, Depends(require_permissions(Permission.OPPORTUNITY_APPROVE))],
) -> OpportunityResponse:
    item = db.get(Opportunity, opportunity_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Opportunity not found")
    return OpportunityResponse.model_validate(item)


@router.post("/{opportunity_id}/decision", response_model=OpportunityResponse)
def set_decision(
    opportunity_id: str,
    request: OpportunityDecisionRequest,
    db: Annotated[Session, Depends(get_db_session)],
    _: Annotated[object, Depends(require_permissions(Permission.OPPORTUNITY_APPROVE))],
) -> OpportunityResponse:
    item = db.get(Opportunity, opportunity_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Opportunity not found")

    service = OpportunityStateService(db)
    try:
        service.apply_decision(
            item,
            request.action,
            actor_type=request.actor_type,
            actor_id=request.actor_id,
            reason=request.reason,
        )
        db.commit()
    except InvalidOpportunityTransitionError as exc:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return OpportunityResponse.model_validate(item)
