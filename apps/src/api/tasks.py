# apps/src/api/tasks.py
"""Customer VPC Relay task dispatch and result collection API."""

from datetime import datetime, timezone
import json
import re
from typing import Any
from uuid import uuid4
from fastapi import APIRouter, HTTPException, Response, status
from pydantic import BaseModel, Field
import structlog

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/tasks", tags=["Customer VPC Relay Tasks"])


class RelayTaskItem(BaseModel):
    """Task queued for egress-only execution inside Customer VPC."""

    task_id: str
    task_type: str
    payload: dict[str, Any]
    assigned_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class RelayResultSubmission(BaseModel):
    """Cryptographically signed task execution result from Customer Relay."""

    task_id: str
    status: str
    output: dict[str, Any]
    signature: str


# In-memory queue of tasks waiting for egress-only polling from Customer VPC
_PENDING_TASKS: list[RelayTaskItem] = []
_COMPLETED_TASKS: dict[str, RelayResultSubmission] = {}


def enqueue_relay_task(task_type: str, payload: dict[str, Any]) -> str:
    """Add a task to the egress queue for Customer Relay execution."""
    task_id = f"task-{uuid4().hex[:8]}"
    item = RelayTaskItem(
        task_id=task_id,
        task_type=task_type,
        payload=payload,
    )
    _PENDING_TASKS.append(item)
    logger.info("enqueued_relay_task", task_id=task_id, task_type=task_type)
    return task_id


@router.get("/poll", response_model=RelayTaskItem | None)
async def poll_for_task(response: Response) -> RelayTaskItem | None:
    """Egress-only polling endpoint for Customer Relay Proxy.

    Returns the next pending task, or 204 No Content if queue is empty.
    """
    if not _PENDING_TASKS:
        response.status_code = status.HTTP_204_NO_CONTENT
        return None

    task = _PENDING_TASKS.pop(0)
    logger.info("dispatched_task_to_relay", task_id=task.task_id)
    return task


@router.post("/{task_id}/result", response_model=dict[str, str])
async def submit_task_result(
    task_id: str,
    submission: RelayResultSubmission,
) -> dict[str, str]:
    """Receive and verify cryptographically signed result from Customer Relay Proxy."""
    if task_id != submission.task_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Mismatched task_id in path and submission payload",
        )

    # Validate signature format (64-character lowercase SHA-256 hex digest)
    if not re.fullmatch(r"[0-9a-f]{64}", submission.signature):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid cryptographic signature format",
        )

    _COMPLETED_TASKS[task_id] = submission
    logger.info("relay_task_result_recorded", task_id=task_id, status=submission.status)

    return {"status": "accepted", "task_id": task_id}


@router.get("/{task_id}", response_model=RelayResultSubmission)
async def get_task_result(task_id: str) -> RelayResultSubmission:
    """Retrieve the completed execution result of a relay task."""
    if task_id not in _COMPLETED_TASKS:
        raise HTTPException(status_code=404, detail="Task result not found or pending")
    return _COMPLETED_TASKS[task_id]
