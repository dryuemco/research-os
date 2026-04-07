from fastapi import APIRouter

from app.api.routes.auth import router as auth_router
from app.api.routes.dashboard import router as dashboard_router
from app.api.routes.decomposition import router as decomposition_router
from app.api.routes.execution_runtime import router as execution_runtime_router
from app.api.routes.health import router as health_router
from app.api.routes.intelligence import router as intelligence_router
from app.api.routes.internal_ui import router as internal_ui_router
from app.api.routes.matching import router as matching_router
from app.api.routes.memory import router as memory_router
from app.api.routes.operations import router as operations_router
from app.api.routes.opportunities import router as opportunities_router
from app.api.routes.proposal_factory import router as proposal_factory_router
from app.api.routes.target_calls import router as target_calls_router

api_router = APIRouter()
api_router.include_router(auth_router, prefix="/auth", tags=["auth"])
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
api_router.include_router(
    execution_runtime_router,
    prefix="/execution-runtime",
    tags=["execution_runtime"],
)
api_router.include_router(dashboard_router, prefix="/dashboard", tags=["dashboard"])
api_router.include_router(memory_router, prefix="/memory", tags=["memory"])
api_router.include_router(intelligence_router, prefix="/intelligence", tags=["intelligence"])
api_router.include_router(operations_router, prefix="/operations", tags=["operations"])
api_router.include_router(internal_ui_router, prefix="/ui", tags=["internal_ui"])
api_router.include_router(target_calls_router, prefix="/target-calls", tags=["target_calls"])
