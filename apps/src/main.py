# apps/api/src/main.py
"""FastAPI application entrypoint for Kautilya AI."""

from fastapi import FastAPI
import structlog

from .api.webhooks import router as webhooks_router

logger = structlog.get_logger(__name__)

app = FastAPI(
    title="Kautilya AI API",
    version="0.1.0",
    description="Enterprise AI Agent Platform for SREs",
)

app.include_router(webhooks_router)


@app.get("/healthz", tags=["Health"])
async def health_check() -> dict[str, str]:
    """Basic health check endpoint."""
    return {"status": "ok"}
