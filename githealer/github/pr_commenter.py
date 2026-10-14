from __future__ import annotations

import os
import json
import urllib.request
from pathlib import Path
from typing import Optional, Dict, Any


class PRCommentBot:
    """Posts rich diagnostic and self-healing reports directly onto GitHub Pull Requests."""

    def __init__(self, token: Optional[str] = None):
        self.token = token or os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
        self.api_base = "https://api.github.com"

    def _headers(self) -> Dict[str, str]:
        headers = {
            "Accept": "application/vnd.github+json",
            "User-Agent": "GitHealer-Bot/1.0"
        }
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    def post_comment(self, repo_slug: str, pr_number: int, comment_body: str) -> Optional[Dict[str, Any]]:
        """Post a Markdown comment to an existing Pull Request or Issue."""
        if not self.token:
            return None

        url = f"{self.api_base}/repos/{repo_slug}/issues/{pr_number}/comments"
        payload = json.dumps({"body": comment_body}).encode("utf-8")
        req = urllib.request.Request(url, data=payload, headers=self._headers(), method="POST")

        try:
            with urllib.request.urlopen(req, timeout=30) as res:
                return json.loads(res.read().decode("utf-8"))
        except Exception:
            return None

    @classmethod
    def format_quick_comment(cls, report_path: str | Path) -> str:
        """Reads a githealer-report.md and wraps it in a branded GitHub PR comment."""
        p = Path(report_path)
        content = p.read_text(encoding="utf-8") if p.is_file() else "No report found."

        return f"""### 🩺 GitHealer CI Analysis & Patch Proposal

{content}

---
*Generated automatically by [GitHealer](https://github.com/soumyadeepmagnusx/git-healer).*
"""
