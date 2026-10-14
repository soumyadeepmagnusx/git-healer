from __future__ import annotations

import os
import sys
import time
import subprocess
from pathlib import Path
from typing import Optional, Dict

from githealer.models import VerificationResult


class SandboxRunner:
    """Executes build and test commands in an isolated directory with timeout and safety controls."""

    def __init__(self, working_dir: str | Path, timeout: int = 60, env_overrides: Optional[Dict[str, str]] = None):
        self.working_dir = Path(working_dir).resolve()
        self.timeout = timeout
        self.env_overrides = env_overrides or {}

    def run(self, command: str) -> VerificationResult:
        """Run a test or validation command in the sandbox."""
        start_time = time.time()

        # Build clean environment with current venv prioritized
        env = os.environ.copy()
        venv_scripts = Path(sys.prefix) / ("Scripts" if os.name == "nt" else "bin")
        if venv_scripts.is_dir():
            env["PATH"] = f"{str(venv_scripts)}{os.pathsep}{env.get('PATH', '')}"

        # Add custom overrides
        env.update(self.env_overrides)
        env["PYTHONUNBUFFERED"] = "1"
        env["CI"] = "true"

        use_shell = True

        try:
            process = subprocess.run(
                command,
                cwd=str(self.working_dir),
                shell=use_shell,
                capture_output=True,
                text=True,
                timeout=self.timeout,
                env=env,
                encoding="utf-8",
                errors="replace"
            )
            duration = time.time() - start_time
            return VerificationResult(
                success=(process.returncode == 0),
                command=command,
                exit_code=process.returncode,
                stdout=process.stdout,
                stderr=process.stderr,
                duration_seconds=round(duration, 2)
            )
        except subprocess.TimeoutExpired as e:
            duration = time.time() - start_time
            stdout = e.stdout if isinstance(e.stdout, str) else (e.stdout.decode("utf-8", "replace") if e.stdout else "")
            stderr = e.stderr if isinstance(e.stderr, str) else (e.stderr.decode("utf-8", "replace") if e.stderr else "")
            return VerificationResult(
                success=False,
                command=command,
                exit_code=-1,
                stdout=stdout,
                stderr=f"{stderr}\n[GitHealer Sandbox] Command timed out after {self.timeout} seconds.",
                duration_seconds=round(duration, 2)
            )
        except Exception as e:
            duration = time.time() - start_time
            return VerificationResult(
                success=False,
                command=command,
                exit_code=-2,
                stdout="",
                stderr=f"[GitHealer Sandbox Error] {str(e)}",
                duration_seconds=round(duration, 2)
            )
