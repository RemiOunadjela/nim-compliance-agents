"""LangGraph orchestrator — wires agents into a conditional state machine."""

from __future__ import annotations

import asyncio
import logging
from typing import Any, TypedDict

from langgraph.graph import END, StateGraph

from nim_compliance_agents.agents.evidence import EvidenceAgent
from nim_compliance_agents.agents.policy import PolicyAgent
from nim_compliance_agents.agents.report import ReportAgent
from nim_compliance_agents.agents.risk import RiskAgent
from nim_compliance_agents.frameworks.loader import FrameworkDefinition, load_framework
from nim_compliance_agents.providers.base import LLMProvider
from nim_compliance_agents.state import ComplianceState

logger = logging.getLogger(__name__)


class GraphState(TypedDict, total=False):
    """Typed dict used as the LangGraph state container.

    LangGraph requires TypedDict for state management. We store the
    Pydantic ComplianceState as a single value and pass it through
    each node, keeping the Pydantic validation guarantees intact.
    """

    state: ComplianceState


def build_graph(
    provider: LLMProvider,
    framework: FrameworkDefinition | None = None,
    framework_name: str = "dsa",
) -> StateGraph:
    """Construct the compliance review state graph.

    The graph implements conditional routing:
    - Policy agent runs first
    - If violations found: fan out to risk + evidence concurrently
    - Merge results, then generate report
    - If no violations: skip directly to report (clean result)

    Args:
        provider: The LLM provider to use for all agents.
        framework: Pre-loaded framework definition. If None, loads by name.
        framework_name: Framework to load if ``framework`` is not provided.

    Returns:
        A compiled LangGraph StateGraph ready for invocation.
    """
    if framework is None:
        framework = load_framework(framework_name)

    policy_agent = PolicyAgent(provider, framework)
    risk_agent = RiskAgent(provider)
    evidence_agent = EvidenceAgent(provider)
    report_agent = ReportAgent(provider)

    async def policy_review(state: GraphState) -> GraphState:
        compliance_state = state["state"]
        updated = await policy_agent.run(compliance_state)
        return {"state": updated}

    async def risk_and_evidence(state: GraphState) -> GraphState:
        """Run risk and evidence agents concurrently, then merge results."""
        compliance_state = state["state"]
        risk_result, evidence_result = await asyncio.gather(
            risk_agent.run(compliance_state),
            evidence_agent.run(compliance_state),
        )
        # Merge the outputs from both concurrent agents
        merged = compliance_state.model_copy(
            update={
                "risk_assessment": risk_result.risk_assessment,
                "evidence": evidence_result.evidence,
                "error": risk_result.error or evidence_result.error,
            }
        )
        return {"state": merged}

    async def report_generation(state: GraphState) -> GraphState:
        compliance_state = state["state"]
        updated = await report_agent.run(compliance_state)
        return {"state": updated}

    def should_analyze(state: GraphState) -> str:
        """Route based on whether violations were found."""
        compliance_state = state["state"]
        if compliance_state.violations:
            logger.info(
                "Violations found (%d), routing to risk + evidence analysis",
                len(compliance_state.violations),
            )
            return "analyze"
        logger.info("No violations found, routing directly to report")
        return "report"

    # Build the graph
    graph = StateGraph(GraphState)

    graph.add_node("policy_review", policy_review)
    graph.add_node("risk_and_evidence", risk_and_evidence)
    graph.add_node("report_generation", report_generation)

    graph.set_entry_point("policy_review")

    graph.add_conditional_edges(
        "policy_review",
        should_analyze,
        {
            "analyze": "risk_and_evidence",
            "report": "report_generation",
        },
    )
    graph.add_edge("risk_and_evidence", "report_generation")
    graph.add_edge("report_generation", END)

    return graph


async def run_review(
    content: str,
    provider: LLMProvider,
    framework_name: str = "dsa",
) -> ComplianceState:
    """High-level entry point: run a full compliance review.

    Args:
        content: The text content to review.
        provider: LLM provider for inference.
        framework_name: Regulatory framework to use.

    Returns:
        The final ComplianceState with all fields populated.
    """
    graph = build_graph(provider, framework_name=framework_name)
    compiled = graph.compile()

    initial_state = ComplianceState(content=content, framework=framework_name)
    result: dict[str, Any] = await compiled.ainvoke({"state": initial_state})

    return result["state"]
