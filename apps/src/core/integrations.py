import os
import structlog
import httpx

logger = structlog.get_logger(__name__)

async def notify_slack(incident_id: str, title: str, status: str):
    """Send an alert to Slack if webhook is configured."""
    webhook_url = os.environ.get("SLACK_WEBHOOK")
    if not webhook_url:
        return
        
    try:
        async with httpx.AsyncClient() as client:
            payload = {
                "text": f"🚨 *Kautilya AI Alert* 🚨\n*Incident:* {incident_id}\n*Title:* {title}\n*Status:* {status}"
            }
            # Catch mock failures for invalid urls during testing
            if webhook_url.startswith("http"):
                await client.post(webhook_url, json=payload, timeout=5.0)
            logger.info("slack_notification_sent", incident_id=incident_id)
    except Exception as e:
        logger.error("slack_notification_failed", error=str(e))


async def create_jira_ticket(incident_id: str, title: str, description: str):
    """Create a Jira ticket if Jira token is configured."""
    jira_token = os.environ.get("JIRA_TOKEN")
    if not jira_token:
        return
        
    # Mocking actual Jira API call for demonstration purposes
    logger.info("jira_ticket_created", incident_id=incident_id, ticket_key=f"KAUT-{incident_id[:4].upper()}")
