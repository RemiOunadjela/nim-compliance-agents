"""Tests for report formatting utilities."""

from __future__ import annotations

import json

import pytest

from nim_compliance_agents.output.formatter import to_json, to_markdown
from nim_compliance_agents.state import (
    ComplianceState,
    Evidence,
    RiskAssessment,
    Severity,
    Violation,
)


@pytest.fixture
def state_with_timings() -> ComplianceState:
    return ComplianceState(
        content="test",
        framework="dsa",
        agent_timings={"policy": 0.123, "risk_and_evidence": 0.456, "report": 0.078},
    )


@pytest.fixture
def state_with_violations_and_timings() -> ComplianceState:
    return ComplianceState(
        content="test",
        framework="dsa",
        violations=[
            Violation(
                category="hate_speech",
                confidence=0.9,
                article="Art 16(6)",
                description="Hate speech found.",
            )
        ],
        risk_assessment=RiskAssessment(
            severity=Severity.P1,
            reasoning="Serious violation",
            regulatory_exposure="High",
            recommended_action="Remove content",
        ),
        evidence=[
            Evidence(
                passage="example passage",
                relevance="directly relevant",
                supports_violation="hate_speech",
            )
        ],
        agent_timings={"policy": 0.1, "risk_and_evidence": 0.2, "report": 0.05},
    )


class TestToMarkdown:
    def test_timing_footer_included(self, state_with_timings):
        result = to_markdown(state_with_timings)
        assert "Agent timings" in result
        assert "policy: 0.123s" in result
        assert "risk_and_evidence: 0.456s" in result
        assert "report: 0.078s" in result

    def test_timing_footer_shows_total(self, state_with_timings):
        result = to_markdown(state_with_timings)
        total = 0.123 + 0.456 + 0.078
        assert f"total: {total:.3f}s" in result

    def test_no_timing_footer_when_empty(self):
        state = ComplianceState(content="test", framework="dsa")
        result = to_markdown(state)
        assert "Agent timings" not in result

    def test_timing_footer_in_violation_report(self, state_with_violations_and_timings):
        result = to_markdown(state_with_violations_and_timings)
        assert "Agent timings" in result

    def test_existing_report_field_bypasses_formatter_but_timing_absent(self):
        # When state.report is pre-populated, to_markdown returns it directly
        state = ComplianceState(
            content="test",
            framework="dsa",
            report="# Pre-generated report\nSome content.",
            agent_timings={"policy": 0.1},
        )
        result = to_markdown(state)
        # The pre-generated report is returned as-is; timing not injected
        assert result == "# Pre-generated report\nSome content."


class TestSeverityLabels:
    def test_p0_label(self):
        assert Severity.P0.label == "Critical (P0)"

    def test_p1_label(self):
        assert Severity.P1.label == "High (P1)"

    def test_p2_label(self):
        assert Severity.P2.label == "Medium (P2)"

    def test_p3_label(self):
        assert Severity.P3.label == "Low (P3)"

    def test_p4_label(self):
        assert Severity.P4.label == "Informational (P4)"

    def test_markdown_uses_human_readable_severity(self, state_with_violations_and_timings):
        result = to_markdown(state_with_violations_and_timings)
        assert "High (P1)" in result
        assert "p1" not in result.split("## Risk Assessment")[1].split("\n")[1]

    def test_json_includes_severity_label(self, state_with_violations_and_timings):
        result = json.loads(to_json(state_with_violations_and_timings))
        assert result["risk_assessment"]["severity_label"] == "High (P1)"
        assert result["risk_assessment"]["severity"] == "p1"

    def test_json_no_risk_assessment_severity_label_absent(self):
        state = ComplianceState(content="test", framework="dsa")
        result = json.loads(to_json(state))
        assert result["risk_assessment"] is None


class TestToJson:
    def test_agent_timings_in_output(self, state_with_timings):
        result = json.loads(to_json(state_with_timings))
        assert "agent_timings_seconds" in result
        assert result["agent_timings_seconds"]["policy"] == 0.123
        assert result["agent_timings_seconds"]["risk_and_evidence"] == 0.456

    def test_empty_timings_still_present(self):
        state = ComplianceState(content="test", framework="dsa")
        result = json.loads(to_json(state))
        assert "agent_timings_seconds" in result
        assert result["agent_timings_seconds"] == {}
