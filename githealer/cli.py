import sys
import os

if sys.platform == "win32":
    try:
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        if hasattr(sys.stderr, "reconfigure"):
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

import shutil
import argparse
from pathlib import Path

from githealer import __version__
from githealer.config import GitHealerConfig
from githealer.orchestrator import GitHealerOrchestrator
from githealer.parsers.ci_log_parser import CILogParser
from githealer.reporting import terminal


def run_command(args):
    config = GitHealerConfig.load(config_path=args.config, repo_root=args.repo)
    if args.model:
        config.model_name = args.model
    if args.cmd:
        config.test_command = args.cmd
    if args.auto_pr:
        config.auto_create_pr = True

    orchestrator = GitHealerOrchestrator(config)
    orchestrator.heal(
        repo_path=args.repo,
        log_file=args.log,
        test_command=args.cmd
    )


def triage_command(args):
    terminal.print_banner()
    log_path = Path(args.log_file)
    if not log_path.is_file():
        terminal.console.print(f"[red]Error: Log file not found: {log_path}[/red]")
        sys.exit(1)

    raw_log = log_path.read_text(encoding="utf-8", errors="replace")
    failures = CILogParser.parse(raw_log)

    terminal.console.print(f"Parsed [bold red]{len(failures)}[/bold red] failure signature(s) from [cyan]{log_path.name}[/cyan]:\n")
    for idx, f in enumerate(failures, 1):
        terminal.console.print(f"[bold yellow]#{idx}[/bold yellow] [bold]{f.test_name}[/bold]")
        terminal.console.print(f"   Framework: [dim]{f.framework}[/dim]")
        terminal.console.print(f"   Location:  [cyan]{f.file_path or 'unknown'}:{f.line_number or '?'}[/cyan]")
        terminal.console.print(f"   Error:     [red]{f.error_type}: {f.error_message}[/red]\n")


def demo_command(args):
    terminal.print_banner()
    terminal.console.print("[bold yellow]🚀 Running GitHealer Interactive Demo![/bold yellow]")
    terminal.console.print("Setting up a sandbox repository with an intentional ZeroDivisionError bug...\n")

    demo_dir = Path("demo_sandbox_repo").resolve()
    if demo_dir.exists():
        shutil.rmtree(demo_dir)
    demo_dir.mkdir(parents=True, exist_ok=True)

    # Write broken code
    calc_py = demo_dir / "calculator.py"
    calc_py.write_text("""# Sample Calculator Module

def add(a, b):
    return a + b

def subtract(a, b):
    return a - b

def multiply(a, b):
    return a * b

def divide(a, b):
    # Intentional bug: missing zero division guard
    return a / b
""", encoding="utf-8")

    # Write test file
    test_calc_py = demo_dir / "test_calculator.py"
    test_calc_py.write_text("""import pytest
from calculator import add, subtract, multiply, divide

def test_add():
    assert add(2, 3) == 5

def test_subtract():
    assert subtract(5, 2) == 3

def test_divide():
    assert divide(10, 2) == 5

def test_divide_by_zero():
    # Expects ValueError('Cannot divide by zero')
    with pytest.raises(ValueError, match="Cannot divide by zero"):
        divide(10, 0)
""", encoding="utf-8")

    terminal.console.print(f"Created demo sandbox at: [cyan]{demo_dir}[/cyan]")
    terminal.console.print("Invoking GitHealer multi-agent workflow on the broken repo...\n")

    config = GitHealerConfig.load(repo_root=str(demo_dir))
    orchestrator = GitHealerOrchestrator(config)
    orchestrator.heal(repo_path=demo_dir, test_command="pytest")


def dashboard_command(args):
    terminal.print_banner()
    terminal.console.print(f"[bold green]Starting GitHealer Live Web Dashboard on port {args.port}...[/bold green]")
    from githealer.dashboard.server import DashboardServer
    DashboardServer.serve(port=args.port, open_browser=not args.no_browser)


def doctor_command(args):
    terminal.print_banner()
    terminal.console.print("[bold cyan]🩺 GitHealer Environment Doctor[/bold cyan]\n")
    from githealer.environment.doctor import EnvironmentDoctor
    ecosystems = EnvironmentDoctor.detect_ecosystem(args.repo)
    terminal.console.print("Detected Project Ecosystems:")
    for eco, present in ecosystems.items():
        icon = "[green]✔[/green]" if present else "[dim]✗[/dim]"
        terminal.console.print(f"  {icon} {eco.capitalize()}")

    if args.log:
        log_txt = Path(args.log).read_text(encoding="utf-8", errors="replace")
        missing = EnvironmentDoctor.diagnose_missing_dependencies(log_txt)
        if missing:
            terminal.console.print(f"\n[bold red]Detected {len(missing)} missing package(s):[/bold red]")
            for eco, pkg in missing:
                terminal.console.print(f"  - [{eco}] [bold]{pkg}[/bold]")
            suggestions = EnvironmentDoctor.suggest_remediation(missing)
            terminal.console.print("\n[bold yellow]Recommended remediation commands:[/bold yellow]")
            for cmd in suggestions:
                terminal.console.print(f"  [cyan]$ {cmd}[/cyan]")
        else:
            terminal.console.print("\n[green]No missing package errors found in log.[/green]")


def check_flaky_command(args):
    terminal.print_banner()
    terminal.console.print(f"[bold yellow]🔬 Testing for flaky test behavior ({args.runs} runs)...[/bold yellow]\n")
    from githealer.sandbox.runner import SandboxRunner
    from githealer.flaky.detector import FlakyTestDetector
    sandbox = SandboxRunner(working_dir=args.repo)
    detector = FlakyTestDetector(sandbox)
    report = detector.analyze(test_command=args.cmd, runs=args.runs)

    color = "yellow" if report.is_flaky else ("green" if report.failures == 0 else "red")
    terminal.console.print(f"[{color}]Result: {report.diagnosis}[/{color}]")
    terminal.console.print(f"Passes: [green]{report.passes}[/green] / Failures: [red]{report.failures}[/red]")
    if report.failing_tests:
        terminal.console.print(f"Intermittent / Failing tests: {', '.join(report.failing_tests)}")


def rollback_command(args):
    terminal.print_banner()
    from githealer.safety.checkpoint import CheckpointManager
    terminal.console.print("[bold yellow]Rolling back to previous checkpoint...[/bold yellow]")
    success = CheckpointManager.rollback(args.repo, checkpoint_id=args.checkpoint)
    if success:
        terminal.console.print("[bold green]✔ Rollback successful! Restored clean working state.[/bold green]")
    else:
        terminal.console.print("[bold red]Failed to restore checkpoint. No valid checkpoints found.[/bold red]")


def main():
    parser = argparse.ArgumentParser(
        prog="git-healer",
        description="Autonomous Multi-Agent CI/CD Self-Healing Engine"
    )
    parser.add_argument("--version", "-v", action="version", version=f"GitHealer {__version__}")

    subparsers = parser.add_subparsers(dest="command", help="Available subcommands")

    # Run
    run_parser = subparsers.add_parser("run", help="Run end-to-end self-healing loop")
    run_parser.add_argument("--repo", "-r", default=".", help="Path to repository (default: current directory)")
    run_parser.add_argument("--log", "-l", help="Optional path to failed CI log file")
    run_parser.add_argument("--cmd", "-c", help="Custom test command (e.g. 'pytest', 'npm test')")
    run_parser.add_argument("--model", "-m", help="Gemini model (e.g. 'gemini-2.5-flash')")
    run_parser.add_argument("--config", help="Path to custom .githealer.yaml")
    run_parser.add_argument("--auto-pr", action="store_true", help="Automatically create git branch and PR")
    run_parser.set_defaults(func=run_command)

    # Triage
    triage_parser = subparsers.add_parser("triage", help="Parse and diagnose raw CI logs")
    triage_parser.add_argument("log_file", help="Path to CI failure log file")
    triage_parser.set_defaults(func=triage_command)

    # Demo
    demo_parser = subparsers.add_parser("demo", help="Run an instant interactive demo with a simulated bug")
    demo_parser.set_defaults(func=demo_command)

    # Dashboard
    dash_parser = subparsers.add_parser("dashboard", help="Start local web dashboard")
    dash_parser.add_argument("--port", "-p", type=int, default=8080, help="Port to run dashboard on")
    dash_parser.add_argument("--no-browser", action="store_true", help="Don't open browser automatically")
    dash_parser.set_defaults(func=dashboard_command)

    # Doctor
    doc_parser = subparsers.add_parser("doctor", help="Diagnose environment and missing dependencies")
    doc_parser.add_argument("--repo", "-r", default=".", help="Repository path")
    doc_parser.add_argument("--log", "-l", help="Optional CI failure log")
    doc_parser.set_defaults(func=doctor_command)

    # Check-Flaky
    flaky_parser = subparsers.add_parser("check-flaky", help="Check if test failures are intermittent/flaky")
    flaky_parser.add_argument("--cmd", "-c", default="pytest", help="Test command to repeat")
    flaky_parser.add_argument("--runs", "-n", type=int, default=3, help="Number of test runs")
    flaky_parser.add_argument("--repo", "-r", default=".", help="Repository path")
    flaky_parser.set_defaults(func=check_flaky_command)

    # Rollback
    rb_parser = subparsers.add_parser("rollback", help="Safely roll back changes using checkpoints")
    rb_parser.add_argument("--repo", "-r", default=".", help="Repository path")
    rb_parser.add_argument("--checkpoint", help="Specific checkpoint ID (defaults to latest)")
    rb_parser.set_defaults(func=rollback_command)

    # Comment PR
    def comment_pr_command(args):
        terminal.print_banner()
        from githealer.github.pr_commenter import PRCommentBot
        bot = PRCommentBot()
        body = PRCommentBot.format_quick_comment(args.report)
        terminal.console.print(f"[bold cyan]Posting self-healing report to PR #{args.pr}...[/bold cyan]")
        res = bot.post_comment(args.repo_slug, args.pr, body)
        if res:
            terminal.console.print(f"[bold green]✔ Successfully commented on PR #{args.pr}![/bold green]")
        else:
            terminal.console.print("[yellow]Notice: Comment skipped or token missing (check GITHUB_TOKEN).[/yellow]")

    comment_parser = subparsers.add_parser("comment-pr", help="Post GitHealer report to GitHub Pull Request")
    comment_parser.add_argument("--repo-slug", required=True, help="GitHub repository (e.g. owner/repo)")
    comment_parser.add_argument("--pr", type=int, required=True, help="Pull Request number")
    comment_parser.add_argument("--report", default="githealer-report.md", help="Path to report markdown")
    comment_parser.set_defaults(func=comment_pr_command)

    # Stats / Observability
    def stats_command(args):
        terminal.print_banner()
        from githealer.observability.tracker import MetricsTracker
        from rich.table import Table
        from rich.panel import Panel

        summary = MetricsTracker.get_summary(args.repo)
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="bold white")

        table.add_row("Total Healing Runs", str(summary["total_runs"]))
        table.add_row("Successful Fixes", str(summary["successful_runs"]))
        table.add_row("Success Rate", f"{summary['success_rate']}%")
        table.add_row("Avg Resolution Time", f"{summary['avg_duration']}s")
        table.add_row("Total Estimated API Cost", f"${summary['total_cost_usd']}")

        terminal.console.print(Panel(table, title="[bold green]📈 GitHealer Observability & Token Metrics[/bold green]", expand=False))

    stats_parser = subparsers.add_parser("stats", help="Display self-healing performance and token statistics")
    stats_parser.add_argument("--repo", "-r", default=".", help="Repository path")
    stats_parser.set_defaults(func=stats_command)

    # Repository Health & Disaster Recovery Forwarders
    def check_forwarder(args):
        import healer
        healer.check.callback()

    def fix_forwarder(args):
        import healer
        healer.fix.callback()

    def cleanup_forwarder(args):
        import healer
        healer.cleanup.callback()

    def secrets_forwarder(args):
        import healer
        healer.secrets.callback()

    check_parser = subparsers.add_parser("check", help="Scan repository for detached HEAD, stale branches, and health")
    check_parser.set_defaults(func=check_forwarder)

    fix_parser = subparsers.add_parser("fix", help="Interactive Git disaster recovery wizard (reflog, rebase rescue)")
    fix_parser.set_defaults(func=fix_forwarder)

    clean_parser = subparsers.add_parser("cleanup", help="Target and purge merged local branches")
    clean_parser.set_defaults(func=cleanup_forwarder)

    sec_parser = subparsers.add_parser("secrets", help="Scan repository for leaked credentials & API keys")
    sec_parser.set_defaults(func=secrets_forwarder)

    # Commit Doctor / Commit Lint
    def commit_lint_command(args):
        terminal.print_banner()
        from githealer.git_doctor.commit_linter import CommitDoctor
        msg = args.message
        if not msg:
            # Check last git commit message
            import subprocess
            res = subprocess.run(["git", "log", "-1", "--pretty=%B"], capture_output=True, text=True)
            msg = res.stdout.strip() if res.returncode == 0 else ""

        if not msg:
            terminal.console.print("[red]Error: No commit message provided and no git commit history found.[/red]")
            return

        terminal.console.print(f"[bold cyan]🔍 Linting Commit Message:[/bold cyan] \"{msg.splitlines()[0]}\"\n")
        res = CommitDoctor.lint(msg)

        if res.is_valid:
            terminal.console.print("[bold green]✔ Valid Conventional Commit![/bold green]")
            terminal.console.print(f"  Type:  [green]{res.commit_type}[/green]")
            if res.scope:
                terminal.console.print(f"  Scope: [cyan]{res.scope}[/cyan]")
            if res.is_breaking:
                terminal.console.print("  [bold red]BREAKING CHANGE[/bold red]")
        else:
            terminal.console.print("[bold red]❌ Commit Message Violations:[/bold red]")
            for err in res.errors:
                terminal.console.print(f"  - [red]{err}[/red]")
            if res.suggestion:
                terminal.console.print(f"\n[bold yellow]💡 Suggested Conventional Format:[/bold yellow]\n  [green]{res.suggestion}[/green]")

        if res.warnings:
            terminal.console.print("\n[yellow]⚠️ Warnings:[/yellow]")
            for w in res.warnings:
                terminal.console.print(f"  - [yellow]{w}[/yellow]")

    commit_parser = subparsers.add_parser("commit-lint", help="Verify commit messages against Conventional Commits")
    commit_parser.add_argument("--message", "-m", help="Message to check (defaults to latest git commit)")
    commit_parser.set_defaults(func=commit_lint_command)

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        sys.exit(0)

    args.func(args)


if __name__ == "__main__":
    main()
