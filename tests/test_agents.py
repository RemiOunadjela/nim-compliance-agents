"""Tests for individual compliance agents."""

from __future__ import annotations

import pytest

from nim_compliance_agents.agents.evidence import EvidenceAgent
from nim_compliance_agents.agents.policy import PolicyAgent
from nim_compliance_agents.agents.report import ReportAgent
from nim_compliance_agents.agents.risk import RiskAgent
from nim_compliance_agents.state import Severity, Violation


class TestPolicyAgent:
    @pytest.mark.asyncio
    async def test_finds_violations(self, mock_provider, dsa_framework, sample_state):
        agent = PolicyAgent(mock_provider, dsa_framework)
        result = await agent.run(sample_state)
        assert len(result.violations) == 2
        assert result.violations[0].category == "hate_speech"
        assert result.violations[1].category == "disinformation"

    @pytest.mark.asyncio
    async def test_clean_content(self, clean_provider, dsa_framework, sample_state):
        agent = PolicyAgent(clean_provider, dsa_framework)
        result = await agent.run(sample_state)
        assert result.violations == []

    @pytest.mark.asyncio
    async def test_error_handling(self, error_provider, dsa_framework, sample_state):
        agent = PolicyAgent(error_provider, dsa_framework)
        result = await agent.run(sample_state)
        assert result.error is not None


class TestRiskAgent:
    @pytest.mark.asyncio
    async def test_scores_severity(self, mock_provider, sample_state):
        # Pre-populate violations
        state = sample_state.model_copy(
            update={
                "violations": [
                    Violation(
                        category="hate_speech",
                        confidence=0.9,
                        article="Art 16(6)",
                        description="Hate speech identified.",
                    )
                ]
            }
        )
        agent = RiskAgent(mock_provider)
        result = await agent.run(state)
        assert result.risk_assessment is not None
        assert result.risk_assessment.severity == Severity.P1

    @pytest.mark.asyncio
    async def test_skips_without_violations(self, mock_provider, sample_state):
        agent = RiskAgent(mock_provider)
        result = await agent.run(sample_state)
        assert result.risk_assessment is None


class TestEvidenceAgent:
    @pytest.mark.asyncio
    async def test_extracts_evidence(self, mock_provider, sample_state):
        state = sample_state.model_copy(
            update={
                "violations": [
                    Violation(
                        category="hate_speech",
                        confidence=0.9,
                        article="Art 16(6)",
                        description="Hate speech.",
                    )
                ]
            }
        )
        agent = EvidenceAgent(mock_provider)
        result = await agent.run(state)
        assert len(result.evidence) == 2

    @pytest.mark.asyncio
    async def test_skips_without_violations(self, mock_provider, sample_state):
        agent = EvidenceAgent(mock_provider)
        result = await agent.run(sample_state)
        assert result.evidence == []


class TestReportAgent:
    @pytest.mark.asyncio
    async def test_generates_report(self, mock_provider, sample_state):
        agent = ReportAgent(mock_provider)
        result = await agent.run(sample_state)
        assert result.report is not None
        assert "Compliance Review Report" in result.report

    @pytest.mark.asyncio
    async def test_error_handling(self, error_provider, sample_state):
        agent = ReportAgent(error_provider)
        result = await agent.run(sample_state)
        assert result.error is not None
