import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import structlog

from app.core.config import settings, validate_production_settings
from app.core.domain_config import get_domain_config
from app.core.logging import configure_structlog
from app.core.middleware import CorrelationIdMiddleware, SecurityHeadersMiddleware
from app.api.v1.endpoints import (
    health,
    auth,
    signals,
    pipeline,
    search,
    feedback,
    intelligence,
    registry,
    cache,
    observability,
    ingestion,
)

# Initialize structured JSON logging
configure_structlog(json_logs=True)
logger = structlog.get_logger("metaradar.main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("service_startup", message="Initializing MetaRadar Backend Service...")
    validate_production_settings()
    try:
        domain_cfg = get_domain_config()
        logger.info(
            "domain_config_loaded",
            disease_area=domain_cfg.disease_area,
            version=domain_cfg.domain_config_version,
        )
    except Exception as e:
        logger.error("domain_config_load_failed", error=str(e))

    # Auto-seed demo personas and canonical data sources
    try:
        from app.db.session import AsyncSessionLocal
        from app.services.auth_service import seed_demo_users_if_needed
        from app.db.seed import seed_canonical_sources_if_needed
        async with AsyncSessionLocal() as session:
            await seed_demo_users_if_needed(session)
            await seed_canonical_sources_if_needed(session)
            await session.commit()
    except Exception as e:
        logger.debug("Startup auto-seed skipped/failed: %s", e)

    # Initialize & Start Autonomous Ingestion Scheduler
    from app.services.scheduler import SourceScheduler
    scheduler = SourceScheduler.get_instance()
    scheduler.start()

    yield

    # Shutdown
    logger.info("service_shutdown", message="Shutting down MetaRadar Backend Service...")
    await scheduler.stop()


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan
)

# Middleware Setup (Order matters in Starlette: last added runs first on request)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(CorrelationIdMiddleware)

# CORS Middleware Setup
if settings.cors_origins_list:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    Catch unhandled exceptions and return structured JSON while strictly preserving
    Access-Control-Allow-* CORS headers. Prevents client browsers from masking server/database
    errors behind opaque 'TypeError: Failed to fetch'.
    """
    logger.error("unhandled_server_exception", error=str(exc), path=request.url.path)

    origin = request.headers.get("origin")
    headers: dict[str, str] = {}
    if origin and settings.cors_origins_list:
        if origin in settings.cors_origins_list or "*" in settings.cors_origins_list:
            headers["Access-Control-Allow-Origin"] = origin
            headers["Access-Control-Allow-Credentials"] = "true"
            headers["Vary"] = "Origin"

    exc_msg = str(exc).lower()
    exc_type = type(exc).__name__.lower()
    is_db_err = any(
        k in exc_msg or k in exc_type
        for k in ["database", "asyncpg", "connection", "operationalerror", "timeout", "interfaceerror"]
    )
    status_code = 503 if is_db_err else 500
    detail = (
        "Database service is unavailable or paused. If using free-tier cloud hosting (Supabase/Render), verify database status."
        if is_db_err
        else "Internal Server Error"
    )

    return JSONResponse(
        status_code=status_code,
        content={"detail": detail, "error_type": type(exc).__name__},
        headers=headers,
    )

# Router Registrations
app.include_router(health.router, prefix=f"{settings.API_V1_STR}/health", tags=["Health & Diagnostics"])
app.include_router(auth.router, prefix=f"{settings.API_V1_STR}/auth", tags=["Authentication & Identity"])
app.include_router(signals.router, prefix=f"{settings.API_V1_STR}", tags=["Signals & Intelligence"])
app.include_router(intelligence.router, prefix=f"{settings.API_V1_STR}", tags=["Intelligence Views"])
app.include_router(registry.router, prefix=f"{settings.API_V1_STR}", tags=["Registry"])
app.include_router(observability.router, prefix=f"{settings.API_V1_STR}", tags=["Observability & System Health"])
app.include_router(cache.router, prefix=f"{settings.API_V1_STR}", tags=["Cache Management"])
app.include_router(pipeline.router, prefix=f"{settings.API_V1_STR}", tags=["Pipeline Execution"])
app.include_router(ingestion.router, prefix=f"{settings.API_V1_STR}", tags=["Live Ingestion & Data Connectors"])
app.include_router(search.router, prefix=f"{settings.API_V1_STR}/search", tags=["Search & Retrieval"])
app.include_router(feedback.router, prefix=f"{settings.API_V1_STR}", tags=["Stakeholder Calibration & Feedback"])


@app.get("/")
async def root():
    return {
        "name": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "docs_url": "/docs",
        "api_v1": settings.API_V1_STR
    }
