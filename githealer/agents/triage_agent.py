from __future__ import annotations

from typing import List, Optional
from pathlib import Path
from githealer.agents.base import BaseAgent
from githealer.models import TestFailure, TriageAnalysis


class TriageAgent(BaseAgent):
    """Subagent responsible for diagnosing the root cause from failures and identifying suspect files."""

    SYSTEM_PROMPT = """You are the GitHealer Diagnostic/Triage Agent.
Your job is to analyze failed CI/CD test logs and determine:
1. Root cause of the failure.
2. The specific source files that must be modified to fix the issue.
3. Recommended fix strategy.

Respond STRICTLY in JSON format with this exact schema:
{
  "summary": "One sentence summary of the bug",
  "root_cause": "Detailed explanation of why the test or build failed",
  "suspect_files": ["path/to/file1.py", "path/to/file2.py"],
  "failing_tests": ["test_name_1"],
  "recommended_action": "Actionable instructions for the Coder agent to fix this bug",
  "confidence": 0.95
}
"""

    def diagnose(self, failures: List[TestFailure], repo_path: str | Path) -> TriageAnalysis:
        repo_root = Path(repo_path)
        failing_names = [f.test_name for f in failures]
        suspects: List[str] = []

        import re

        # Find candidate files from stack traces or repo
        raw_candidates = []
        for f in failures:
            if f.file_path:
                raw_candidates.append(f.file_path)
                p_name = Path(f.file_path).name
                if p_name.startswith("test_"):
                    raw_candidates.append(p_name[5:])
                elif p_name.endswith("_test.py"):
                    raw_candidates.append(p_name[:-8] + ".py")

            # Extract any file referenced in stack traces
            extracted = re.findall(r'(\b[A-Za-z0-9_\-\./\\]+\.(?:py|js|ts|go|rs))\b', f.stack_trace)
            raw_candidates.extend(extracted)

        for candidate in raw_candidates:
            # Clean up candidate path
            clean_cand = candidate.replace("\\", "/").strip().lstrip("/")
            norm_p = Path(clean_cand)

            if (repo_root / norm_p).is_file():
                suspects.append(str(norm_p).replace("\\", "/"))
            else:
                # Search repo for file basename
                matches = list(repo_root.glob(f"**/{norm_p.name}"))
                for m in matches:
                    try:
                        rel = m.relative_to(repo_root)
                        suspects.append(str(rel).replace("\\", "/"))
                    except Exception:
                        pass

        # De-duplicate while preserving order, prioritizing non-test files
        unique_suspects = list(dict.fromkeys(suspects))
        impl_files = [s for s in unique_suspects if not Path(s).name.startswith("test_") and not Path(s).name.endswith("_test.py")]
        test_files = [s for s in unique_suspects if s not in impl_files]
        suspects = impl_files + test_files

        # Check if LLM is available
        if self.llm.is_available():
            failure_details = "\n---\n".join([
                f"Test: {f.test_name}\nFile: {f.file_path}:{f.line_number}\nError: {f.error_type} - {f.error_message}\nStacktrace:\n{f.stack_trace}"
                for f in failures[:5]
            ])
            prompt = f"Failed Test Details:\n{failure_details}\n\nCandidate Suspect Files detected: {suspects}\nDiagnose the root cause."
            try:
                response = self.llm.generate(prompt=prompt, system_instruction=self.SYSTEM_PROMPT)
                data = self.extract_json(response)
                return TriageAnalysis(
                    summary=data.get("summary", "Automated CI failure diagnosis"),
                    root_cause=data.get("root_cause", failures[0].error_message),
                    suspect_files=data.get("suspect_files", suspects) or suspects,
                    failing_tests=data.get("failing_tests", failing_names) or failing_names,
                    recommended_action=data.get("recommended_action", "Apply surgical bug fix"),
                    confidence=float(data.get("confidence", 0.9))
                )
            except Exception:
                pass

        # Intelligent Heuristic Fallback (Offline Mode)
        primary_failure = failures[0] if failures else TestFailure(test_name="Unknown")
        return TriageAnalysis(
            summary=f"Failure in {primary_failure.test_name}: {primary_failure.error_type or 'Error'}",
            root_cause=f"{primary_failure.error_type}: {primary_failure.error_message or 'Assertion failed'}",
            suspect_files=suspects or ([primary_failure.file_path] if primary_failure.file_path else []),
            failing_tests=failing_names,
            recommended_action=f"Inspect and patch {primary_failure.file_path or 'failing module'} to satisfy tests.",
            confidence=0.85
        )
