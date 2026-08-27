# packages/agents/src/tools/mcp_clients.py
"""MCP-compliant LangChain tools for graph traversal and source control inspection."""

from typing import Any

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

    # ponytail: realistic mock commit diff showing a thread pool starvation bug in database connection pooling
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
