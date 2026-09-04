# apps/api/src/core/idempotency.py
"""Redis-backed webhook idempotency and deduplication engine."""

from collections.abc import AsyncIterator
import hashlib
import os
from typing import Annotated

from fastapi import Depends, Header, HTTPException, Request, status
import redis.asyncio as aioredis
from redis.asyncio import Redis
import structlog

logger = structlog.get_logger(__name__)

# Default TTL: 24 hours (86400 seconds)
DEFAULT_IDEMPOTENCY_TTL: int = 86400


class DuplicateWebhookError(Exception):
    """Raised when an incoming webhook contains an idempotency key that has already been processed or locked."""

    def __init__(self, key: str) -> None:
        self.key = key
        super().__init__(f"Duplicate webhook detected for idempotency key: {key}")


async def get_redis_client() -> AsyncIterator[Redis]:
    """Provide an asynchronous Redis client instance."""
    # ponytail: default to localhost:6379 for local dev, inject via REDIS_URL in production
    redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    client: Redis = aioredis.from_url(redis_url, decode_responses=True)
    try:
        yield client
    finally:
        await client.aclose()


async def check_and_lock_idempotency(
    redis_client: Redis,
    idempotency_key: str,
    ttl: int = DEFAULT_IDEMPOTENCY_TTL,
) -> bool:
    """Atomically claim an idempotency key using Redis SET NX.

    Args:
        redis_client: Active async Redis connection client.
        idempotency_key: Unique identifier string for the incoming request/payload.
        ttl: Time-to-live in seconds before the key expires (defaults to 24h).

    Returns:
        True if the key was successfully acquired.

    Raises:
        DuplicateWebhookError: If the key already exists in Redis.
    """
    namespaced_key: str = f"idempotency:{idempotency_key}"
    is_set = await redis_client.set(namespaced_key, "locked", nx=True, ex=ttl)

    if not is_set:
        logger.warning("duplicate_webhook_rejected", idempotency_key=idempotency_key)
        raise DuplicateWebhookError(key=idempotency_key)

    logger.info("idempotency_key_locked", idempotency_key=idempotency_key, ttl=ttl)
    return True


async def require_idempotency(
    request: Request,
    redis_client: Annotated[Redis, Depends(get_redis_client)],
    x_idempotency_key: Annotated[str | None, Header(alias="X-Idempotency-Key")] = None,
) -> str:
    """FastAPI dependency to enforce idempotency on incoming webhook endpoints.

    Extracts `X-Idempotency-Key` header if present; otherwise computes a SHA-256
    digest over the raw request body as a deterministic fallback.

    Args:
        request: Incoming FastAPI request.
        redis_client: Injected Redis client.
        x_idempotency_key: Optional custom idempotency key header.

    Returns:
        The locked idempotency key.

    Raises:
        HTTPException: 409 Conflict if duplicate request detected.
    """
    header_key = (
        x_idempotency_key
        or request.headers.get("x-idempotency-key")
        or request.headers.get("idempotency-key")
    )
    if header_key and header_key.strip():
        key: str = header_key.strip()
    else:
        body: bytes = await request.body()
        key = hashlib.sha256(body).hexdigest()

    try:
        await check_and_lock_idempotency(redis_client=redis_client, idempotency_key=key)
    except DuplicateWebhookError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc

    return key
