"""CLI interface for geo-toolkit."""

import click
import json
import sys
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich import box

from geo_toolkit.auditor import GEOAuditor
from geo_toolkit.reporters.markdown import generate_markdown_report
from geo_toolkit.reporters.json_report import generate_json_report
from geo_toolkit.reporters.html_dashboard import generate_html_dashboard

console = Console()


def get_score_color(score):
    if score >= 80:
        return "green"
    elif score >= 60:
        return "yellow"
    elif score >= 40:
        return "dark_orange"
    return "red"


def get_grade(score):
    if score >= 90:
        return "A+"
    elif score >= 80:
        return "A"
    elif score >= 70:
        return "B"
    elif score >= 60:
        return "C"
    elif score >= 40:
        return "D"
    return "F"


@click.group()
@click.version_option(version="0.1.0", prog_name="geo-toolkit")
def main():
    """geo-toolkit: Audit your content for AI search engine citability."""
    pass


@main.command()
@click.argument("url")
@click.option("-f", "--format", "output_format", default="text",
              type=click.Choice(["text", "json", "markdown", "html"]),
              help="Output format")
@click.option("-o", "--output", "output_file", default=None,
              help="Save report to file")
def audit(url, output_format, output_file):
    """Run a full GEO audit on a URL.

    Analyzes the page for AI crawler access, llms.txt compliance,
    content structure, schema markup, passage citability, and more.
    """
    console.print()
    console.print(Panel.fit(
        "[bold cyan]geo-toolkit[/bold cyan] [dim]v0.1.0[/dim]\n"
        "[dim]Generative Engine Optimization Auditor[/dim]",
        border_style="cyan",
    ))
    console.print()

    with console.status("[bold cyan]Fetching and analyzing page...") as status:
        try:
            auditor = GEOAuditor()
            results = auditor.audit(url)
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")
            sys.exit(1)

    if output_format == "json":
        report = generate_json_report(results)
        output = json.dumps(report, indent=2)
        if output_file:
            with open(output_file, "w") as f:
                f.write(output)
            console.print(f"[green]Report saved to {output_file}[/green]")
        else:
            console.print(output)

    elif output_format == "markdown":
        report = generate_markdown_report(results)
        if output_file:
            with open(output_file, "w") as f:
                f.write(report)
            console.print(f"[green]Report saved to {output_file}[/green]")
        else:
            console.print(report)

    elif output_format == "html":
        out = output_file or "geo-report.html"
        generate_html_dashboard(results, output_path=out)
        console.print(f"[green]Dashboard saved to {out}[/green]")
        console.print(f"[cyan]Open in your browser: file://{out}[/cyan]")

    else:
        print_text_report(results)


@main.command("check-crawlers")
@click.argument("domain")
def check_crawlers(domain):
    """Check if AI crawlers are blocked in robots.txt."""
    with console.status("[bold cyan]Checking robots.txt for AI crawler access..."):
        from geo_toolkit.auditors.crawler_access import CrawlerAccessAuditor
        auditor = CrawlerAccessAuditor()
        url = domain if domain.startswith("http") else f"https://{domain}"
        result = auditor.audit(url)

    console.print()
    console.print("[bold]AI Crawler Access Report[/bold]\n")

    table = Table(box=box.ROUNDED)
    table.add_column("Crawler", style="bold")
    table.add_column("User-Agent", style="dim")
    table.add_column("Status")

    for crawler in result["crawlers"]:
        status = "[green]ALLOWED[/green]" if crawler["allowed"] else "[red]BLOCKED[/red]"
        table.add_row(crawler["name"], crawler["user_agent"], status)

    console.print(table)
    console.print()


@main.command("check-llms-txt")
@click.argument("domain")
def check_llms_txt(domain):
    """Check for llms.txt compliance."""
    with console.status("[bold cyan]Checking llms.txt..."):
        from geo_toolkit.auditors.llms_txt import LLMSTxtAuditor
        auditor = LLMSTxtAuditor()
        url = domain if domain.startswith("http") else f"https://{domain}"
        result = auditor.audit(url)

    console.print()
    console.print("[bold]llms.txt Compliance Report[/bold]\n")

    if result["found"]:
        console.print(f"[green]llms.txt found![/green]")
        console.print(f"[dim]URL: {result['url']}[/dim]")
        console.print(f"[dim]Size: {result['size']} bytes[/dim]")
        if result["sections"]:
            console.print(f"[dim]Sections: {', '.join(result['sections'])}[/dim]")
    else:
        console.print("[yellow]No llms.txt file found[/yellow]")
        console.print("[cyan]Create one at your domain root. See https://llmstxt.org[/cyan]")
    console.print()


def print_text_report(results):
    """Print a formatted text report to the console."""
    url = results["url"]
    score = results["score"]
    grade = get_grade(score)
    audits = results["audits"]

    console.print(f"\n  [bold]GEO Audit Report[/bold]")
    console.print(f"  [dim]{url}[/dim]\n")

    # Score display
    color = get_score_color(score)
    console.print(Panel.fit(
        f"[bold {color}]{score}/100[/bold {color}]  [bold]Grade: {grade}[/bold]",
        title="AI Citability Score",
        border_style=color,
    ))
    console.print()

    # Individual audits
    for audit_result in audits:
        if audit_result.get("passed"):
            icon = "[green]PASS[/green]"
        elif audit_result.get("warning"):
            icon = "[yellow]WARN[/yellow]"
        else:
            icon = "[red]FAIL[/red]"

        console.print(f"  [{icon}] [bold]{audit_result['name']}[/bold]")
        console.print(f"  [dim]      {audit_result['description']}[/dim]")

        for detail in audit_result.get("details", []):
            console.print(f"  [dim]      - {detail}[/dim]")

        if audit_result.get("recommendation"):
            console.print(f"  [cyan]      Fix: {audit_result['recommendation']}[/cyan]")
        console.print()

    # Summary
    passed = sum(1 for a in audits if a.get("passed"))
    warned = sum(1 for a in audits if a.get("warning"))
    failed = sum(1 for a in audits if not a.get("passed") and not a.get("warning"))

    console.print("[dim]  ─────────────────────────────────────[/dim]")
    console.print(
        f"  [green]{passed} passed[/green]  "
        f"[yellow]{warned} warnings[/yellow]  "
        f"[red]{failed} failed[/red]\n"
    )


if __name__ == "__main__":
    main()
