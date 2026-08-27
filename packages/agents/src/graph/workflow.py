# packages/agents/src/graph/workflow.py
"""Autonomous SRE incident remediation state graph with cyclic self-healing."""

from typing import Any, Literal

from langchain_core.messages import HumanMessage
from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph
import structlog

from ..nodes.blast_radius_node import blast_radius_step
from ..nodes.coder_node import coder_step
from ..nodes.triage_node import triage_step
from ..nodes.verifier_mock_node import verifier_mock_step
from ..state import AgentState

logger = structlog.get_logger(__name__)


def route_verification(state: AgentState) -> Literal["coder", "__end__"]:
    """Evaluate verification outcome and determine self-healing retry or terminal route.

    Args:
        state: Current agent state after verifier node evaluation.

    Returns:
        "coder" to retry patch synthesis, or "__end__" to terminate.
    """
    verification_status = state.get("verification_status", "pending")
    retry_count = state.get("retry_count", 0)

    logger.info(
        "routing_verification_decision",
        status=verification_status,
        retry_count=retry_count,
    )

    if verification_status == "passed":
        logger.info("remediation_verified_successfully")
        return END

    if verification_status == "failed":
        if retry_count < 3:
            logger.warning(
                "remediation_failed_retrying",
                next_attempt=retry_count + 1,
            )
            return "coder"
        # Fail-closed safety boundary
        logger.error(
            "remediation_retry_exhausted_failing_closed",
            total_retries=retry_count,
        )
        return END

    return END


def create_incident_graph() -> CompiledStateGraph:
    """Build and compile the autonomous SRE incident resolution state graph.

    Returns:
        Compiled LangGraph StateGraph instance.
    """
    workflow = StateGraph(AgentState)

    # Register reasoning and execution nodes
    workflow.add_node("triage", triage_step)
    workflow.add_node("blast_radius", blast_radius_step)
    workflow.add_node("coder", coder_step)
    workflow.add_node("verifier", verifier_mock_step)

    # Establish linear triage and diagnostic pipeline
    workflow.add_edge(START, "triage")
    workflow.add_edge("triage", "blast_radius")
    workflow.add_edge("blast_radius", "coder")
    workflow.add_edge("coder", "verifier")

    # Add cyclic feedback loop with fail-closed safety guardrails
    workflow.add_conditional_edges(
        "verifier",
        route_verification,
        {
            "coder": "coder",
            END: END,
        },
    )

    return workflow.compile()


# Export compiled graph instance
incident_graph: CompiledStateGraph = create_incident_graph()


if __name__ == "__main__":
    # Executable demonstration block with sample CanonicalAlert
    sample_alert: dict[str, Any] = {
        "id": "alert-c0ffee-99",
        "source": "datadog",
        "external_id": "c0ffee123",
        "service_name": "auth-service",
        "title": "High Latency & Thread Pool Exhaustion on auth-service",
        "severity": "critical",
        "description": "504 Gateway Timeouts detected. DB pool saturation > 98%.",
        "raw_payload": {"monitor_id": 88419},
    }

    initial_state: AgentState = {
        "alert": sample_alert,
        "graph_context": [],
        "hypothesis": "",
        "proposed_patch": "",
        "verification_status": "pending",
        "retry_count": 0,
        "messages": [
            HumanMessage(
                content=f"Trigger incident remediation workflow for alert: {sample_alert['title']}"
            )
        ],
    }

    print("=== STARTING KAUTILYA AI INCIDENT REASONING GRAPH ===")
    final_state = incident_graph.invoke(initial_state)

    print("\n=== FINAL REASONING REPORT ===")
    print(f"Service:             {final_state['alert']['service_name']}")
    print(f"Hypothesis:          {final_state['hypothesis']}")
    print(f"Verification Status: {final_state['verification_status']}")
    print(f"Total Retries:       {final_state['retry_count']}")
    print(f"Proposed Patch:\n{final_state['proposed_patch']}")
    print(f"\nTotal Reasoning Messages: {len(final_state['messages'])}")
    for i, msg in enumerate(final_state["messages"], start=1):
        print(f"\n--- Message {i} [{msg.type}] ---")
        print(msg.content)
