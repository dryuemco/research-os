from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.session import get_db_session
from app.schemas.auth import LoginRequest, LoginResponse
from app.security.tokens import create_access_token
from app.services.auth_service import AuthService

router = APIRouter()


@router.post("/login", response_model=LoginResponse)
def login(
    request: LoginRequest,
    db: Annotated[Session, Depends(get_db_session)],
) -> LoginResponse:
    user = AuthService(db).authenticate(username=request.username, password=request.password)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )

    settings = get_settings()
    ttl_seconds = settings.auth_token_ttl_minutes * 60
    token = create_access_token(
        {"sub": user.id, "username": user.username, "role": user.role.value},
        secret=settings.auth_token_secret,
        ttl_seconds=ttl_seconds,
    )
    return LoginResponse(
        access_token=token,
        expires_in_seconds=ttl_seconds,
        username=user.username,
        role=user.role.value,
    )
