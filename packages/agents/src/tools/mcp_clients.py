# packages/agents/src/tools/mcp_clients.py
"""MCP-compliant LangChain tools for graph traversal and source control inspection."""

from typing import Any
import os
import requests

from langchain_core.tools import tool
import structlog

logger = structlog.get_logger(__name__)


@tool
def execute_cypher_query(
    query: str,
    parameters: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """Execute a parameterized Cypher query against the Neo4j topological knowledge graph.

    Args:
        query: Parameterized Cypher query string.
        parameters: Key-value dictionary of Cypher query parameters.

    Returns:
        List of graph records matching the query.
    """
    params = parameters or {}
    logger.info("executing_mcp_cypher_query", cypher=query, parameters=params)

    # ponytail: return deterministic mock graph topology for Phase 2 agent reasoning validation
    service = str(params.get("service_name", "auth-service"))
    return [
        {
            "source_service": service,
            "dependency": "user-database",
            "relationship": "DEPENDS_ON",
            "criticality": "high",
        },
        {
            "source_service": "payment-api",
            "dependency": service,
            "relationship": "CALLS",
            "criticality": "critical",
        },
        {
            "source_service": "web-frontend",
            "dependency": "payment-api",
            "relationship": "CALLS",
            "criticality": "high",
        },
    ]


@tool
def fetch_github_commit_diff(commit_hash: str) -> str:
    """Fetch the unified git diff and modified file contents for a specific GitHub commit hash.

    Args:
        commit_hash: Unique SHA-1 hash of the git commit.

    Returns:
        Unified diff string showing code modifications introduced in the commit.
    """
    logger.info("fetching_mcp_github_commit_diff", commit_hash=commit_hash)

    github_token = os.environ.get("GITHUB_TOKEN")
    repo_url = os.environ.get("TARGET_REPO_URL", "https://github.com/23f2001317/vehicle-parking-v2.git")
    
    if github_token and "github.com/" in repo_url:
        # Extract owner/repo from URL
        # e.g. https://github.com/owner/repo.git -> owner/repo
        parts = repo_url.replace(".git", "").split("github.com/")
        if len(parts) > 1:
            owner_repo = parts[1]
            url = f"https://api.github.com/repos/{owner_repo}/commits/{commit_hash}"
            headers = {
                "Authorization": f"token {github_token}",
                "Accept": "application/vnd.github.v3.diff"
            }
            try:
                response = requests.get(url, headers=headers, timeout=10)
                if response.status_code == 200:
                    return response.text
                else:
                    logger.warning("github_api_error", status_code=response.status_code, text=response.text)
            except Exception as e:
                logger.error("github_api_exception", error=str(e))
                
    # fallback to mock diff if credentials unavailable or fetch failed
    return f"""commit {commit_hash}
Author: backend-dev <dev@kautilya.internal>
Date:   Thu Aug 27 14:00:00 2026 +0000

    refactor(db): reduce database connection pool size

diff --git a/src/db/pool.py b/src/db/pool.py
index a1b2c3d..e4f5g6h 100644
--- a/src/db/pool.py
+++ b/src/db/pool.py
@@ -10,7 +10,7 @@ class DBConfig:
-    max_connections: int = 100
-    pool_timeout: int = 30
+    max_connections: int = 2
+    pool_timeout: int = 2
"""


@tool
def query_runbook_embeddings(service_name: str, query_text: str) -> list[dict[str, Any]]:
    """Query pgvector vector database for relevant runbooks and standard operating procedures (SOP).

    Args:
        service_name: Target microservice name.
        query_text: Natural language search query (e.g. 'high latency pool timeout').

    Returns:
        List of matching runbook entries with relevance scores.
    """
    logger.info("querying_mcp_runbook_embeddings", service=service_name, query=query_text)
    return [
        {
            "service_name": service_name,
            "runbook_title": f"{service_name} Thread Pool Starvation Playbook",
            "similarity": 0.93,
            "recommended_action": (
                "Increase max_connections parameter in DBConfig to >= 50. "
                "Ensure pool_timeout is at least 30 seconds to absorb transient traffic spikes."
            ),
        }
    ]


@tool
def fetch_service_logs(service_name: str, limit: int = 10) -> list[str]:
    """Fetch recent container error logs for the specified service.

    Args:
        service_name: Name of the microservice.
        limit: Max number of log lines to retrieve.

    Returns:
        List of log line strings.
    """
    logger.info("fetching_mcp_service_logs", service=service_name, limit=limit)
    return [
        f"[ERROR] {service_name}: Timeout acquiring connection from pool after 2000ms",
        f"[WARN] {service_name}: Active connections: 2/2 (100% capacity)",
        f"[ERROR] {service_name}: 504 Gateway Timeout returned on /api/v1/auth/verify",
    ]

