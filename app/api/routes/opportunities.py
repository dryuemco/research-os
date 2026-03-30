from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db_session
from app.domain.opportunity_discovery.models import Opportunity
from app.schemas.opportunity import (
    OpportunityDecisionRequest,
    OpportunityIngestRequest,
    OpportunityResponse,
)
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
) -> OpportunityResponse:
    try:
        opportunity = OpportunityIngestionService(db).ingest_dev_payload(request)
        db.commit()
    except ValueError as exc:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return OpportunityResponse.model_validate(opportunity)


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
