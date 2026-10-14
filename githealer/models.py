from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone


@dataclass
class TestFailure:
    """Represents a single parsed test failure or build error from CI logs."""
    test_name: str
    file_path: Optional[str] = None
    line_number: Optional[int] = None
    error_type: Optional[str] = None
    error_message: str = ""
    stack_trace: str = ""
    framework: str = "generic"  # pytest, jest, go, cargo, etc.


@dataclass
class TriageAnalysis:
    """Diagnosis formulated by the Triage Agent."""
    summary: str
    root_cause: str
    suspect_files: List[str]
    failing_tests: List[str]
    recommended_action: str
    confidence: float = 0.95  # 0.0 to 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CodePatch:
    """Represents a proposed file modification to fix the bug."""
    file_path: str
    original_code: str
    patched_code: str
    diff: str
    explanation: str


@dataclass
class VerificationResult:
    """Result of running test command inside the sandbox."""
    success: bool
    command: str
    exit_code: int
    stdout: str
    stderr: str
    duration_seconds: float


@dataclass
class HealReport:
    """Complete summary of the self-healing workflow."""
    repo_path: str
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    failures: List[TestFailure] = field(default_factory=list)
    triage: Optional[TriageAnalysis] = None
    patches: List[CodePatch] = field(default_factory=list)
    verification: Optional[VerificationResult] = None
    pr_url: Optional[str] = None
    branch_name: Optional[str] = None
    success: bool = False
