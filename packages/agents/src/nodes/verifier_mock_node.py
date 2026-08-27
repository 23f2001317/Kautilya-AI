# packages/agents/src/nodes/verifier_mock_node.py
"""Verifier node simulating automated sandbox execution and testing."""

from typing import Any, Literal

from langchain_core.messages import AIMessage
import structlog

from ..state import AgentState

logger = structlog.get_logger(__name__)


def verifier_mock_step(state: AgentState) -> dict[str, Any]:
    """Simulate sandbox execution and verification against integration tests.

    Args:
        state: Current agent workflow state.

    Returns:
        Partial state update containing updated verification_status, retry_count, and messages.
    """
    retry_count = state.get("retry_count", 0)
    proposed_patch = state.get("proposed_patch", "")

    logger.info("executing_verifier_step", retry_count=retry_count)

    # ponytail: simulate first attempt failing (e.g. insufficient pool under high concurrency),
    # and second attempt passing to test self-healing cycle.
    status: Literal["passed", "failed"]
    if retry_count == 0 and "max_connections: int = 20" in proposed_patch:
        status = "failed"
        new_retry_count = retry_count + 1
        msg = AIMessage(
            content=(
                f"[Verifier] Sandbox Run FAILED (Attempt {new_retry_count}). "
                "Integration test 'test_concurrency_load_100_qps' failed: pool timeout under heavy load."
            )
        )
    else:
        status = "passed"
        new_retry_count = retry_count
        msg = AIMessage(
            content=(
                f"[Verifier] Sandbox Run PASSED! "
                "All 24 integration tests and health checks succeeded."
            )
        )

    return {
        "verification_status": status,
        "retry_count": new_retry_count,
        "messages": [msg],
    }
