from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.session import get_db_session
from app.schemas.intelligence import (
    PartnerFitRequest,
    PartnerFitResult,
    PartnerProfileCreate,
    PartnerProfileResponse,
    ProposalQualitySummary,
)
from app.schemas.memory import RetrievalQuery
from app.services.partner_intelligence_service import PartnerIntelligenceService
from app.services.proposal_quality_service import ProposalQualityService
from app.services.retrieval_service import RetrievalService

router = APIRouter()


@router.get("/retrieval/backends")
def retrieval_backends(db: Annotated[Session, Depends(get_db_session)]) -> dict:
    return {"items": RetrievalService(db).backend_capabilities()}


@router.post("/retrieval/preview")
def retrieval_preview(
    request: RetrievalQuery,
    db: Annotated[Session, Depends(get_db_session)],
) -> dict:
    items = RetrievalService(db).retrieve(request)
    return {
        "items": [item.model_dump() for item in items],
        "count": len(items),
    }


@router.post("/partners", response_model=PartnerProfileResponse)
def create_partner(
    request: PartnerProfileCreate,
    db: Annotated[Session, Depends(get_db_session)],
) -> PartnerProfileResponse:
    model = PartnerIntelligenceService(db).create_partner(request)
    db.commit()
    return PartnerProfileResponse.model_validate(model)


@router.get("/partners", response_model=list[PartnerProfileResponse])
def list_partners(
    db: Annotated[Session, Depends(get_db_session)],
    active_only: bool = Query(default=True),
) -> list[PartnerProfileResponse]:
    items = PartnerIntelligenceService(db).list_partners(active_only=active_only)
    return [PartnerProfileResponse.model_validate(item) for item in items]


@router.post("/partners/fit", response_model=list[PartnerFitResult])
def partner_fit_preview(
    request: PartnerFitRequest,
    db: Annotated[Session, Depends(get_db_session)],
) -> list[PartnerFitResult]:
    return PartnerIntelligenceService(db).fit_preview(request)


@router.get("/proposal-quality/{proposal_id}", response_model=ProposalQualitySummary)
def proposal_quality_summary(
    proposal_id: str,
    db: Annotated[Session, Depends(get_db_session)],
    round_number: int | None = Query(default=None),
) -> ProposalQualitySummary:
    try:
        return ProposalQualityService(db).summarize(proposal_id, round_number=round_number)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
