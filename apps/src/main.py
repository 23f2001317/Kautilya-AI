# apps/src/main.py
"""FastAPI application entrypoint for Kautilya AI."""

from contextlib import asynccontextmanager
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import structlog

from .api.alerts_sim import router as alerts_sim_router
from .api.audit import router as audit_router
from .api.incidents import router as incidents_router
from .api.slack import router as slack_router
from .api.tasks import router as tasks_router
from .api.topology import router as topology_router
from .api.webhooks import router as webhooks_router
from .api.websockets import router as websockets_router
from .api.config import router as config_router
from .core.database import init_db
from .core.scheduler import autonomous_scan_loop

logger = structlog.get_logger(__name__)
DEFAULT_CORS_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan managing database bootstrapping and teardown."""
    logger.info("bootstrapping_kautilya_storage")
    await init_db()
    
    # Start autonomous scanner loop in background
    import asyncio
    scan_task = asyncio.create_task(autonomous_scan_loop())
    
    yield
    
    logger.info("shutting_down_kautilya_api")
    scan_task.cancel()


app = FastAPI(
    title="Kautilya AI API",
    version="0.2.0",
    description="Enterprise AI Agent Platform for SREs",
    lifespan=lifespan,
)

# Enable CORS for Next.js dashboard local dev and staging
cors_origins_env = os.getenv("CORS_ALLOW_ORIGINS")
allowed_cors_origins = (
    [origin.strip() for origin in cors_origins_env.split(",") if origin.strip()]
    if cors_origins_env
    else DEFAULT_CORS_ORIGINS
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(webhooks_router)
app.include_router(incidents_router)
app.include_router(tasks_router)
app.include_router(websockets_router)
app.include_router(slack_router)
app.include_router(audit_router)
app.include_router(topology_router)
app.include_router(alerts_sim_router)
app.include_router(config_router)


@app.get("/healthz", tags=["Health"])
async def health_check() -> dict[str, str]:
    """Basic health check endpoint."""
    return {"status": "ok"}
