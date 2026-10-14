from __future__ import annotations

import sys
import shutil
import tempfile
from pathlib import Path
from typing import Optional, List

from githealer.config import GitHealerConfig
from githealer.models import HealReport, TestFailure, CodePatch, VerificationResult
from githealer.parsers.ci_log_parser import CILogParser
from githealer.llm.client import GeminiClient
from githealer.agents.triage_agent import TriageAgent
from githealer.agents.coder_agent import CoderAgent
from githealer.agents.explainer_agent import ExplainerAgent
from githealer.sandbox.runner import SandboxRunner
from githealer.github.client import GitHubClient
from githealer.reporting import terminal
from githealer.reporting.markdown import MarkdownReporter


class GitHealerOrchestrator:
    """Master multi-agent orchestrator managing the self-healing lifecycle."""

    def __init__(self, config: Optional[GitHealerConfig] = None):
        self.config = config or GitHealerConfig.load()
        self.llm = GeminiClient(api_key=self.config.gemini_api_key, model=self.config.model_name)
        self.triage_agent = TriageAgent(self.llm)
        self.coder_agent = CoderAgent(self.llm)
        self.explainer_agent = ExplainerAgent()
        self.github = GitHubClient(token=self.config.github_token, git_executable=self.config.git_executable)

    def detect_test_command(self, repo_path: Path) -> str:
        """Autodetect suitable test command for python, node, rust, or go repositories."""
        if self.config.test_command:
            return self.config.test_command

        if (repo_path / "pytest.ini").exists() or (repo_path / "setup.py").exists() or list(repo_path.glob("test*.py")) or list(repo_path.glob("tests/*.py")):
            return "pytest"
        if (repo_path / "package.json").exists():
            return "npm test"
        if (repo_path / "Cargo.toml").exists():
            return "cargo test"
        if list(repo_path.glob("*_test.go")):
            return "go test ./..."

        return "pytest"

    def heal(
        self,
        repo_path: str | Path,
        log_file: Optional[str | Path] = None,
        test_command: Optional[str] = None,
        apply_in_place: bool = True
    ) -> HealReport:
        """Execute the end-to-end self-healing loop."""
        repo_root = Path(repo_path).resolve()
        test_cmd = test_command or self.detect_test_command(repo_root)

        terminal.print_banner()
        terminal.print_step(1, f"Initializing GitHealer on [cyan]{repo_root.name}[/cyan]")

        sandbox = SandboxRunner(working_dir=repo_root, timeout=self.config.sandbox_timeout_seconds)

        # Step 1: Ingest failing log or run test command
        raw_log = ""
        if log_file and Path(log_file).is_file():
            raw_log = Path(log_file).read_text(encoding="utf-8", errors="replace")
            terminal.console.print(f"Loaded CI log from: [cyan]{log_file}[/cyan]")
        else:
            terminal.console.print(f"Executing baseline test command in sandbox: [bold]{test_cmd}[/bold]")
            initial_run = sandbox.run(test_cmd)
            raw_log = f"{initial_run.stdout}\n{initial_run.stderr}"
            if initial_run.success:
                terminal.console.print("[green]All tests are already passing! No healing needed.[/green]")
                return HealReport(repo_path=str(repo_root), success=True, verification=initial_run)

        # Step 2: Parse Failures
        terminal.print_step(2, "Parsing CI Failure Log")
        failures = CILogParser.parse(raw_log)
        terminal.console.print(f"Extracted [bold red]{len(failures)}[/bold red] failure signature(s).")
        for f in failures:
            terminal.console.print(f"  ❌ [bold]{f.test_name}[/bold] ({f.error_type}): {f.error_message}")

        # Step 3: Triage Agent
        terminal.print_step(3, "Triage Agent Formulating Diagnosis")
        triage = self.triage_agent.diagnose(failures, repo_root)
        terminal.print_triage(triage)

        # Backup files before applying modifications
        backups = {}
        for sf in triage.suspect_files:
            target_f = repo_root / sf
            if target_f.is_file():
                backups[sf] = target_f.read_text(encoding="utf-8")

        # Step 3.5: Create Safety Checkpoint Snapshot
        from githealer.safety.checkpoint import CheckpointManager
        chk_id = CheckpointManager.create_checkpoint(repo_root, label="pre-heal-snapshot")
        terminal.console.print(f"[dim]Created safety checkpoint snapshot: {chk_id}[/dim]")

        # Step 4: Iterative Coder & Verification Loop
        report = HealReport(
            repo_path=str(repo_root),
            failures=failures,
            triage=triage,
            success=False
        )

        patches: List[CodePatch] = []
        verified = False

        for iteration in range(1, self.config.max_retries + 1):
            terminal.print_step(4, f"Coder Agent Iteration {iteration}/{self.config.max_retries}")
            patches = self.coder_agent.generate_patch(repo_root, triage, failures)

            if not patches:
                terminal.console.print("[yellow]No applicable patches could be generated in this cycle.[/yellow]")
                break

            for p in patches:
                terminal.print_patch(p)
                # Apply patch to disk
                file_dest = repo_root / p.file_path
                file_dest.write_text(p.patched_code, encoding="utf-8")

            # Verify in sandbox
            terminal.print_step(5, f"Sandbox Verification (Iteration {iteration})")
            v_res = sandbox.run(test_cmd)
            terminal.print_verification(v_res)
            report.verification = v_res

            if v_res.success:
                terminal.console.print("[bold green]✔ Patch verified! All tests passed.[/bold green]")
                verified = True
                report.patches = patches
                report.success = True
                break
            else:
                terminal.console.print("[yellow]Verification failed. Feeding stack trace back to Coder Agent...[/yellow]")
                failures = CILogParser.parse(f"{v_res.stdout}\n{v_res.stderr}") or failures

        # If not verified and user didn't want in-place broken files, restore
        if not verified and not apply_in_place:
            for sf, orig in backups.items():
                (repo_root / sf).write_text(orig, encoding="utf-8")
            terminal.console.print("[dim]Restored original files after failed verification.[/dim]")

        # Step 6: PR Creation & Reports
        if verified and self.config.auto_create_pr:
            terminal.print_step(6, "Opening Self-Healed Pull Request")
            branch_name = f"githealer/fix-{int(Path(repo_root).stat().st_mtime)}"
            report.branch_name = branch_name
            pr_body = self.explainer_agent.generate_pr_body(report)
            committed = self.github.create_local_branch_and_commit(
                repo_path=repo_root,
                branch_name=branch_name,
                patches=report.patches,
                commit_message=f"fix: automated patch by GitHealer for {triage.summary}"
            )
            if committed:
                terminal.console.print(f"Created local branch [cyan]{branch_name}[/cyan] and committed patches.")

        # Save Markdown artifact
        report_path = repo_root / "githealer-report.md"
        MarkdownReporter.generate_report(report, report_path)
        terminal.console.print(f"Generated report artifact: [cyan]{report_path}[/cyan]")

        # Record Observability Metrics
        from githealer.observability.tracker import MetricsTracker, SessionMetrics
        MetricsTracker.record_session(SessionMetrics(
            timestamp=report.timestamp,
            target_repo=repo_root.name,
            duration_seconds=report.verification.duration_seconds if report.verification else 0.5,
            total_iterations=len(patches) or 1,
            success=report.success,
            estimated_cost_usd=0.0001
        ), repo_root)

        terminal.print_final_summary(report)
        return report
