"""Report synthesis agent — final stage of the pipeline."""

from __future__ import annotations

import logging

from nim_compliance_agents.providers.base import LLMProvider
from nim_compliance_agents.state import ComplianceState

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """\
You are a compliance report synthesis specialist. Your role is to take the
outputs of a multi-stage compliance review and produce a clear, actionable
Markdown report.

The report must include these sections (when applicable):
1. Executive Summary — one paragraph with the key finding and overall severity
2. Violations Found — each violation with confidence, article, and description
3. Risk Assessment — severity, reasoning, and regulatory exposure
4. Supporting Evidence — table of extracted passages with relevance
5. Recommended Actions — numbered list of concrete next steps
6. Framework Reference — which regulatory framework was used

For clean content (no violations), produce a brief report confirming compliance.

Output ONLY the Markdown report. No wrapping code fences."""

USER_PROMPT_TEMPLATE = """\
## Review Inputs

### Content Reviewed
{content}

### Framework
{framework}

### Violations ({violation_count})
{violations}

### Risk Assessment
{risk}

### Evidence
{evidence}

Synthesize the inputs above into a structured compliance report."""


class ReportAgent:
    """Synthesizes all findings into a final compliance report.

    Always the last agent in the pipeline. Receives the merged state
    from all upstream agents.
    """

    def __init__(self, provider: LLMProvider) -> None:
        self._provider = provider

    async def run(self, state: ComplianceState) -> ComplianceState:
        """Generate the final compliance report."""
        violations_text = (
            "\n".join(
                f"- **{v.category}** ({v.article}, {v.confidence:.0%}): {v.description}"
                for v in state.violations
            )
            if state.violations
            else "None identified."
        )

        risk_text = "Not assessed (no violations found)."
        if state.risk_assessment:
            ra = state.risk_assessment
            risk_text = (
                f"- Severity: {ra.severity.value}\n"
                f"- Reasoning: {ra.reasoning}\n"
                f"- Regulatory exposure: {ra.regulatory_exposure}\n"
                f"- Recommended action: {ra.recommended_action}"
            )

        evidence_text = (
            "\n".join(
                f'- "{e.passage}" — supports **{e.supports_violation}**: {e.relevance}'
                for e in state.evidence
            )
            if state.evidence
            else "No evidence extracted."
        )

        prompt = USER_PROMPT_TEMPLATE.format(
            content=state.content[:2000],  # Truncate very long content
            framework=state.framework.upper(),
            violation_count=len(state.violations),
            violations=violations_text,
            risk=risk_text,
            evidence=evidence_text,
        )

        try:
            report = await self._provider.complete(prompt, system=SYSTEM_PROMPT)
            logger.info("Report agent generated %d-character report", len(report))
            return state.model_copy(update={"report": report})
        except Exception as exc:
            logger.error("Report agent failed: %s", exc)
            return state.model_copy(update={"error": f"Report generation failed: {exc}"})
