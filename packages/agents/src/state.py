# packages/agents/src/state.py
"""LangGraph state schema for autonomous SRE reasoning workflows."""

import operator
from typing import Annotated, Any, Literal, TypedDict

from langchain_core.messages import BaseMessage
from pydantic import BaseModel, Field


class RootCauseHypothesis(BaseModel):
    """Structured root-cause diagnosis produced during agent triage."""

    service_name: str
    failure_category: str = Field(
        ..., description="Category e.g. resource_exhaustion, regression, config"
    )
    root_cause: str = Field(..., description="Detailed diagnosis")
    confidence_score: float = Field(default=0.92, ge=0.0, le=1.0)
    culprit_commit: str | None = None
    affected_dependencies: list[str] = Field(default_factory=list)


class AgentState(TypedDict):
    """Represents the mutable state passed across LangGraph nodes in the SRE agent workflow.

    Attributes:
        alert: Canonical normalized alert payload being analyzed.
        graph_context: Extracted topological nodes, dependency edges, and blast radius metadata.
        hypothesis: Deduced root-cause theory and explanation.
        structured_hypothesis: Machine-readable Pydantic dictionary of root-cause hypothesis.
        proposed_patch: Synthesized code, configuration, or parameter remediation patch.
        verification_status: Current evaluation state in the execution sandbox.
        retry_count: Number of failed remediation/verification iterations.
        messages: Append-only ledger of reasoning thoughts and MCP tool invocations.
    """

    alert: dict[str, Any]
    graph_context: list[dict[str, Any]]
    hypothesis: str
    structured_hypothesis: dict[str, Any] | None
    proposed_patch: str
    verification_status: Literal["pending", "passed", "failed"]
    retry_count: int
    use_real_sandbox: bool | None
    messages: Annotated[list[BaseMessage], operator.add]

