# apps/src/api/topology.py
"""Dynamic system topology API backed by Neo4j and persistent database repository."""

from typing import Any
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
import structlog
from sqlalchemy import select

from ..core.database import (
    TopologyEdgeRecord,
    TopologyNodeRecord,
    db_get_topology,
    db_list_incidents,
    get_session_factory,
)

try:
    from packages.graph_core.src.neo4j_client import Neo4jManager
    _NEO4J_AVAILABLE = True
except ImportError:
    _NEO4J_AVAILABLE = False

logger = structlog.get_logger(__name__)

router = APIRouter(tags=["Topology Knowledge Graph"])


class NewNodePayload(BaseModel):
    """Payload to add a new service to the live topology."""

    name: str
    node_type: str = Field(default="service", description="service, database, cache, or frontend")
    tier: str = Field(default="backend")
    criticality: str = Field(default="high")
    connect_to: str | None = Field(default=None, description="Target service to establish a CALLS edge to")


@router.get("/topology", response_model=dict[str, Any])
@router.get("/api/topology", response_model=dict[str, Any])
async def get_live_topology() -> dict[str, Any]:
    """Retrieve dynamic system dependency topology enriched with active incident alerts."""
    nodes, edges = await db_get_topology()

    # Query active incidents to dynamically compute node health status
    active_incidents = await db_list_incidents()
    alert_services = {
        inc.service_name: inc.severity
        for inc in active_incidents
        if inc.status in ("triaging", "patch_ready")
    }

    # Identify impacted upstream/downstream services
    impacted_services: set[str] = set()
    for inc in active_incidents:
        if inc.status in ("triaging", "patch_ready"):
            impacted_services.update(inc.impacted_services)

    # Assign dynamic health status
    enriched_nodes = []
    for node in nodes:
        name = node["name"]
        if name in alert_services:
            status = "alert"
        elif name in impacted_services:
            status = "impacted"
        else:
            status = "healthy"

        enriched_nodes.append(
            {
                "id": node["id"],
                "name": name,
                "label": name,
                "type": node["type"],
                "tier": node["tier"],
                "status": status,
                "criticality": node["criticality"],
            }
        )

    return {
        "nodes": enriched_nodes,
        "edges": edges,
        "total_nodes": len(enriched_nodes),
        "total_edges": len(edges),
        "active_alerts": list(alert_services.keys()),
    }


@router.post("/api/topology/nodes", response_model=dict[str, Any])
async def add_topology_node(payload: NewNodePayload) -> dict[str, Any]:
    """Add a new microservice node to the persistent topology graph."""
    session_factory = get_session_factory()
    node_id = f"node-{payload.name.lower().replace(' ', '-')}"

    async with session_factory() as session:
        # Check if node exists
        existing = await session.execute(
            select(TopologyNodeRecord).where(TopologyNodeRecord.name == payload.name)
        )
        if existing.scalar_one_or_none():
            raise HTTPException(status_code=409, detail=f"Node '{payload.name}' already exists")

        new_node = TopologyNodeRecord(
            id=node_id,
            name=payload.name,
            node_type=payload.node_type,
            tier=payload.tier,
            criticality=payload.criticality,
        )
        session.add(new_node)

        # If connect_to is provided, create an edge
        if payload.connect_to:
            edge_id = f"edge-{payload.name}-to-{payload.connect_to}"
            new_edge = TopologyEdgeRecord(
                id=edge_id,
                source=payload.name,
                target=payload.connect_to,
                relationship="CALLS",
            )
            session.add(new_edge)

        await session.commit()
        logger.info("added_dynamic_topology_node", name=payload.name, node_id=node_id)

    return {"status": "created", "node_id": node_id, "name": payload.name}
