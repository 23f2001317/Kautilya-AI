# apps/src/api/alerts_sim.py
"""Simulated alert trigger generating genuinely varied realistic SRE incidents."""

import random
from typing import Any
from uuid import uuid4
from fastapi import APIRouter
from pydantic import BaseModel, Field
import structlog
import os
import requests

from ..core.orchestrator import orchestrator

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/api/alerts", tags=["Alert Ingestion & Simulation"])


class SimulateAlertRequest(BaseModel):
    archetype: str | None = Field(
        default=None,
        description="One of: 'db_pool', 'redis_cache', 'gateway_timeout', 'memory_leak' or None for random",
    )


ARCHETYPES = [
    {
        "archetype": "db_pool",
        "title": "Database Connection Pool Starvation on {service}",
        "severity": "critical",
        "commit": "c0ffee123",
        "description": "504 Gateway Timeouts detected. Active database connection pool saturated at 100%.",
        "failure_category": "resource_exhaustion",
    },
    {
        "archetype": "redis_cache",
        "title": "Redis Cache Eviction Surge & Latency Spike on {service}",
        "severity": "high",
        "commit": "d4e5f6a7",
        "description": "Cache miss rate surged to 85% after recent deployment. Downstream database query queue backlog growing.",
        "failure_category": "cache_saturation",
    },
    {
        "archetype": "gateway_timeout",
        "title": "Circuit Breaker Trip & Upstream Timeouts on {service}",
        "severity": "critical",
        "commit": "a1b2c3d4",
        "description": "HTTP client connection timeout set too aggressively (100ms) causing cascading 503 Service Unavailable errors.",
        "failure_category": "network_partition",
    },
    {
        "archetype": "memory_leak",
        "title": "Memory Growth Anomaly & OOM Kill Risk on {service}",
        "severity": "high",
        "commit": "f9e8d7c6",
        "description": "Unbounded event listener buffer accumulation detected in worker loop. RSS memory at 92% of cgroup limit.",
        "failure_category": "memory_leak",
    },
]


@router.post("/simulate", response_model=dict[str, Any])
async def simulate_incident_alert(payload: SimulateAlertRequest | None = None) -> dict[str, Any]:
    """Trigger a real end-to-end remediation pipeline with a realistic, varied alert payload."""
    chosen_archetype = payload.archetype if payload and payload.archetype else None

    # Pick matching archetype or select random
    selected = None
    if chosen_archetype:
        for arch in ARCHETYPES:
            if arch["archetype"] == chosen_archetype:
                selected = arch
                break

    if not selected:
        selected = random.choice(ARCHETYPES)

    # Fetch real latest commit if possible
    commit_hash = selected["commit"]
    github_token = os.environ.get("GITHUB_TOKEN")
    repo_url = os.environ.get("TARGET_REPO_URL", "https://github.com/23f2001317/vehicle-parking-v2.git")
    
    # Infer target service name from repo url
    service_name = repo_url.split("/")[-1].replace(".git", "") if "/" in repo_url else "unknown-service"
    
    if github_token and "github.com/" in repo_url:
        parts = repo_url.replace(".git", "").split("github.com/")
        if len(parts) > 1:
            owner_repo = parts[1]
            try:
                url = f"https://api.github.com/repos/{owner_repo}/commits"
                headers = {"Authorization": f"token {github_token}"}
                response = requests.get(url, headers=headers, timeout=5)
                if response.status_code == 200 and len(response.json()) > 0:
                    commit_hash = response.json()[0]["sha"]
            except Exception as e:
                logger.warning("failed_to_fetch_latest_commit", error=str(e))

    unique_id = f"inc-{service_name[:4]}-{uuid4().hex[:6]}"
    
    formatted_title = selected["title"].format(service=service_name)
    
    alert_data = {
        "id": unique_id,
        "source": "datadog",
        "external_id": commit_hash,
        "service_name": service_name,
        "title": formatted_title,
        "severity": selected["severity"],
        "description": selected["description"],
        "failure_category": selected["failure_category"],
        "raw_payload": selected,
    }

    logger.info(
        "simulating_realistic_alert",
        incident_id=unique_id,
        service=service_name,
        archetype=selected["archetype"],
    )

    # Process through the genuine multi-plane LangGraph orchestrator
    incident = await orchestrator.process_alert(alert_data)

    return {
        "status": "triggered",
        "incident_id": incident.id,
        "service_name": incident.service_name,
        "title": incident.title,
        "status_code": incident.status,
        "confidence_score": incident.confidence_score,
        "hypothesis": incident.hypothesis,
    }
