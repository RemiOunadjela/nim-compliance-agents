"""Compliance state model — the contract between agents."""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class Severity(str, Enum):
    """Priority levels for compliance violations."""

    P0 = "p0"  # Imminent harm, requires immediate action
    P1 = "p1"  # Serious violation, action within hours
    P2 = "p2"  # Moderate violation, action within days
    P3 = "p3"  # Minor violation, routine review
    P4 = "p4"  # Informational, no action required

    @property
    def label(self) -> str:
        """Human-readable label, e.g. 'Critical (P0)'."""
        _names: dict[str, str] = {
            "p0": "Critical",
            "p1": "High",
            "p2": "Medium",
            "p3": "Low",
            "p4": "Informational",
        }
        return f"{_names[self.value]} ({self.value.upper()})"


class Violation(BaseModel):
    """A single policy violation identified during content review."""

    category: str
    confidence: float = Field(ge=0.0, le=1.0)
    article: str
    description: str


class RiskAssessment(BaseModel):
    """Risk scoring output from the risk agent."""

    severity: Severity
    reasoning: str
    regulatory_exposure: str
    recommended_action: str


class Evidence(BaseModel):
    """A passage extracted from the content that supports a violation finding."""

    passage: str
    relevance: str
    supports_violation: str


class ComplianceState(BaseModel):
    """The state that flows through the LangGraph pipeline.

    Every agent reads from and writes to this model. It is the sole
    communication contract between pipeline stages.
    """

    content: str
    framework: str = "dsa"
    violations: list[Violation] = Field(default_factory=list)
    risk_assessment: RiskAssessment | None = None
    evidence: list[Evidence] = Field(default_factory=list)
    report: str | None = None
    error: str | None = None
    agent_timings: dict[str, float] = Field(default_factory=dict)
