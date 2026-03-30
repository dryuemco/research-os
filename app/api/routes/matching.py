from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.session import get_db_session
from app.schemas.matching import MatchRequest, MatchResultResponse
from app.services.matching_service import MatchingService

router = APIRouter()


@router.post("/run", response_model=list[MatchResultResponse])
def run_matching(
    request: MatchRequest,
    db: Annotated[Session, Depends(get_db_session)],
) -> list[MatchResultResponse]:
    service = MatchingService(db)
    try:
        results = service.run_match(request)
        db.commit()
    except ValueError as exc:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return [MatchResultResponse.model_validate(item) for item in results]


@router.get("", response_model=list[MatchResultResponse])
def list_matches(
    db: Annotated[Session, Depends(get_db_session)],
    profile_id: str | None = Query(default=None),
) -> list[MatchResultResponse]:
    service = MatchingService(db)
    results = service.list_matches(profile_id)
    return [MatchResultResponse.model_validate(item) for item in results]
