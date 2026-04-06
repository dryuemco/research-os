import logging
from contextlib import asynccontextmanager
from uuid import uuid4

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.core.config import get_settings
from app.core.logging import configure_logging

try:
    settings = get_settings()
except Exception:  # pragma: no cover - startup boot guard
    logging.basicConfig(level=logging.INFO)
    logging.getLogger(__name__).exception("Failed to load application settings during import")
    raise

configure_logging(settings.log_level)
logger = logging.getLogger(__name__)


def _startup_summary() -> dict[str, object]:
    default_internal_key = settings.internal_api_key in (None, "", "dev-internal-key")
    default_download_secret = settings.artifact_download_secret in (
        None,
        "",
        "dev-artifact-download-secret",
    )
    return {
        "app_env": settings.app_env,
        "host": settings.runtime_host(),
        "port": settings.runtime_port(),
        "docs_enabled": settings.docs_enabled,
        "database_url_scheme": settings.sqlalchemy_database_url().split("://", maxsplit=1)[0],
        "cors_origins_count": len(settings.cors_origins()),
        "using_default_internal_api_key": default_internal_key,
        "using_default_artifact_download_secret": default_download_secret,
    }

@asynccontextmanager
async def lifespan(_: FastAPI):
    logger.info("FastAPI startup diagnostics: %s", _startup_summary())
    yield


app = FastAPI(
    title=settings.app_name,
    debug=settings.app_debug,
    docs_url="/docs" if settings.docs_enabled else None,
    redoc_url="/redoc" if settings.docs_enabled else None,
    openapi_url="/openapi.json" if settings.docs_enabled else None,
    lifespan=lifespan,
)

allowed_origins = settings.cors_origins()
if allowed_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=False,
        allow_methods=["GET", "POST", "PUT", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type", "X-Internal-Api-Key", "X-User-Id"],
    )
app.include_router(api_router)


@app.middleware("http")
async def request_id_middleware(request, call_next):
    request_id = request.headers.get("X-Request-Id") or str(uuid4())
    response = await call_next(request)
    response.headers["X-Request-Id"] = request_id
    return response


def run() -> None:
    host = settings.runtime_host()
    port = settings.runtime_port()
    logger.info("Starting FastAPI runtime with config: %s", _startup_summary())
    try:
        uvicorn.run("app.main:app", host=host, port=port, log_level=settings.log_level.lower())
    except Exception:
        logger.exception("Failed to boot FastAPI runtime")
        raise


if __name__ == "__main__":
    run()
