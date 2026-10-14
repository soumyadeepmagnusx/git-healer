#!/usr/bin/env python3
"""
Git Healer: Automagically diagnose and fix your broken Git repositories & CI/CD pipelines.
"""

from __future__ import annotations

import os
import re
import sys
import subprocess
from pathlib import Path

# Ensure UTF-8 on Windows
if sys.platform == "win32":
    try:
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        if hasattr(sys.stderr, "reconfigure"):
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

try:
    import click
    import questionary
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
except ImportError:
    print("Missing dependencies. Run: pip install click questionary rich")
    sys.exit(1)

# Find Git executable
GIT_CMD = "git"
if os.name == "nt":
    for candidate in [r"C:\Program Files\Git\cmd\git.exe", os.path.expandvars(r"%LOCALAPPDATA%\Programs\Git\cmd\git.exe")]:
        if os.path.isfile(candidate):
            GIT_CMD = candidate
            break

console = Console(legacy_windows=False, force_terminal=True)


def run_git(command: list) -> str:
    """Helper function to execute Git commands safely."""
    try:
        result = subprocess.run(
            [GIT_CMD] + command,
            capture_output=True,
            text=True,
            check=True,
            encoding="utf-8",
            errors="replace"
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        return f"Error: {e.stderr.strip()}"
    except Exception as e:
        return f"Error: {str(e)}"


@click.group()
def cli():
    """Git Healer: Automagically diagnose and fix your broken Git repositories & CI/CD."""
    pass


@cli.command()
def check():
    """Scan the repository for common issues, detached HEAD, stale branches, and leaks."""
    console.print("\n[bold cyan]🔍 Scanning repository health...[/bold cyan]\n")

    table = Table(title="Git Healer Diagnostics", header_style="bold magenta")
    table.add_column("Diagnostic Check", style="cyan", width=22)
    table.add_column("Status", style="bold", width=18)
    table.add_column("Recommendation", style="yellow")

    # 1. Check for detached HEAD
    head_status = run_git(["symbolic-ref", "-q", "HEAD"])
    if "Error:" in head_status:
        table.add_row("Detached HEAD", "[bold red]CRITICAL[/bold red]", "You are detached from a branch. Run 'git switch <branch>'.")
    else:
        table.add_row("HEAD State", "[green]Healthy[/green]", "On a valid branch.")

    # 2. Check for unmerged/stale local branches
    merged_branches = run_git(["branch", "--merged"])
    if not merged_branches.startswith("Error:"):
        merged_list = [b.strip() for b in merged_branches.splitlines() if b.strip() and not b.startswith("*") and b.strip() not in ["main", "master"]]
        if merged_list:
            table.add_row("Stale Branches", f"[bold yellow]{len(merged_list)} Stale[/bold yellow]", f"Merged branches found ({', '.join(merged_list[:3])}). Run 'git-healer cleanup'.")
        else:
            table.add_row("Local Branches", "[green]Clean[/green]", "No unneeded merged branches.")
    else:
        table.add_row("Local Branches", "[dim]N/A[/dim]", "No git branches found.")

    # 3. Check for uncommitted work
    status_out = run_git(["status", "--porcelain"])
    if status_out and not status_out.startswith("Error:"):
        lines = status_out.splitlines()
        table.add_row("Working Tree", f"[bold yellow]{len(lines)} Uncommitted[/bold yellow]", "Uncommitted changes found. Commit or stash your work.")
    else:
        table.add_row("Working Tree", "[green]Clean[/green]", "Working directory is clean.")

    # 4. Check for committed or untracked .env / secret files
    secret_patterns = [".env", ".env.local", "*.pem", "*.key", "id_rsa"]
    found_secrets = []
    for pat in secret_patterns:
        for p in Path(".").glob(f"**/{pat}"):
            if ".git" not in p.parts and ".venv" not in p.parts:
                found_secrets.append(str(p))

    if found_secrets:
        table.add_row("Secret Files", "[bold red]WARNING[/bold red]", f"Found exposed secret files: {', '.join(found_secrets[:2])}. Add to .gitignore!")
    else:
        table.add_row("Secret Files", "[green]Clean[/green]", "No obvious secret/env files exposed.")

    console.print(table)


@cli.command()
def fix():
    """Interactive step-by-step Git disaster recovery wizard."""
    console.print("[bold green]🩹 Welcome to the Git Healer Emergency Room.[/bold green]\n")

    choice = questionary.select(
        "What went wrong in your repository?",
        choices=[
            "I accidentally did a hard reset and lost my work!",
            "I am stuck in a messy rebase or merge conflict.",
            "I committed secrets / API keys by mistake.",
            "I need to quickly squash my last few messy commits."
        ]
    ).ask()

    if choice == "I accidentally did a hard reset and lost my work!":
        console.print("\n[bold yellow]Analyzing Reflog to find your lost commits...[/bold yellow]")
        reflog = run_git(["reflog", "-n", "8"])
        console.print(f"\n[dim]Recent Git history (Reflog):[/dim]\n{reflog}\n")

        commit = questionary.text("Enter the commit hash (e.g. abc1234) you want to restore:").ask()
        if commit:
            confirm = questionary.confirm(f"Are you sure you want to force reset to {commit}?").ask()
            if confirm:
                res = run_git(["reset", "--hard", commit.strip()])
                console.print(f"[bold green]✔ Success![/bold green] Repository healed to commit {commit}.")

    elif choice == "I am stuck in a messy rebase or merge conflict.":
        abort = questionary.confirm("Do you want to safely abort and reset to how things were?").ask()
        if abort:
            run_git(["rebase", "--abort"])
            run_git(["merge", "--abort"])
            console.print("[bold green]✔ Aborted rebase/merge successfully. Working directory is safe.[/bold green]")

    elif choice == "I committed secrets / API keys by mistake.":
        console.print("\n[bold red]🚨 Secret Leak Detected:[/bold red]")
        console.print("To remove the secret from the latest commit without losing your code changes:")
        console.print("  [cyan]git reset --soft HEAD~1[/cyan]")
        console.print("Then add the sensitive file to [bold].gitignore[/bold] before committing again.\n")
        undo = questionary.confirm("Would you like GitHealer to soft-undo the latest commit now?").ask()
        if undo:
            run_git(["reset", "--soft", "HEAD~1"])
            console.print("[bold green]✔ Soft-reset performed! Your file changes are preserved in the staging area.[/bold green]")

    elif choice == "I need to quickly squash my last few messy commits.":
        count = questionary.text("How many recent commits do you want to squash into one?", default="2").ask()
        if count and count.isdigit() and int(count) > 1:
            n = int(count)
            msg = questionary.text("Enter the unified commit message:").ask()
            if msg:
                run_git(["reset", "--soft", f"HEAD~{n}"])
                run_git(["commit", "-m", msg.strip()])
                console.print(f"[bold green]✔ Squashed last {n} commits into a single clean commit![/bold green]")


@cli.command()
def cleanup():
    """Target and purge merged local branches to keep your workspace pristine."""
    console.print("\n[bold cyan]🧹 Target and Clean Stale Merged Branches[/bold cyan]\n")
    merged = run_git(["branch", "--merged"])
    if merged.startswith("Error:"):
        console.print("[red]Could not retrieve branch list.[/red]")
        return

    to_delete = [
        b.strip() for b in merged.splitlines()
        if b.strip() and not b.startswith("*") and b.strip() not in ["main", "master", "develop"]
    ]

    if not to_delete:
        console.print("[green]✔ No stale merged branches found. Workspace is clean![/green]")
        return

    console.print(f"Found [bold yellow]{len(to_delete)}[/bold yellow] merged branch(es): {', '.join(to_delete)}")
    confirm = questionary.confirm("Delete these merged local branches?").ask()
    if confirm:
        for branch in to_delete:
            res = run_git(["branch", "-d", branch])
            console.print(f"  [green]✔ Deleted {branch}[/green]")
        console.print("\n[bold green]Cleanup complete![/bold green]")


@cli.command()
def secrets():
    """Scan tracked and working tree files for exposed API keys and credentials."""
    console.print("\n[bold red]🔐 Scanning for leaked credentials & API keys...[/bold red]\n")

    patterns = {
        "Google/Gemini API Key": r"AIza[0-9A-Za-z\-_]{35}",
        "OpenAI API Key": r"sk-[a-zA-Z0-9]{20,48}",
        "GitHub Personal Access Token": r"gh[pousr]_[A-Za-z0-9_]{36,255}",
        "AWS Access Key ID": r"AKIA[0-9A-Z]{16}",
        "Generic Private Key": r"-----BEGIN [A-Z ]+PRIVATE KEY-----",
    }

    leaks = []
    root = Path(".")
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        rel = path.relative_to(root)
        if any(part in [".git", ".venv", "venv", "__pycache__", "node_modules"] for part in rel.parts):
            continue

        try:
            content = path.read_text(encoding="utf-8", errors="ignore")
            for label, regex in patterns.items():
                matches = re.findall(regex, content)
                for m in matches:
                    masked = m[:4] + "*" * (len(m) - 8) + m[-4:] if len(m) > 8 else "****"
                    leaks.append((str(rel), label, masked))
        except Exception:
            pass

    if leaks:
        table = Table(title="🚨 Leaked Credentials Found!", header_style="bold red")
        table.add_column("File", style="cyan")
        table.add_column("Credential Type", style="yellow")
        table.add_column("Masked Secret", style="red")
        for f, t, s in leaks:
            table.add_row(f, t, s)
        console.print(table)
        console.print("\n[bold red]ACTION REQUIRED:[/bold red] Remove these keys immediately and revoke them with the service provider!")
    else:
        console.print("[bold green]✔ No leaked API keys or credentials detected across your repository.[/bold green]")


if __name__ == "__main__":
    cli()
