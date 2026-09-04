# apps/tests/test_phase2.py
"""Test verification for Phase 2: Agentic Reasoning & LangGraph Planners."""

from typing import Any
from unittest.mock import MagicMock, patch

from langchain_core.messages import HumanMessage
from packages.agents.src.graph.workflow import create_incident_graph, route_verification
from packages.agents.src.nodes.triage_node import triage_step
from packages.agents.src.state import AgentState, RootCauseHypothesis


def _make_sample_state(retry_count: int = 0, status: str = "pending") -> AgentState:
    return {
        "alert": {
            "id": "test-alert-1",
            "source": "datadog",
            "external_id": "c0ffee123",
            "service_name": "auth-service",
            "title": "High Thread Latency",
            "severity": "critical",
            "description": "Connection pool exhausted",
            "raw_payload": {},
        },
        "graph_context": [],
        "hypothesis": "",
        "structured_hypothesis": None,
        "proposed_patch": "",
        "verification_status": status,  # type: ignore[typeddict-item]
        "retry_count": retry_count,
        "messages": [HumanMessage(content="Start incident triage")],
    }


def test_triage_produces_structured_hypothesis() -> None:
    state = _make_sample_state()
    update = triage_step(state)

    assert "hypothesis" in update
    assert "structured_hypothesis" in update
    struct_data = update["structured_hypothesis"]
    assert struct_data is not None

    model = RootCauseHypothesis.model_validate(struct_data)
    assert model.service_name == "auth-service"
    assert model.failure_category == "resource_exhaustion"
    assert model.confidence_score >= 0.8
    assert model.culprit_commit == "c0ffee123"


def test_triage_recovers_from_tool_failure() -> None:
    state = _make_sample_state()
    mock_tool = MagicMock()
    mock_tool.invoke.side_effect = RuntimeError("GitHub API 503 Service Unavailable")
    with patch(
        "packages.agents.src.nodes.triage_node.fetch_github_commit_diff",
        mock_tool,
    ):
        update = triage_step(state)
        assert "Diff retrieval failed" in update["messages"][0].content
        assert update["structured_hypothesis"] is not None


def test_verification_routing_rules() -> None:
    # Passed -> TERMINATE (__end__)
    passed_state = _make_sample_state(retry_count=1, status="passed")
    assert route_verification(passed_state) == "__end__"

    # Failed under 3 attempts -> RETRY (coder)
    failed_state_1 = _make_sample_state(retry_count=1, status="failed")
    assert route_verification(failed_state_1) == "coder"

    # Failed at >= 3 attempts -> FAIL-CLOSED TERMINATE (__end__)
    exhausted_state = _make_sample_state(retry_count=3, status="failed")
    assert route_verification(exhausted_state) == "__end__"


def test_full_graph_cyclic_self_healing_execution() -> None:
    graph = create_incident_graph()
    initial_state = _make_sample_state()

    final_state = graph.invoke(initial_state)

    assert final_state["verification_status"] == "passed"
    assert final_state["retry_count"] == 1
    assert "max_connections: int = 50" in final_state["proposed_patch"]
    assert len(final_state["messages"]) >= 5
