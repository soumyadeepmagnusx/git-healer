from __future__ import annotations

import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List
from githealer.sandbox.runner import SandboxRunner
from githealer.parsers.ci_log_parser import CILogParser


@dataclass
class FlakinessReport:
    total_runs: int
    passes: int
    failures: int
    flakiness_percentage: float
    is_flaky: bool
    failing_tests: List[str] = field(default_factory=list)
    diagnosis: str = ""


class FlakyTestDetector:
    """Detects intermittent and non-deterministic test failures by running rapid sandbox trials."""

    def __init__(self, sandbox: SandboxRunner):
        self.sandbox = sandbox

    def analyze(self, test_command: str, runs: int = 3) -> FlakinessReport:
        passes = 0
        failures = 0
        failed_tests_seen = []

        for i in range(runs):
            res = self.sandbox.run(test_command)
            if res.success:
                passes += 1
            else:
                failures += 1
                parsed = CILogParser.parse(f"{res.stdout}\n{res.stderr}")
                for p in parsed:
                    if p.test_name not in failed_tests_seen:
                        failed_tests_seen.append(p.test_name)

        is_flaky = (passes > 0 and failures > 0)
        flakiness_pct = (passes / runs * 100) if is_flaky else (0.0 if passes == runs else 100.0)

        if is_flaky:
            diagnosis = f"FLAKY TEST DETECTED: Succeeded in {passes}/{runs} runs. Likely caused by race conditions, timing timeouts, or unseeded randomness."
        elif failures == runs:
            diagnosis = f"DETERMINISTIC BUG: Failed consistently in all {runs} runs. Genuine code defect requiring a patch."
        else:
            diagnosis = f"STABLE: Passed in all {runs} runs."

        return FlakinessReport(
            total_runs=runs,
            passes=passes,
            failures=failures,
            flakiness_percentage=flakiness_pct,
            is_flaky=is_flaky,
            failing_tests=failed_tests_seen,
            diagnosis=diagnosis
        )
