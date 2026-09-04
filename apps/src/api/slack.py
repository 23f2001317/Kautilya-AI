# apps/src/api/slack.py
"""Slack interactive webhook integration for SRE remediation actions."""

from typing import Any
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
import structlog

from .incidents import ApprovalPayload, RejectionPayload, approve_incident_patch, reject_incident_patch

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/api/integrations/slack", tags=["Slack Integration"])


class SlackActionPayload(BaseModel):
    """Payload representing an interactive button action clicked in Slack."""

    incident_id: str
    user_id: str = Field(..., description="Slack user ID or email")
    action: str = Field(..., description="'approve', 'reject', or 'refine'")
    notes: str | None = None


@router.post("/actions", status_code=status.HTTP_200_OK)
async def handle_slack_action(payload: SlackActionPayload) -> dict[str, Any]:
    """Handle interactive Slack approval, rejection, or refinement actions."""
    incident_id = payload.incident_id
    action = payload.action.lower()

    logger.info("slack_action_received", incident_id=incident_id, action=action, user=payload.user_id)

    if action == "approve":
        approval = ApprovalPayload(
            signer_id=f"slack:{payload.user_id}",
            comments=payload.notes or "Approved via Slack Interactive Message",
        )
        updated = await approve_incident_patch(incident_id, approval)
        return {
            "response_type": "in_channel",
            "text": f":white_check_mark: Incident *{incident_id}* approved by <@{payload.user_id}>. Pull Request created: {updated.pr_url}",
        }

    if action in ("reject", "refine"):
        rejection = RejectionPayload(
            signer_id=f"slack:{payload.user_id}",
            reason=payload.notes or f"Action '{action}' initiated from Slack.",
        )
        await reject_incident_patch(incident_id, rejection)
        return {
            "response_type": "in_channel",
            "text": f":warning: Remediation for incident *{incident_id}* {action}d by <@{payload.user_id}>.",
        }

    raise HTTPException(status_code=400, detail=f"Unsupported Slack action: {action}")
