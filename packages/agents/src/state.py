# packages/agents/src/state.py
"""LangGraph state schema for autonomous SRE reasoning workflows."""

import operator
from typing import Annotated, Any, Literal, TypedDict

from langchain_core.messages import BaseMessage


class AgentState(TypedDict):
    """Represents the mutable state passed across LangGraph nodes in the SRE agent workflow.

    Attributes:
        alert: Canonical normalized alert payload being analyzed.
        graph_context: Extracted topological nodes, dependency edges, and blast radius metadata.
        hypothesis: Deduced root-cause theory and explanation.
        proposed_patch: Synthesized code, configuration, or parameter remediation patch.
        verification_status: Current evaluation state in the execution sandbox.
        retry_count: Number of failed remediation/verification iterations.
        messages: Append-only ledger of reasoning thoughts and MCP tool invocations.
    """

    alert: dict[str, Any]
    graph_context: list[dict[str, Any]]
    hypothesis: str
    proposed_patch: str
    verification_status: Literal["pending", "passed", "failed"]
    retry_count: int
    messages: Annotated[list[BaseMessage], operator.add]
