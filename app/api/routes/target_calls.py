from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db_session
from app.domain.common.enums import UserRole
from app.schemas.target_call import (
    TargetCallCreateRequest,
    TargetCallResponse,
    TargetCallUpdateRequest,
)
from app.security.auth import CurrentUser, require_roles
from app.services.target_call_service import TargetCallService

router = APIRouter()


@router.post("", response_model=TargetCallResponse)
def create_target_call(
    request: TargetCallCreateRequest,
    db: Annotated[Session, Depends(get_db_session)],
    current_user: Annotated[CurrentUser, Depends(require_roles(UserRole.ADMIN))],
) -> TargetCallResponse:
    item = TargetCallService(db).create(request, actor_user_id=current_user.user_id)
    db.commit()
    return TargetCallResponse.model_validate(item)


@router.get("", response_model=list[TargetCallResponse])
def list_target_calls(
    db: Annotated[Session, Depends(get_db_session)],
    _: Annotated[CurrentUser, Depends(require_roles(UserRole.ADMIN))],
) -> list[TargetCallResponse]:
    items = TargetCallService(db).list_all()
    return [TargetCallResponse.model_validate(item) for item in items]


@router.get("/{target_call_id}", response_model=TargetCallResponse)
def get_target_call(
    target_call_id: str,
    db: Annotated[Session, Depends(get_db_session)],
    _: Annotated[CurrentUser, Depends(require_roles(UserRole.ADMIN))],
) -> TargetCallResponse:
    try:
        item = TargetCallService(db).get_or_raise(target_call_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return TargetCallResponse.model_validate(item)


@router.patch("/{target_call_id}", response_model=TargetCallResponse)
def update_target_call(
    target_call_id: str,
    request: TargetCallUpdateRequest,
    db: Annotated[Session, Depends(get_db_session)],
    current_user: Annotated[CurrentUser, Depends(require_roles(UserRole.ADMIN))],
) -> TargetCallResponse:
    service = TargetCallService(db)
    try:
        item = service.update(target_call_id, request, actor_user_id=current_user.user_id)
        db.commit()
    except ValueError as exc:
        db.rollback()
        if str(exc) == "Target call not found":
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return TargetCallResponse.model_validate(item)


@router.delete("/{target_call_id}", response_model=TargetCallResponse)
def delete_target_call(
    target_call_id: str,
    db: Annotated[Session, Depends(get_db_session)],
    current_user: Annotated[CurrentUser, Depends(require_roles(UserRole.ADMIN))],
) -> TargetCallResponse:
    service = TargetCallService(db)
    try:
        item = service.archive(target_call_id, actor_user_id=current_user.user_id)
        db.commit()
    except ValueError as exc:
        db.rollback()
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return TargetCallResponse.model_validate(item)
