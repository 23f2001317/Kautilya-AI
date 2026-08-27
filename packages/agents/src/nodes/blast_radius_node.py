# packages/agents/src/nodes/blast_radius_node.py
"""Blast radius calculation node discovering upstream and downstream topological impacts."""

from typing import Any

from langchain_core.messages import AIMessage
import structlog

from ..state import AgentState
from ..tools.mcp_clients import execute_cypher_query

logger = structlog.get_logger(__name__)


def blast_radius_step(state: AgentState) -> dict[str, Any]:
    """Execute topological queries across Neo4j to identify dependent microservices.

    Args:
        state: Current agent workflow state.

    Returns:
        Partial state update containing updated graph_context and diagnostic messages.
    """
    alert = state.get("alert", {})
    service_name = str(alert.get("service_name", "auth-service"))

    logger.info("executing_blast_radius_step", service_name=service_name)

    cypher_query = """
    MATCH (s:Service {name: $service_name})<-[:CALLS*1..3]-(caller:Service)
    RETURN caller.name AS caller_service, s.name AS target_service
    """
    parameters = {"service_name": service_name}

    # Execute MCP graph traversal
    topology_records = execute_cypher_query.invoke(
        {"query": cypher_query, "parameters": parameters}
    )

    downstream_services = [
        str(r.get("source_service", ""))
        for r in topology_records
        if r.get("source_service") != service_name
    ]

    msg = AIMessage(
        content=(
            f"[Blast Radius] Evaluated topology for '{service_name}'. "
            f"Identified {len(topology_records)} impacted relationships. "
            f"Critical downstream services: {', '.join(set(downstream_services))}"
        )
    )

    return {
        "graph_context": topology_records,
        "messages": [msg],
    }
