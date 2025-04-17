"""Command-line interface for nim-compliance-agents."""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

import click
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel

from nim_compliance_agents.frameworks.loader import list_frameworks, load_framework
from nim_compliance_agents.graph import run_review
from nim_compliance_agents.output.formatter import to_json, to_markdown

console = Console()


@click.group()
@click.version_option(package_name="nim-compliance-agents")
def cli() -> None:
    """Multi-Agent Compliance Review on NVIDIA NIM."""


@cli.command()
@click.option(
    "--input",
    "input_path",
    required=True,
    type=click.Path(exists=True, path_type=Path),
    help="Path to the content file to review.",
)
@click.option(
    "--framework",
    default="dsa",
    show_default=True,
    help="Regulatory framework to use for review.",
)
@click.option(
    "--mock",
    is_flag=True,
    default=False,
    help="Use mock provider (no API key required).",
)
@click.option(
    "--output-format",
    type=click.Choice(["markdown", "json"]),
    default="markdown",
    show_default=True,
    help="Output format for the compliance report.",
)
@click.option(
    "--output",
    "output_path",
    type=click.Path(path_type=Path),
    default=None,
    help="Write report to file instead of stdout.",
)
def review(
    input_path: Path,
    framework: str,
    mock: bool,
    output_format: str,
    output_path: Path | None,
) -> None:
    """Review content against a regulatory compliance framework."""
    content = input_path.read_text(encoding="utf-8")

    if not content.strip():
        console.print("[red]Error:[/red] Input file is empty.")
        sys.exit(1)

    if mock:
        from nim_compliance_agents.providers.mock import MockProvider

        provider = MockProvider()
    else:
        try:
            from nim_compliance_agents.providers.nim import NIMProvider

            provider = NIMProvider()
        except ValueError as exc:
            console.print(f"[red]Error:[/red] {exc}")
            console.print("Hint: use --mock to run without an API key.")
            sys.exit(1)

    console.print(
        Panel(
            f"Reviewing content ({len(content)} chars) "
            f"against [bold]{framework.upper()}[/bold] framework",
            title="nim-compliance-agents",
        )
    )

    state = asyncio.run(run_review(content, provider, framework_name=framework))

    if state.error:
        console.print(f"[yellow]Warning:[/yellow] {state.error}")

    if output_format == "json":
        report_text = to_json(state)
    else:
        report_text = to_markdown(state)

    if output_path:
        output_path.write_text(report_text, encoding="utf-8")
        console.print(f"Report written to [bold]{output_path}[/bold]")
    else:
        if output_format == "markdown":
            console.print(Markdown(report_text))
        else:
            console.print(report_text)

    violation_count = len(state.violations)
    if violation_count > 0:
        severity = state.risk_assessment.severity.value if state.risk_assessment else "unknown"
        console.print(
            f"\n[bold red]{violation_count} violation(s) found[/bold red] — severity: {severity}"
        )
    else:
        console.print("\n[bold green]No violations found.[/bold green]")


@cli.group()
def frameworks() -> None:
    """Manage regulatory framework definitions."""


@frameworks.command("list")
def frameworks_list() -> None:
    """List available regulatory frameworks."""
    available = list_frameworks()
    if not available:
        console.print("[yellow]No frameworks found.[/yellow]")
        return

    for name in available:
        fw = load_framework(name)
        console.print(
            f"  [bold]{fw.abbreviation}[/bold] — {fw.name} ({fw.jurisdiction}, {fw.version})"
        )
        for cat in fw.violation_categories:
            console.print(f"    {cat.id}: {cat.name} ({cat.article})")


if __name__ == "__main__":
    cli()
