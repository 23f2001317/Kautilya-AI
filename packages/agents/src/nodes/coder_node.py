# packages/agents/src/nodes/coder_node.py
"""Coder node synthesizing targeted code and configuration remediation patches."""

from typing import Any
from langchain_core.messages import AIMessage
from langchain_google_genai import ChatGoogleGenerativeAI
import structlog
import os

from ..state import AgentState

logger = structlog.get_logger(__name__)


def coder_step(state: AgentState) -> dict[str, Any]:
    """Generate a targeted code or configuration patch addressing the diagnosed hypothesis.

    Args:
        state: Current agent workflow state.

    Returns:
        Partial state update containing proposed_patch, pending verification status, and messages.
    """
    hypothesis = state.get("hypothesis", "")
    alert = state.get("alert", {})
    service_name = str(alert.get("service_name", "auth-service"))
    retry_count = state.get("retry_count", 0)

    logger.info("executing_coder_step", service=service_name, retry_count=retry_count)

    # Synthesize patch tailored to diagnosed archetype
    gemini_key = os.environ.get("GEMINI_API_KEY")
    if gemini_key:
        llm = ChatGoogleGenerativeAI(model="gemini-1.5-pro", api_key=gemini_key)
        prompt = f"""
        You are an elite SRE generating a remediation patch.
        Service: {service_name}
        Attempt: {retry_count + 1}
        Hypothesis: {hypothesis}
        
        Write a precise git unified diff patch to fix the issue described in the hypothesis.
        Output ONLY the raw diff. No markdown blocks, no intro, no outro. Just the patch.
        """
        response = llm.invoke(prompt)
        proposed_patch = response.content.strip()
        if proposed_patch.startswith("```diff"):
            proposed_patch = proposed_patch.replace("```diff", "", 1).strip()
        if proposed_patch.endswith("```"):
            proposed_patch = proposed_patch[:-3].strip()
    else:
        if "redis" in hypothesis.lower() or "cache" in hypothesis.lower():
            if retry_count == 0:
                proposed_patch = """diff --git a/src/cache/client.py b/src/cache/client.py
--- a/src/cache/client.py
+++ b/src/cache/client.py
@@ -12,4 +12,4 @@ class RedisConfig:
-    socket_timeout: float = 0.2
-    max_connections: int = 10
+    socket_timeout: float = 1.0
+    max_connections: int = 25
"""
            else:
                proposed_patch = """diff --git a/src/cache/client.py b/src/cache/client.py
--- a/src/cache/client.py
+++ b/src/cache/client.py
@@ -12,4 +12,6 @@ class RedisConfig:
-    socket_timeout: float = 0.2
-    max_connections: int = 10
+    socket_timeout: float = 2.0
+    max_connections: int = 100
+    retry_on_timeout: bool = True
"""
        elif "gateway" in hypothesis.lower() or "socket timeout" in hypothesis.lower():
            if retry_count == 0:
                proposed_patch = """diff --git a/src/network/client.py b/src/network/client.py
--- a/src/network/client.py
+++ b/src/network/client.py
@@ -15,4 +15,4 @@ class HTTPClientConfig:
-    request_timeout_ms: int = 100
-    max_retries: int = 0
+    request_timeout_ms: int = 500
+    max_retries: int = 2
"""
            else:
                proposed_patch = """diff --git a/src/network/client.py b/src/network/client.py
--- a/src/network/client.py
+++ b/src/network/client.py
@@ -15,4 +15,6 @@ class HTTPClientConfig:
-    request_timeout_ms: int = 100
-    max_retries: int = 0
+    request_timeout_ms: int = 2000
+    max_retries: int = 3
+    circuit_breaker_enabled: bool = True
"""
        elif "memory" in hypothesis.lower() or "buffer" in hypothesis.lower():
            proposed_patch = """diff --git a/src/worker/listener.py b/src/worker/listener.py
--- a/src/worker/listener.py
+++ b/src/worker/listener.py
@@ -20,4 +20,6 @@ class EventBuffer:
-    max_buffer_size: int = 1_000_000
-    auto_evict: bool = False
+    max_buffer_size: int = 10_000
+    auto_evict: bool = True
+    eviction_policy: str = "lru"
"""
        else:
            # Default database connection pool remediation
            if retry_count == 0:
                proposed_patch = """diff --git a/src/db/pool.py b/src/db/pool.py
--- a/src/db/pool.py
+++ b/src/db/pool.py
@@ -10,4 +10,4 @@ class DBConfig:
-    max_connections: int = 2
-    pool_timeout: int = 2
+    max_connections: int = 20
+    pool_timeout: int = 15
"""
            else:
                proposed_patch = """diff --git a/src/db/pool.py b/src/db/pool.py
--- a/src/db/pool.py
+++ b/src/db/pool.py
@@ -10,4 +10,6 @@ class DBConfig:
-    max_connections: int = 2
-    pool_timeout: int = 2
+    max_connections: int = 50
+    pool_timeout: int = 30
+    retry_backoff: float = 0.5
"""

    msg = AIMessage(
        content=(
            f"[Coder] Synthesized remediation patch for {service_name} (attempt {retry_count + 1}):\n"
            f"Hypothesis context: {hypothesis[:100]}...\n"
            f"Patch diff:\n{proposed_patch}"
        )
    )

    return {
        "proposed_patch": proposed_patch,
        "verification_status": "pending",
        "messages": [msg],
    }
