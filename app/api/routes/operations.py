from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.session import get_db_session
from app.schemas.operations import (
    MarkNotificationReadRequest,
    MatchingRunResponse,
    NotificationResponse,
    OperationalJobRunResponse,
    TriggerIngestionRequest,
    TriggerMatchingRequest,
)
from app.services.notification_service import NotificationService
from app.services.operational_loop_service import OperationalLoopService
from app.services.source_registry_service import SourceRegistryService

router = APIRouter()


@router.get("/sources")
def list_sources() -> dict:
    return {"items": SourceRegistryService().list_sources()}


@router.post("/jobs/ingestion", response_model=OperationalJobRunResponse)
def trigger_ingestion(
    request: TriggerIngestionRequest,
    db: Annotated[Session, Depends(get_db_session)],
) -> OperationalJobRunResponse:
    service = OperationalLoopService(db)
    try:
        run = service.run_ingestion_job(
            source_name=request.source_name,
            trigger_source=request.trigger_source,
            run_matching_after=request.run_matching_after,
            records=[r.model_dump() for r in request.records] if request.records else None,
        )
        db.commit()
    except ValueError as exc:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return OperationalJobRunResponse.model_validate(run)


@router.post("/jobs/matching", response_model=OperationalJobRunResponse)
def trigger_matching(
    request: TriggerMatchingRequest,
    db: Annotated[Session, Depends(get_db_session)],
) -> OperationalJobRunResponse:
    service = OperationalLoopService(db)
    try:
        run = service.run_matching_job(
            profile_id=request.profile_id,
            scoring_policy_id=request.scoring_policy_id,
            trigger_source=request.trigger_source,
            opportunity_ids=request.opportunity_ids,
        )
        db.commit()
    except ValueError as exc:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return OperationalJobRunResponse.model_validate(run)


@router.post("/scheduler/tick", response_model=list[OperationalJobRunResponse])
def scheduler_tick(
    db: Annotated[Session, Depends(get_db_session)],
) -> list[OperationalJobRunResponse]:
    service = OperationalLoopService(db)
    runs = service.run_due_jobs()
    db.commit()
    return [OperationalJobRunResponse.model_validate(item) for item in runs]


@router.get("/jobs", response_model=list[OperationalJobRunResponse])
def list_job_runs(
    db: Annotated[Session, Depends(get_db_session)],
    limit: int = Query(default=50, ge=1, le=200),
) -> list[OperationalJobRunResponse]:
    runs = OperationalLoopService(db).list_job_runs(limit=limit)
    return [OperationalJobRunResponse.model_validate(item) for item in runs]


@router.get("/matching-runs", response_model=list[MatchingRunResponse])
def list_matching_runs(
    db: Annotated[Session, Depends(get_db_session)],
    limit: int = Query(default=50, ge=1, le=200),
) -> list[MatchingRunResponse]:
    runs = OperationalLoopService(db).list_matching_runs(limit=limit)
    return [MatchingRunResponse.model_validate(item) for item in runs]


@router.get("/notifications", response_model=list[NotificationResponse])
def list_notifications(
    user_id: str,
    db: Annotated[Session, Depends(get_db_session)],
) -> list[NotificationResponse]:
    items = NotificationService(db).list_for_user(user_id)
    return [NotificationResponse.model_validate(item) for item in items]


@router.post("/notifications/{notification_id}/read", response_model=NotificationResponse)
def mark_notification_read(
    notification_id: str,
    request: MarkNotificationReadRequest,
    db: Annotated[Session, Depends(get_db_session)],
) -> NotificationResponse:
    try:
        item = NotificationService(db).mark_read(notification_id, user_id=request.user_id)
        db.commit()
    except ValueError as exc:
        db.rollback()
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return NotificationResponse.model_validate(item)
