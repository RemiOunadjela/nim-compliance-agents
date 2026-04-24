"""Report formatting utilities for Markdown and JSON output."""

from __future__ import annotations

import json
from typing import Any

from nim_compliance_agents.state import ComplianceState


def to_json(state: ComplianceState) -> str:
    """Serialize the compliance state to a JSON string.

    Produces a structured JSON document suitable for downstream
    integration with ticketing systems or compliance dashboards.
    """
    payload: dict[str, Any] = {
        "framework": state.framework,
        "violation_count": len(state.violations),
        "violations": [v.model_dump() for v in state.violations],
        "risk_assessment": (
            {
                **state.risk_assessment.model_dump(),
                "severity_label": state.risk_assessment.severity.label,
            }
            if state.risk_assessment
            else None
        ),
        "evidence": [e.model_dump() for e in state.evidence],
        "report": state.report,
        "agent_timings_seconds": state.agent_timings,
    }
    if state.error:
        payload["error"] = state.error
    return json.dumps(payload, indent=2)


def to_markdown(state: ComplianceState) -> str:
    """Format the compliance state as a standalone Markdown report.

    If the report agent has already generated a report, returns that
    directly. Otherwise, builds a minimal report from the raw state.
    """
    if state.report:
        return state.report

    lines = ["# Compliance Review Report", ""]
    if not state.violations:
        lines.append("No violations identified. Content is compliant.")
    else:
        lines.append(f"**{len(state.violations)} violation(s) found.**")
        lines.append("")

        for i, v in enumerate(state.violations, 1):
            lines.append(f"## {i}. {v.category} ({v.article})")
            lines.append(f"- Confidence: {v.confidence:.0%}")
            lines.append(f"- {v.description}")
            lines.append("")

        if state.risk_assessment:
            ra = state.risk_assessment
            lines.append("## Risk Assessment")
            lines.append(f"- **Severity:** {ra.severity.label}")
            lines.append(f"- **Reasoning:** {ra.reasoning}")
            lines.append(f"- **Regulatory exposure:** {ra.regulatory_exposure}")
            lines.append(f"- **Recommended action:** {ra.recommended_action}")
            lines.append("")

        if state.evidence:
            lines.append("## Supporting Evidence")
            for e in state.evidence:
                lines.append(
                    f'- "{e.passage}" — {e.relevance} (supports: {e.supports_violation})'
                )
            lines.append("")

    if state.agent_timings:
        total = sum(state.agent_timings.values())
        timing_parts = ", ".join(
            f"{agent}: {secs:.3f}s" for agent, secs in state.agent_timings.items()
        )
        lines.append("")
        lines.append(f"---\n*Agent timings — {timing_parts} | total: {total:.3f}s*")

    return "\n".join(lines)
