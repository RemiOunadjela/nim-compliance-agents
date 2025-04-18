"""Tests for the compliance state model."""

from __future__ import annotations

import pytest

from nim_compliance_agents.state import (
    ComplianceState,
    Evidence,
    RiskAssessment,
    Severity,
    Violation,
)


class TestSeverity:
    def test_values(self):
        assert Severity.P0.value == "p0"
        assert Severity.P4.value == "p4"

    def test_from_string(self):
        assert Severity("p1") == Severity.P1


class TestViolation:
    def test_valid_violation(self):
        v = Violation(
            category="hate_speech",
            confidence=0.85,
            article="DSA Article 16(6)",
            description="Incites hatred.",
        )
        assert v.confidence == 0.85

    def test_confidence_bounds(self):
        with pytest.raises(ValueError):
            Violation(
                category="test",
                confidence=1.5,
                article="Art 1",
                description="Invalid",
            )

    def test_confidence_lower_bound(self):
        with pytest.raises(ValueError):
            Violation(
                category="test",
                confidence=-0.1,
                article="Art 1",
                description="Invalid",
            )


class TestRiskAssessment:
    def test_valid_assessment(self):
        ra = RiskAssessment(
            severity=Severity.P1,
            reasoning="High risk.",
            regulatory_exposure="EU DSC",
            recommended_action="Restrict immediately.",
        )
        assert ra.severity == Severity.P1


class TestEvidence:
    def test_valid_evidence(self):
        e = Evidence(
            passage="exact quote here",
            relevance="supports the finding",
            supports_violation="hate_speech",
        )
        assert e.supports_violation == "hate_speech"


class TestComplianceState:
    def test_defaults(self):
        state = ComplianceState(content="test content")
        assert state.framework == "dsa"
        assert state.violations == []
        assert state.risk_assessment is None
        assert state.evidence == []
        assert state.report is None
        assert state.error is None

    def test_model_copy_update(self):
        state = ComplianceState(content="test")
        violation = Violation(
            category="test",
            confidence=0.9,
            article="Art 1",
            description="A violation",
        )
        updated = state.model_copy(update={"violations": [violation]})
        assert len(updated.violations) == 1
        assert len(state.violations) == 0  # original unchanged
