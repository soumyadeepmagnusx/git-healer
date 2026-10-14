from __future__ import annotations

import re
from pathlib import Path
from typing import List, Optional
from githealer.agents.base import BaseAgent
from githealer.models import TestFailure, TriageAnalysis, CodePatch
from githealer.parsers.diff_parser import DiffParser


class CoderAgent(BaseAgent):
    """Subagent responsible for generating surgical code patches to resolve the failure."""

    SYSTEM_PROMPT = """You are the GitHealer Coder Agent.
You write surgical, minimal, regression-free code fixes for software bugs.
You will be provided:
1. Diagnosis & Root Cause from the Triage Agent.
2. The failing test details & stack trace.
3. The exact content of the file that needs fixing.

CRITICAL INSTRUCTIONS:
- Preserve all existing coding style, imports, and indentation.
- Do NOT rewrite unrelated parts of the file.
- Return ONLY the updated code wrapped in ```python (or the appropriate language) block.
- Do NOT include extraneous conversational commentary outside the code block.
"""

    def generate_patch(
        self,
        repo_path: str | Path,
        triage: TriageAnalysis,
        failures: List[TestFailure]
    ) -> List[CodePatch]:
        repo_root = Path(repo_path)
        patches: List[CodePatch] = []

        for rel_path in triage.suspect_files:
            full_path = repo_root / rel_path
            if not full_path.is_file():
                continue

            try:
                original_code = full_path.read_text(encoding="utf-8")
            except Exception:
                continue

            patched_code = None
            explanation = ""

            # Try LLM Fix if available
            if self.llm.is_available():
                prompt = f"""File Path: {rel_path}
Diagnosis: {triage.root_cause}
Recommended Action: {triage.recommended_action}

Failing Tests:
{chr(10).join([f"- {f.test_name}: {f.error_message}" for f in failures])}

Current File Content:
```{Path(rel_path).suffix.lstrip('.')}
{original_code}
```

Provide the complete updated content of {rel_path} that fixes this bug."""
                try:
                    response = self.llm.generate(prompt=prompt, system_instruction=self.SYSTEM_PROMPT)
                    extracted = self.extract_code_block(response)
                    is_valid, err = DiffParser.validate_syntax(extracted, rel_path)
                    if is_valid and extracted != original_code:
                        patched_code = extracted
                        explanation = f"AI patch applied by CoderAgent to resolve: {triage.root_cause}"
                except Exception:
                    pass

            # Intelligent Mock / Fallback Fix for known patterns (ensures demo works out of the box)
            if not patched_code:
                patched_code, explanation = self._heuristic_fix(original_code, rel_path, failures)

            if patched_code and patched_code != original_code:
                patch = DiffParser.create_patch(
                    file_path=rel_path,
                    original_code=original_code,
                    patched_code=patched_code,
                    explanation=explanation
                )
                patches.append(patch)

        return patches

    def _heuristic_fix(self, code: str, file_path: str, failures: List[TestFailure]) -> tuple[Optional[str], str]:
        """Provides smart rule-based patching for common bugs (e.g. ZeroDivisionError, off-by-one, None check)."""
        new_code = code

        for f in failures:
            msg = (f.error_message + " " + f.stack_trace).lower()

            # Fix 1: ZeroDivisionError
            if "zerodivisionerror" in msg or "division by zero" in msg:
                # Look for divide function: return a / b
                if re.search(r"def divide\s*\(\s*a\s*,\s*b\s*\):", new_code):
                    new_code = re.sub(
                        r"(def divide\s*\(\s*a\s*,\s*b\s*\):[^\n]*\n)(\s*)([^\n]+)",
                        r"\1\2if b == 0:\n\2    raise ValueError('Cannot divide by zero')\n\2\3",
                        new_code
                    )
                    return new_code, "Added zero-division validation check raising ValueError"

            # Fix 2: Off-by-one or equality check
            if "assert " in msg and "==" in msg:
                # If off-by-one in loop or calculation
                if "- 1" in new_code and "+ 1" in msg:
                    new_code = new_code.replace("- 1", "")
                    return new_code, "Corrected off-by-one boundary calculation"

            # Fix 3: Missing dict key
            if "keyerror" in msg:
                # Change d[k] to d.get(k, default)
                match = re.search(r"KeyError:\s*['\"]([^'\"]+)['\"]", f.error_message)
                if match:
                    key = match.group(1)
                    if f"['{key}']" in new_code:
                        new_code = new_code.replace(f"['{key}']", f".get('{key}')")
                        return new_code, f"Safely accessed dictionary key '{key}' using .get()"

        return None, ""
