import sys
import os

# Ensure safe UTF-8 output on Windows consoles
if sys.platform == "win32":
    try:
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        if hasattr(sys.stderr, "reconfigure"):
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.syntax import Syntax
from rich.text import Text

from githealer.models import HealReport, TriageAnalysis, CodePatch, VerificationResult

# Disable legacy windows rendering which triggers charmap cp1252 encode errors
console = Console(legacy_windows=False, force_terminal=True)

BANNER = r"""[bold cyan]
   ____ _ _   _   _            _             
  / ___(_) |_| | | | ___  __ _| | ___ _ __   
 | |  _| | __| |_| |/ _ \/ _` | |/ _ \ '__|  
 | |_| | | |_|  _  |  __/ (_| | |  __/ |     
  \____|_|\__|_| |_|\___|\__,_|_|\___|_|     
[/bold cyan]
[dim italic]Autonomous Multi-Agent CI/CD Self-Healing Engine[/dim italic]
"""

def print_banner():
    console.print(BANNER)

def print_step(step_number: int, title: str):
    console.print(f"\n[bold yellow]⚡ Step {step_number}:[/bold yellow] [bold white]{title}[/bold white]")

def print_triage(triage: TriageAnalysis):
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Field", style="cyan", width=20)
    table.add_column("Diagnosis", style="white")

    table.add_row("Summary", triage.summary)
    table.add_row("Root Cause", triage.root_cause)
    table.add_row("Suspect Files", ", ".join(triage.suspect_files) or "None detected")
    table.add_row("Failing Tests", ", ".join(triage.failing_tests) or "General failure")
    table.add_row("Confidence", f"{triage.confidence * 100:.1f}%")

    console.print(Panel(table, title="[bold green]🩺 Triage & Diagnosis[/bold green]", expand=False))

def print_patch(patch: CodePatch):
    console.print(f"\n[bold cyan]Proposed Patch for:[/bold cyan] [underline]{patch.file_path}[/underline]")
    syntax = Syntax(patch.diff, "diff", theme="monokai", line_numbers=True)
    console.print(Panel(syntax, title=f"Unified Diff: {patch.file_path}", expand=False))

def print_verification(v: VerificationResult):
    status_text = "[bold green]PASSED[/bold green]" if v.success else "[bold red]FAILED[/bold red]"
    console.print(f"\n[bold]Sandbox Verification:[/bold] {status_text} (took {v.duration_seconds}s)")
    if not v.success and v.stderr:
        console.print(Panel(v.stderr[:1000], title="[red]Verification Error[/red]", style="red"))

def print_final_summary(report: HealReport):
    if report.success:
        msg = f"[bold green]✔ Self-healing completed successfully![/bold green]\n"
        if report.branch_name:
            msg += f"Branch: [cyan]{report.branch_name}[/cyan]\n"
        if report.pr_url:
            msg += f"Pull Request: [link={report.pr_url}]{report.pr_url}[/link]\n"
        console.print(Panel(msg, title="[bold green]Success[/bold green]", border_style="green"))
    else:
        console.print(Panel("[bold red]Self-healing was unable to resolve all test failures automatically.[/bold red]", title="[bold red]Review Needed[/bold red]", border_style="red"))
