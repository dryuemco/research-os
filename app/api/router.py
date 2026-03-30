from fastapi import APIRouter

from app.api.routes.decomposition import router as decomposition_router
from app.api.routes.health import router as health_router
from app.api.routes.matching import router as matching_router
from app.api.routes.opportunities import router as opportunities_router
from app.api.routes.proposal_factory import router as proposal_factory_router

api_router = APIRouter()
api_router.include_router(health_router, prefix="/health", tags=["health"])
api_router.include_router(opportunities_router, prefix="/opportunities", tags=["opportunities"])
api_router.include_router(matching_router, prefix="/matches", tags=["matching"])
api_router.include_router(
    proposal_factory_router,
    prefix="/proposal-factory",
    tags=["proposal_factory"],
)

api_router.include_router(
    decomposition_router,
    prefix="/decomposition",
    tags=["decomposition"],
)
