"""Policy classification agent — first stage of the pipeline."""

from __future__ import annotations

import json
import logging

from nim_compliance_agents.frameworks.loader import FrameworkDefinition
from nim_compliance_agents.providers.base import LLMProvider
from nim_compliance_agents.providers.nim import parse_json_response
from nim_compliance_agents.state import ComplianceState, Violation

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """\
You are a regulatory compliance policy classifier. Your role is to analyze
content against a specific regulatory framework and identify potential violations.

You must respond with a JSON object containing a single key "violations", which
is a list of violation objects. Each violation object must have these fields:
- category: string matching one of the framework violation category IDs
- confidence: float between 0.0 and 1.0
- article: the specific regulatory article reference
- description: a clear explanation of why this constitutes a violation

If the content does not violate any policy, return {"violations": []}.

Respond ONLY with valid JSON. No explanations outside the JSON."""

USER_PROMPT_TEMPLATE = """\
## Regulatory Framework: {framework_name} ({framework_abbr})

### Violation Categories
{categories}

## Content to Review
{content}

Analyze the content above and return a JSON object with any violations found."""


class PolicyAgent:
    """Classifies content against a regulatory framework.

    This is always the first agent in the pipeline. Its output determines
    whether downstream agents (risk, evidence) need to run.
    """

    def __init__(self, provider: LLMProvider, framework: FrameworkDefinition) -> None:
        self._provider = provider
        self._framework = framework

    async def run(self, state: ComplianceState) -> ComplianceState:
        """Classify content and return updated state with any violations."""
        categories_text = "\n".join(
            f"- **{cat.id}** ({cat.article}): {cat.description}"
            for cat in self._framework.violation_categories
        )
        prompt = USER_PROMPT_TEMPLATE.format(
            framework_name=self._framework.name,
            framework_abbr=self._framework.abbreviation,
            categories=categories_text,
            content=state.content,
        )

        max_retries = 2
        for attempt in range(max_retries + 1):
            try:
                response = await self._provider.complete(prompt, system=SYSTEM_PROMPT)
                data = parse_json_response(response)
                violations = [Violation(**v) for v in data.get("violations", [])]
                logger.info("Policy agent found %d violation(s)", len(violations))
                return state.model_copy(update={"violations": violations})
            except (json.JSONDecodeError, KeyError, TypeError, RuntimeError) as exc:
                if attempt < max_retries:
                    logger.warning(
                        "Policy agent parse error (attempt %d/%d): %s",
                        attempt + 1,
                        max_retries + 1,
                        exc,
                    )
                    continue
                logger.error("Policy agent failed to parse response after retries")
                return state.model_copy(update={"error": f"Policy agent parse failure: {exc}"})
