from __future__ import annotations

from githealer.models import HealReport


class ExplainerAgent:
    """Subagent responsible for authoring human-readable PR descriptions and engineering reports."""

    @staticmethod
    def generate_pr_body(report: HealReport) -> str:
        status_badge = "🟢 **PASSED**" if (report.verification and report.verification.success) else "🔴 **PENDING REVIEW**"

        diffs_md = ""
        for p in report.patches:
            diffs_md += f"""
<details>
<summary><code>{p.file_path}</code> (Click to expand diff)</summary>

```diff
{p.diff}
```

*Note: {p.explanation}*
</details>
"""

        failing_tests_md = ""
        for f in report.failures:
            failing_tests_md += f"- ❌ `{f.test_name}` ({f.error_type or 'Error'}): {f.error_message}\n"

        verification_details = ""
        if report.verification:
            verification_details = f"""
### 🧪 Sandbox Verification
- **Command:** `{report.verification.command}`
- **Exit Code:** `{report.verification.exit_code}`
- **Duration:** `{report.verification.duration_seconds}s`
- **Status:** {status_badge}
"""

        body = f"""## 🩺 GitHealer Automated Self-Healing Patch

This automated Pull Request was created by **GitHealer** after detecting a failing CI run.

---

### 🔍 Diagnosis & Triage Summary
- **Root Cause:** {report.triage.root_cause if report.triage else 'Test failure detected in CI'}
- **Suspect Files:** {", ".join([f"`{f}`" for f in (report.triage.suspect_files if report.triage else [])])}
- **Recommended Action:** {report.triage.recommended_action if report.triage else 'Verified patch applied'}

### 💥 Failing Tests
{failing_tests_md or 'No specific test names isolated.'}

---

### 🛠️ Proposed Changes
{diffs_md or 'No diff generated.'}

{verification_details}

---
*Created automatically with [GitHealer](https://github.com/google-antigravity/git-healer) & Antigravity Multi-Agent Engine.*
"""
        return body
