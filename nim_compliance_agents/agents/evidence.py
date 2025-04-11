"""Evidence extraction agent — pulls supporting passages from content."""

from __future__ import annotations

import json
import logging

from nim_compliance_agents.providers.base import LLMProvider
from nim_compliance_agents.providers.nim import parse_json_response
from nim_compliance_agents.state import ComplianceState, Evidence

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """\
You are an evidence extraction specialist for regulatory compliance review.
Given content and a set of identified violations, you must extract the specific
passages from the content that support each violation finding.

Respond with a JSON object containing a single key "evidence", which is a list
of evidence objects. Each object must have:
- passage: the exact text excerpt from the content (verbatim quote)
- relevance: why this passage is relevant to the violation
- supports_violation: the violation category ID this evidence supports

Extract at least one piece of evidence per violation. Prefer shorter, focused
excerpts over long passages.

Respond ONLY with valid JSON. No explanations outside the JSON."""

USER_PROMPT_TEMPLATE = """\
## Violations Identified

{violations}

## Original Content

{content}

Extract specific passages from the content that support each violation above."""


class EvidenceAgent:
    """Extracts supporting evidence passages from the reviewed content.

    Runs concurrently with the risk agent after the policy agent
    identifies violations.
    """

    def __init__(self, provider: LLMProvider) -> None:
        self._provider = provider

    async def run(self, state: ComplianceState) -> ComplianceState:
        """Extract evidence and return updated state."""
        if not state.violations:
            return state

        violations_text = "\n".join(
            f"- **{v.category}** ({v.article}): {v.description}" for v in state.violations
        )
        prompt = USER_PROMPT_TEMPLATE.format(
            violations=violations_text,
            content=state.content,
        )

        max_retries = 2
        for attempt in range(max_retries + 1):
            try:
                response = await self._provider.complete(prompt, system=SYSTEM_PROMPT)
                data = parse_json_response(response)
                evidence = [Evidence(**e) for e in data.get("evidence", [])]
                logger.info("Evidence agent extracted %d passage(s)", len(evidence))
                return state.model_copy(update={"evidence": evidence})
            except (json.JSONDecodeError, KeyError, TypeError) as exc:
                if attempt < max_retries:
                    logger.warning(
                        "Evidence agent parse error (attempt %d/%d): %s",
                        attempt + 1,
                        max_retries + 1,
                        exc,
                    )
                    continue
                logger.error("Evidence agent failed to parse response after retries")
                return state.model_copy(update={"error": f"Evidence agent parse failure: {exc}"})
