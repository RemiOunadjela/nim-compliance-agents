"""Mock provider for testing and demos without an API key."""

from __future__ import annotations

import json

from nim_compliance_agents.providers.base import LLMProvider

# Pre-built responses keyed by the agent type detected from the system prompt.
_VIOLATION_RESPONSES = {
    "policy": json.dumps(
        {
            "violations": [
                {
                    "category": "hate_speech",
                    "confidence": 0.92,
                    "article": "DSA Article 16(6)",
                    "description": (
                        "Content contains language that incites hatred against a protected group "
                        "based on ethnic origin."
                    ),
                },
                {
                    "category": "disinformation",
                    "confidence": 0.78,
                    "article": "DSA Article 34",
                    "description": (
                        "Contains demonstrably false claims about public health presented as fact."
                    ),
                },
            ]
        }
    ),
    "risk": json.dumps(
        {
            "severity": "p1",
            "reasoning": (
                "Hate speech targeting ethnic groups combined with health disinformation "
                "creates a high-severity compound risk. Content has potential for viral spread."
            ),
            "regulatory_exposure": "EU Digital Services Coordinator, national equality bodies",
            "recommended_action": (
                "Restrict content visibility immediately. Escalate to trust & safety team "
                "for full review within 4 hours. Notify DSA transparency reporting pipeline."
            ),
        }
    ),
    "evidence": json.dumps(
        {
            "evidence": [
                {
                    "passage": (
                        "These people are responsible for spreading the disease deliberately."
                    ),
                    "relevance": (
                        "Attributes malicious intent to an ethnic group, meeting the threshold "
                        "for incitement to hatred under DSA Article 16(6)."
                    ),
                    "supports_violation": "hate_speech",
                },
                {
                    "passage": (
                        "Studies have proven that the vaccine causes "
                        "the illness it claims to prevent."
                    ),
                    "relevance": (
                        "Presents a debunked claim as established fact without citing legitimate "
                        "sources, qualifying as systematic disinformation under DSA Article 34."
                    ),
                    "supports_violation": "disinformation",
                },
            ]
        }
    ),
    "report": (
        "# Compliance Review Report\n\n"
        "## Executive Summary\n\n"
        "This content review identified **2 violations** of the EU Digital Services Act. "
        "The overall risk severity is **P1 (Serious)**, requiring action within hours.\n\n"
        "## Violations Found\n\n"
        "### 1. Hate Speech (DSA Article 16(6))\n"
        "- **Confidence:** 92%\n"
        "- **Description:** Content contains language that incites hatred against a "
        "protected group based on ethnic origin.\n\n"
        "### 2. Disinformation (DSA Article 34)\n"
        "- **Confidence:** 78%\n"
        "- **Description:** Contains demonstrably false claims about public health "
        "presented as fact.\n\n"
        "## Risk Assessment\n\n"
        "- **Severity:** P1 — Serious violation, action within hours\n"
        "- **Regulatory Exposure:** EU Digital Services Coordinator, national equality bodies\n"
        "- **Reasoning:** Hate speech targeting ethnic groups combined with health "
        "disinformation creates a high-severity compound risk.\n\n"
        "## Supporting Evidence\n\n"
        "| # | Passage | Supports | Relevance |\n"
        "|---|---------|----------|-----------|\n"
        '| 1 | "These people are responsible for spreading the disease deliberately." '
        "| hate_speech | Incitement to hatred under Article 16(6) |\n"
        '| 2 | "Studies have proven that the vaccine causes the illness..." '
        "| disinformation | Debunked claim presented as fact |\n\n"
        "## Recommended Actions\n\n"
        "1. Restrict content visibility immediately.\n"
        "2. Escalate to trust & safety team for full review within 4 hours.\n"
        "3. Notify DSA transparency reporting pipeline.\n"
    ),
}

_CLEAN_RESPONSES = {
    "policy": json.dumps({"violations": []}),
    "report": (
        "# Compliance Review Report\n\n"
        "## Executive Summary\n\n"
        "No violations were identified. The content complies with the "
        "EU Digital Services Act framework.\n\n"
        "## Result\n\n"
        "**CLEAN** — No action required.\n"
    ),
}


class MockProvider(LLMProvider):
    """Returns pre-built responses for testing and demos.

    The provider inspects the system prompt to determine which agent is
    calling it and returns the corresponding mock response. Set
    ``return_clean=True`` to simulate content that passes review.
    """

    def __init__(self, *, return_clean: bool = False, return_error: bool = False) -> None:
        self._return_clean = return_clean
        self._return_error = return_error

    async def complete(
        self,
        prompt: str,
        system: str = "",
        temperature: float = 0.1,
    ) -> str:
        if self._return_error:
            raise RuntimeError("Simulated provider error for testing")

        agent_type = self._detect_agent(system)
        if self._return_clean:
            return _CLEAN_RESPONSES.get(agent_type, _CLEAN_RESPONSES["policy"])
        return _VIOLATION_RESPONSES.get(agent_type, _VIOLATION_RESPONSES["policy"])

    @staticmethod
    def _detect_agent(system: str) -> str:
        """Determine which agent is calling based on the system prompt."""
        lower = system.lower()
        # Check report/synthesis first — the report prompt mentions "risk"
        # and "evidence" in its instructions, so order matters here.
        if "report synthesis" in lower or "synthesize" in lower:
            return "report"
        if "risk assessment" in lower:
            return "risk"
        if "evidence extraction" in lower:
            return "evidence"
        return "policy"
