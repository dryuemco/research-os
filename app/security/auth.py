from __future__ import annotations

from dataclasses import dataclass
from typing import Annotated

from fastapi import Depends, Header, HTTPException
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.session import get_db_session
from app.domain.common.enums import Permission, UserRole
from app.domain.identity_models import User
from app.security.tokens import decode_access_token


@dataclass(slots=True)
class CurrentUser:
    user_id: str
    role: UserRole
    team_name: str | None
    org_name: str | None


ROLE_PERMISSIONS: dict[UserRole, set[Permission]] = {
    UserRole.ADMIN: set(Permission),
    UserRole.RESEARCH_LEAD: {
        Permission.OPPORTUNITY_APPROVE,
        Permission.PROPOSAL_STATE_TRANSITION,
        Permission.EXPORT_GENERATE,
        Permission.EXPORT_APPROVE,
        Permission.EXPORT_DOWNLOAD,
        Permission.VIEW_SENSITIVE,
    },
    UserRole.GRANT_WRITER: {
        Permission.EXPORT_GENERATE,
        Permission.EXPORT_DOWNLOAD,
        Permission.MEMORY_BLOCK_MUTATE,
        Permission.PROPOSAL_STATE_TRANSITION,
    },
    UserRole.REVIEWER: {
        Permission.EXPORT_APPROVE,
        Permission.EXPORT_DOWNLOAD,
        Permission.VIEW_SENSITIVE,
    },
    UserRole.TECHNICAL_LEAD: {
        Permission.RUNTIME_CONTROL,
        Permission.EXPORT_GENERATE,
        Permission.EXPORT_DOWNLOAD,
        Permission.VIEW_SENSITIVE,
    },
    UserRole.EDITOR: set(),
    UserRole.VIEWER: set(),
}


def _user_to_current(user: User) -> CurrentUser:
    return CurrentUser(
        user_id=user.id,
        role=user.role,
        team_name=user.team_name,
        org_name=user.org_name,
    )


def _resolve_token_user(db: Session, authorization: str | None) -> CurrentUser | None:
    if not authorization or not isinstance(authorization, str):
        return None
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise HTTPException(status_code=401, detail="Invalid authorization header")

    settings = get_settings()
    payload = decode_access_token(token, secret=settings.auth_token_secret)
    if payload is None:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    user = db.get(User, user_id)
    if user is None or not user.is_active:
        raise HTTPException(status_code=403, detail="User is not active or not found")
    return _user_to_current(user)


def _resolve_internal_user(
    db: Session,
    x_internal_api_key: str | None,
    x_user_id: str | None,
    x_user_role: str | None,
) -> CurrentUser:
    settings = get_settings()
    if not settings.internal_api_key:
        raise HTTPException(status_code=500, detail="INTERNAL_API_KEY is not configured")
    if x_internal_api_key != settings.internal_api_key:
        raise HTTPException(status_code=401, detail="Invalid internal API key")
    if not x_user_id:
        raise HTTPException(status_code=401, detail="Missing X-User-Id")

    user = db.get(User, x_user_id)
    if user is None:
        if settings.app_env in {"local", "test"} and x_user_role:
            try:
                role = UserRole(x_user_role)
            except ValueError as exc:
                raise HTTPException(status_code=401, detail="Invalid X-User-Role") from exc
            return CurrentUser(
                user_id=x_user_id,
                role=role,
                team_name=None,
                org_name=None,
            )
        raise HTTPException(status_code=403, detail="User is not active or not found")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="User is not active or not found")
    return _user_to_current(user)


def get_current_user(
    db: Annotated[Session, Depends(get_db_session)],
    authorization: str | None = Header(default=None),
    x_internal_api_key: str | None = Header(default=None),
    x_user_id: str | None = Header(default=None),
    x_user_role: str | None = Header(default=None),
) -> CurrentUser:
    token_user = _resolve_token_user(db, authorization)
    if token_user is not None:
        return token_user
    return _resolve_internal_user(db, x_internal_api_key, x_user_id, x_user_role)


def get_internal_admin_user(
    db: Annotated[Session, Depends(get_db_session)],
    x_internal_api_key: str | None = Header(default=None),
    x_user_id: str | None = Header(default=None),
    x_user_role: str | None = Header(default=None),
) -> CurrentUser:
    settings = get_settings()
    if not settings.internal_api_key:
        raise HTTPException(status_code=500, detail="INTERNAL_API_KEY is not configured")
    if x_internal_api_key != settings.internal_api_key:
        raise HTTPException(status_code=401, detail="Invalid internal API key")
    if not x_user_id:
        raise HTTPException(status_code=401, detail="Missing X-User-Id")

    role_raw = x_user_role or UserRole.ADMIN.value
    try:
        requested_role = UserRole(role_raw)
    except ValueError as exc:
        raise HTTPException(status_code=401, detail="Invalid X-User-Role") from exc

    if requested_role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Missing permissions: ['opportunity.approve']")

    user = db.get(User, x_user_id)
    if user is not None:
        return CurrentUser(
            user_id=user.id,
            role=UserRole.ADMIN,
            team_name=user.team_name,
            org_name=user.org_name,
        )

    return CurrentUser(
        user_id=x_user_id,
        role=UserRole.ADMIN,
        team_name=None,
        org_name=None,
    )


def require_permissions(*permissions: Permission):
    def dependency(
        current_user: Annotated[CurrentUser, Depends(get_current_user)]
    ) -> CurrentUser:
        granted = ROLE_PERMISSIONS.get(current_user.role, set())
        missing = [permission for permission in permissions if permission not in granted]
        if missing:
            raise HTTPException(
                status_code=403,
                detail=f"Missing permissions: {[permission.value for permission in missing]}",
            )
        return current_user

    return dependency


def require_roles(*roles: UserRole):
    def dependency(current_user: Annotated[CurrentUser, Depends(get_current_user)]) -> CurrentUser:
        if current_user.role not in roles:
            raise HTTPException(status_code=403, detail="Insufficient role")
        return current_user

    return dependency
