from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db_session
from app.schemas.health import HealthResponse
from app.services.health_service import HealthService

router = APIRouter()


@router.get("", response_model=HealthResponse)
def health(db: Annotated[Session, Depends(get_db_session)]) -> HealthResponse:
    """Liveness and lightweight dependency status endpoint."""
    return HealthService(db).get_health()
