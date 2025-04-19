#!/usr/bin/env python3
"""Example: run a compliance review programmatically."""

from __future__ import annotations

import asyncio
from pathlib import Path

from nim_compliance_agents.graph import run_review
from nim_compliance_agents.output.formatter import to_json, to_markdown
from nim_compliance_agents.providers.mock import MockProvider


async def main() -> None:
    content_path = Path(__file__).parent / "sample_content.txt"
    content = content_path.read_text(encoding="utf-8")

    # Use the mock provider for this example (no API key required).
    # Replace with NIMProvider() for real inference.
    provider = MockProvider()

    state = await run_review(content, provider, framework_name="dsa")

    print("=== Markdown Report ===\n")
    print(to_markdown(state))

    print("\n=== JSON Output ===\n")
    print(to_json(state))


if __name__ == "__main__":
    asyncio.run(main())
