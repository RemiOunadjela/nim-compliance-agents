"""Tests for the LangGraph orchestrator."""

from __future__ import annotations

import pytest

from nim_compliance_agents.graph import run_review
from nim_compliance_agents.providers.mock import MockProvider


class TestGraphExecution:
    @pytest.mark.asyncio
    async def test_full_pipeline_with_violations(self, mock_provider):
        content = "Content with violations for testing."
        state = await run_review(content, mock_provider, framework_name="dsa")

        assert len(state.violations) > 0
        assert state.risk_assessment is not None
        assert len(state.evidence) > 0
        assert state.report is not None

    @pytest.mark.asyncio
    async def test_clean_content_skips_analysis(self):
        provider = MockProvider(return_clean=True)
        content = "Perfectly safe content."
        state = await run_review(content, provider, framework_name="dsa")

        assert state.violations == []
        assert state.risk_assessment is None
        assert state.evidence == []
        assert state.report is not None
        assert "No violations" in state.report

    @pytest.mark.asyncio
    async def test_preserves_framework(self, mock_provider):
        state = await run_review("test", mock_provider, framework_name="dsa")
        assert state.framework == "dsa"

    @pytest.mark.asyncio
    async def test_preserves_content(self, mock_provider):
        content = "Original content for review."
        state = await run_review(content, mock_provider, framework_name="dsa")
        assert state.content == content

    @pytest.mark.asyncio
    async def test_agent_timings_populated_with_violations(self, mock_provider):
        state = await run_review("test content", mock_provider, framework_name="dsa")
        assert "policy" in state.agent_timings
        assert "risk_and_evidence" in state.agent_timings
        assert "report" in state.agent_timings
        assert all(v >= 0.0 for v in state.agent_timings.values())

    @pytest.mark.asyncio
    async def test_agent_timings_populated_clean_content(self):
        provider = MockProvider(return_clean=True)
        state = await run_review("safe content", provider, framework_name="dsa")
        assert "policy" in state.agent_timings
        assert "report" in state.agent_timings
        # No violations means risk_and_evidence node was skipped
        assert "risk_and_evidence" not in state.agent_timings
