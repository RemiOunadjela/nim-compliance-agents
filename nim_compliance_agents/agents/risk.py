"""Risk severity scoring agent."""

from __future__ import annotations

import json
import logging

from nim_compliance_agents.providers.base import LLMProvider
from nim_compliance_agents.providers.nim import parse_json_response
from nim_compliance_agents.state import ComplianceState, RiskAssessment

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """\
You are a risk assessment specialist for regulatory compliance. Given a set of
policy violations, you must score the overall severity and provide actionable
guidance.

Consider these factors:
- Content type and potential reach
- Regulatory exposure (which bodies have jurisdiction)
- Severity of individual violations and their compound effect
- Precedent from prior enforcement actions

Respond with a JSON object containing:
- severity: one of "p0", "p1", "p2", "p3", "p4"
- reasoning: a clear explanation of how you arrived at the severity score
- regulatory_exposure: which regulatory bodies or authorities are relevant
- recommended_action: specific steps the platform should take

Respond ONLY with valid JSON. No explanations outside the JSON."""

USER_PROMPT_TEMPLATE = """\
## Violations Identified

{violations}

## Severity Scale
- p0: Imminent harm requiring immediate action (child safety, terrorism)
- p1: Serious violation requiring action within hours
- p2: Moderate violation requiring action within days
- p3: Minor violation for routine review queue
- p4: Informational finding, no action required

Score the overall risk severity for the violations above."""


class RiskAgent:
    """Scores the aggregate risk severity for identified violations.

    Runs concurrently with the evidence agent after the policy agent
    identifies violations.
    """

    def __init__(self, provider: LLMProvider) -> None:
        self._provider = provider

    async def run(self, state: ComplianceState) -> ComplianceState:
        """Score risk severity and return updated state."""
        if not state.violations:
            return state

        violations_text = "\n".join(
            f"- **{v.category}** ({v.article}, confidence {v.confidence:.0%}): {v.description}"
            for v in state.violations
        )
        prompt = USER_PROMPT_TEMPLATE.format(violations=violations_text)

        max_retries = 2
        for attempt in range(max_retries + 1):
            try:
                response = await self._provider.complete(prompt, system=SYSTEM_PROMPT)
                data = parse_json_response(response)
                assessment = RiskAssessment(**data)
                logger.info("Risk agent scored severity: %s", assessment.severity.value)
                return state.model_copy(update={"risk_assessment": assessment})
            except (json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
                if attempt < max_retries:
                    logger.warning(
                        "Risk agent parse error (attempt %d/%d): %s",
                        attempt + 1,
                        max_retries + 1,
                        exc,
                    )
                    continue
                logger.error("Risk agent failed to parse response after retries")
                return state.model_copy(update={"error": f"Risk agent parse failure: {exc}"})
