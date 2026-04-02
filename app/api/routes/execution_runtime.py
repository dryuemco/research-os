from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db_session
from app.domain.common.enums import Permission
from app.schemas.runtime_execution import (
    ExecutionRunResponse,
    ExecutionTaskRequest,
    ProviderTraceResponse,
    ResumeRunRequest,
    RetryRunRequest,
    RoutingQuotaPreviewRequest,
    RoutingQuotaPreviewResponse,
)
from app.security.auth import require_permissions
from app.services.execution_runtime_service import ExecutionRuntimeService

router = APIRouter()


@router.post("/tasks", response_model=ExecutionRunResponse)
def submit_execution_task(
    request: ExecutionTaskRequest,
    db: Annotated[Session, Depends(get_db_session)],
    _: Annotated[object, Depends(require_permissions(Permission.RUNTIME_CONTROL))],
) -> ExecutionRunResponse:
    service = ExecutionRuntimeService(db)
    try:
        run = service.submit_task(request)
        db.commit()
    except ValueError as exc:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return ExecutionRunResponse.model_validate(run)


@router.get("/runs/{run_id}", response_model=ExecutionRunResponse)
def get_execution_run(
    run_id: str,
    db: Annotated[Session, Depends(get_db_session)],
    _: Annotated[object, Depends(require_permissions(Permission.RUNTIME_CONTROL))],
) -> ExecutionRunResponse:
    service = ExecutionRuntimeService(db)
    try:
        run = service._get_run(run_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return ExecutionRunResponse.model_validate(run)


@router.post("/runs/{run_id}/retry", response_model=ExecutionRunResponse)
def retry_execution_run(
    run_id: str,
    request: RetryRunRequest,
    db: Annotated[Session, Depends(get_db_session)],
    _: Annotated[object, Depends(require_permissions(Permission.RUNTIME_CONTROL))],
) -> ExecutionRunResponse:
    service = ExecutionRuntimeService(db)
    try:
        run = service.retry_run(run_id, request.reason)
        db.commit()
    except ValueError as exc:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return ExecutionRunResponse.model_validate(run)


@router.post("/runs/{run_id}/resume", response_model=ExecutionRunResponse)
def resume_execution_run(
    run_id: str,
    request: ResumeRunRequest,
    db: Annotated[Session, Depends(get_db_session)],
    _: Annotated[object, Depends(require_permissions(Permission.RUNTIME_CONTROL))],
) -> ExecutionRunResponse:
    service = ExecutionRuntimeService(db)
    try:
        run = service.resume_run(run_id, request.reason)
        db.commit()
    except ValueError as exc:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return ExecutionRunResponse.model_validate(run)


@router.post("/routing-quota-preview", response_model=RoutingQuotaPreviewResponse)
def preview_routing_and_quota(
    request: RoutingQuotaPreviewRequest,
    db: Annotated[Session, Depends(get_db_session)],
) -> RoutingQuotaPreviewResponse:
    service = ExecutionRuntimeService(db)
    response = service.preview_routing_and_quota(request)
    db.commit()
    return response


@router.get("/traces", response_model=list[ProviderTraceResponse])
def list_provider_traces(
    db: Annotated[Session, Depends(get_db_session)],
    run_id: str | None = None,
) -> list[ProviderTraceResponse]:
    service = ExecutionRuntimeService(db)
    traces = service.list_traces(run_id=run_id)
    return [ProviderTraceResponse.model_validate(trace) for trace in traces]


@router.post("/jobs/process-next")
def process_next_job(
    db: Annotated[Session, Depends(get_db_session)],
    _: Annotated[object, Depends(require_permissions(Permission.RUNTIME_CONTROL))],
) -> dict:
    service = ExecutionRuntimeService(db)
    job = service.process_next_job()
    db.commit()
    return {"processed": bool(job), "job_id": job.id if job else None}
