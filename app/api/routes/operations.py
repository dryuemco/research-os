from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.session import get_db_session
from app.domain.common.enums import Permission
from app.domain.opportunity_discovery.models import Opportunity
from app.schemas.operations import (
    DemoBootstrapRequest,
    MarkNotificationReadRequest,
    MatchingRunResponse,
    NotificationResponse,
    OperationalJobRunResponse,
    TriggerIngestionRequest,
    TriggerLiveIngestionRequest,
    TriggerMatchingRequest,
)
from app.security.auth import get_internal_admin_user, require_permissions
from app.services.demo_seed_service import DemoSeedService
from app.services.opportunity_adapters.base import AdapterFetchError
from app.services.notification_service import NotificationService
from app.services.operational_loop_service import OperationalLoopService
from app.services.opportunity_import_service import OpportunityImportService
from app.services.source_registry_service import SourceRegistryService

router = APIRouter()


def _db_error_payload(exc: Exception, *, default_code: str) -> dict:
    message = str(exc)
    if isinstance(exc, AdapterFetchError):
        return {
            "error_code": exc.code,
            "message": message,
            "diagnostics": exc.diagnostics,
        }
    if "UndefinedTable" in message or 'relation "' in message:
        return {
            "error_code": "database_schema_missing",
            "message": message,
            "remediation": "Apply database migrations: alembic upgrade head",
        }
    return {"error_code": default_code, "message": message}


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


@router.post("/jobs/ingestion/live")
def trigger_live_ingestion(
    request: TriggerLiveIngestionRequest,
    db: Annotated[Session, Depends(get_db_session)],
    _: Annotated[object, Depends(get_internal_admin_user)],
) -> dict:
    normalized_programmes = [item.strip().lower() for item in request.programmes if item.strip()]
    try:
        result = OpportunityImportService(db).ingest_live_eu_funding(
            programmes=normalized_programmes,
            limit=request.limit,
            run_matching_after=request.run_matching_after,
        )
        samples = db.scalars(
            select(Opportunity)
            .where(Opportunity.source_program.in_(normalized_programmes))
            .order_by(Opportunity.created_at.desc())
            .limit(5)
        ).all()
        db.commit()
    except ValueError as exc:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(
            status_code=503,
            detail=_db_error_payload(exc, default_code="db_error"),
        ) from exc
    except Exception as exc:
        db.rollback()
        raise HTTPException(
            status_code=502, detail=_db_error_payload(exc, default_code="live_ingestion_failed")
        ) from exc

    return {
        **result,
        "sample_opportunities": [
            {
                "id": item.id,
                "external_id": item.external_id,
                "title": item.title,
                "source_program": item.source_program,
                "deadline_at": item.deadline_at,
            }
            for item in samples
        ],
    }


@router.post("/bootstrap/demo")
def bootstrap_demo_data(
    request: DemoBootstrapRequest,
    db: Annotated[Session, Depends(get_db_session)],
    _: Annotated[object, Depends(get_internal_admin_user)],
) -> dict:
    if not request.confirm:
        raise HTTPException(
            status_code=400,
            detail="Set confirm=true to run demo bootstrap mutations.",
        )
    try:
        result = DemoSeedService(db).bootstrap(
            fixture_path=request.fixture_path or get_settings().operational_source_fixture_path,
            reset_demo_state=request.reset_demo_state,
            create_demo_proposal=request.create_demo_proposal,
        )
        db.commit()
    except ValueError as exc:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(
            status_code=503,
            detail=_db_error_payload(exc, default_code="db_error"),
        ) from exc
    except Exception as exc:
        db.rollback()
        raise HTTPException(
            status_code=500, detail=_db_error_payload(exc, default_code="demo_bootstrap_failed")
        ) from exc

    return {
        "status": "ok",
        "opportunities_loaded": result.opportunities_loaded,
        "matches_created": result.matches_created,
        "notifications_created": result.notifications_created,
        "proposal_created": result.proposal_created,
    }
