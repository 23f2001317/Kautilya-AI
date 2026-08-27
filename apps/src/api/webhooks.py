# apps/api/src/api/webhooks.py
"""Webhook ingestion endpoints for telemetry and source control events."""

from datetime import datetime, timezone
from typing import Annotated, Any, Literal
from uuid import uuid4

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel, ConfigDict, Field
import structlog

from ..core.idempotency import require_idempotency

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/webhooks", tags=["Webhooks"])


# --- Pydantic Schemas ---


class DatadogAlertPayload(BaseModel):
    """Incoming alert payload structure sent by Datadog webhooks."""

    model_config = ConfigDict(extra="ignore")

    id: str = Field(..., description="Unique alert identifier from Datadog")
    event_title: str = Field(..., description="Title of the triggered monitor/alert")
    body: str = Field(..., description="Details and context of the alert")
    priority: str = Field(default="normal", description="Alert priority e.g. normal, low, high")
    alert_type: str = Field(
        default="error", description="Type of alert e.g. error, warning, info, success"
    )
    service: str = Field(default="unknown-service", description="Impacted microservice or tag")
    tags: list[str] = Field(default_factory=list, description="Associated monitor tags")
    date: int | None = Field(default=None, description="Epoch timestamp of the event")


class GitHubCommit(BaseModel):
    """Commit metadata from GitHub push payloads."""

    id: str
    message: str
    timestamp: str
    author: dict[str, str] = Field(default_factory=dict)


class GitHubWebhookPayload(BaseModel):
    """Incoming event payload sent by GitHub webhooks (Push or Action)."""

    model_config = ConfigDict(extra="ignore")

    ref: str | None = Field(default=None, description="Git reference e.g. refs/heads/main")
    head_commit: GitHubCommit | None = Field(
        default=None, description="Head commit metadata"
    )
    repository: dict[str, Any] = Field(
        default_factory=dict, description="Repository information"
    )
    action: str | None = Field(default=None, description="Action for issue/PR events")
    sender: dict[str, Any] = Field(default_factory=dict, description="Event sender info")


class CanonicalAlert(BaseModel):
    """Normalized internal representation of an ingested telemetry or platform event."""

    id: str = Field(
        default_factory=lambda: str(uuid4()), description="Internal unique canonical ID"
    )
    source: Literal["datadog", "github"] = Field(
        ..., description="Origin system of the incoming alert"
    )
    external_id: str = Field(
        ..., description="Identifier assigned by the external provider"
    )
    service_name: str = Field(
        ..., description="Target service affected by or related to the event"
    )
    title: str = Field(..., description="Summarized alert/event title")
    severity: str = Field(
        ..., description="Normalized severity e.g. critical, high, medium, low, info"
    )
    description: str = Field(
        ..., description="Explanatory details or message body"
    )
    raw_payload: dict[str, Any] = Field(
        ..., description="Full original payload for auditability"
    )
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Ingestion UTC timestamp",
    )


class IngestionResponse(BaseModel):
    """API response acknowledging successful webhook ingestion."""

    status: str = "received"
    idempotency_key: str
    canonical_alert_id: str


# --- Event Queue Publisher Mock ---


async def publish_to_event_queue(alert: CanonicalAlert) -> None:
    """Publish the canonical alert into the asynchronous event processing queue.

    Args:
        alert: Canonical normalized alert to dispatch.
    """
    # ponytail: log-based queue mock for Phase 1; replace with RabbitMQ/Celery publisher in Phase 2
    logger.info(
        "published_canonical_alert_to_queue",
        canonical_id=alert.id,
        source=alert.source,
        service_name=alert.service_name,
        severity=alert.severity,
        title=alert.title,
    )


# --- Route Endpoints ---


@router.post(
    "/datadog",
    response_model=IngestionResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Ingest Datadog Monitor Alert",
)
async def ingest_datadog_webhook(
    payload: DatadogAlertPayload,
    idempotency_key: Annotated[str, Depends(require_idempotency)],
) -> IngestionResponse:
    """Receive, deduplicate, and normalize Datadog monitor webhook alerts.

    Args:
        payload: Validated Datadog alert payload.
        idempotency_key: Redis-validated idempotency key from dependency.

    Returns:
        IngestionResponse containing acceptance status and canonical alert ID.
    """
    severity_map = {
        "error": "critical",
        "warning": "medium",
        "info": "info",
        "success": "info",
    }
    normalized_severity = severity_map.get(payload.alert_type.lower(), "high")

    canonical_alert = CanonicalAlert(
        source="datadog",
        external_id=payload.id,
        service_name=payload.service,
        title=payload.event_title,
        severity=normalized_severity,
        description=payload.body,
        raw_payload=payload.model_dump(),
    )

    await publish_to_event_queue(canonical_alert)

    return IngestionResponse(
        status="received",
        idempotency_key=idempotency_key,
        canonical_alert_id=canonical_alert.id,
    )


@router.post(
    "/github",
    response_model=IngestionResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Ingest GitHub Webhook Event",
)
async def ingest_github_webhook(
    payload: GitHubWebhookPayload,
    idempotency_key: Annotated[str, Depends(require_idempotency)],
) -> IngestionResponse:
    """Receive, deduplicate, and normalize GitHub repository push and deployment webhooks.

    Args:
        payload: Validated GitHub webhook payload.
        idempotency_key: Redis-validated idempotency key from dependency.

    Returns:
        IngestionResponse containing acceptance status and canonical alert ID.
    """
    repo_name = str(payload.repository.get("name", "unknown-repo"))
    commit_id = payload.head_commit.id if payload.head_commit else str(uuid4())
    commit_msg = payload.head_commit.message if payload.head_commit else "GitHub event triggered"

    canonical_alert = CanonicalAlert(
        source="github",
        external_id=commit_id,
        service_name=repo_name,
        title=f"GitHub Event on {repo_name}",
        severity="info",
        description=commit_msg,
        raw_payload=payload.model_dump(),
    )

    await publish_to_event_queue(canonical_alert)

    return IngestionResponse(
        status="received",
        idempotency_key=idempotency_key,
        canonical_alert_id=canonical_alert.id,
    )
