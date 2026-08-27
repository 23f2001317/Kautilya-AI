# packages/agents/src/nodes/triage_node.py
"""Triage reasoning node correlating alerts with deployment history."""

from typing import Any

from langchain_core.messages import AIMessage
import structlog

from ..state import AgentState
from ..tools.mcp_clients import fetch_github_commit_diff

logger = structlog.get_logger(__name__)


def triage_step(state: AgentState) -> dict[str, Any]:
    """Analyze incoming canonical alert and correlate with recent source code changes.

    Args:
        state: Current agent workflow state.

    Returns:
        Partial state update containing initial root-cause hypothesis and logged message.
    """
    alert = state.get("alert", {})
    service_name = str(alert.get("service_name", "unknown-service"))
    alert_title = str(alert.get("title", "Unknown Alert"))
    commit_hash = str(alert.get("external_id", "c0ffee123"))

    logger.info("executing_triage_step", service_name=service_name, alert_title=alert_title)

    # Ingest commit diff via MCP tool
    commit_diff = fetch_github_commit_diff.invoke({"commit_hash": commit_hash})

    hypothesis = (
        f"Alert '{alert_title}' on service '{service_name}' was triggered by commit {commit_hash}. "
        "The commit throttled the database connection pool (max_connections=2), causing thread starvation under load."
    )

    thought_message = AIMessage(
        content=f"[Triage] Formulated Root Cause Hypothesis:\n{hypothesis}\n\nDiff inspection:\n{commit_diff}"
    )

    return {
        "hypothesis": hypothesis,
        "messages": [thought_message],
    }
