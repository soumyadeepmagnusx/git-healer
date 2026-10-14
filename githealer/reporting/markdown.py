from __future__ import annotations

from pathlib import Path
from githealer.models import HealReport


class MarkdownReporter:
    """Writes detailed Markdown reports and artifacts."""

    @staticmethod
    def generate_report(report: HealReport, output_file: str | Path = "githealer-report.md") -> str:
        status_str = "SUCCESS" if report.success else "NEEDS_REVIEW"

        mermaid_graph = """```mermaid
flowchart LR
    CI["Failing CI Run"] --> Triage["Triage Agent (Diagnose)"]
    Triage --> Coder["Coder Agent (Patch)"]
    Coder --> Sandbox["Sandbox Verification"]
    Sandbox -->|"Tests Pass"| Verified["Self-Healed PR"]
    Sandbox -->|"Tests Fail"| Coder
```"""

        patches_md = ""
        for p in report.patches:
            patches_md += f"""
### File: `{p.file_path}`

```diff
{p.diff}
```
*Patch rationale: {p.explanation}*
"""

        content = f"""# 🩺 GitHealer Report: {status_str}

Generated on: `{report.timestamp}`  
Repository: `{report.repo_path}`

{mermaid_graph}

## 📋 Triage Diagnosis
- **Summary:** {report.triage.summary if report.triage else 'N/A'}
- **Root Cause:** {report.triage.root_cause if report.triage else 'N/A'}
- **Confidence:** {f"{report.triage.confidence * 100:.1f}%" if report.triage else 'N/A'}
- **Suspect Files:** {", ".join([f"`{f}`" for f in (report.triage.suspect_files if report.triage else [])])}

## 🛠️ Generated Patches
{patches_md or 'No patches generated.'}

## 🧪 Verification
- **Command:** `{report.verification.command if report.verification else 'N/A'}`
- **Exit Code:** `{report.verification.exit_code if report.verification else 'N/A'}`
- **Success:** `{report.verification.success if report.verification else False}`
- **Duration:** `{report.verification.duration_seconds if report.verification else 0}s`

---
*Powered by GitHealer & Antigravity Multi-Agent Architecture.*
"""
        out_p = Path(output_file)
        out_p.write_text(content, encoding="utf-8")
        return content
