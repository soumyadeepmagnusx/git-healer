from __future__ import annotations

import os
import json
import subprocess
import urllib.request
import urllib.error
from pathlib import Path
from typing import Optional, Dict, Any, List
from githealer.models import CodePatch


class GitHubClient:
    """Interacts with GitHub REST API and local Git command line."""

    def __init__(self, token: Optional[str] = None, git_executable: str = "git"):
        self.token = token or os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
        self.git_cmd = git_executable
        self.api_base = "https://api.github.com"

    def _headers(self) -> Dict[str, str]:
        headers = {
            "Accept": "application/vnd.github+json",
            "User-Agent": "GitHealer-SelfHealing-Agent/1.0"
        }
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    def create_local_branch_and_commit(
        self,
        repo_path: str | Path,
        branch_name: str,
        patches: List[CodePatch],
        commit_message: str
    ) -> bool:
        """Create a local git branch, apply the patches, and commit."""
        cwd = str(Path(repo_path).resolve())

        try:
            # 1. Create or checkout branch
            subprocess.run([self.git_cmd, "checkout", "-B", branch_name], cwd=cwd, check=True, capture_output=True, text=True)

            # 2. Apply patches to disk
            for p in patches:
                target = Path(cwd) / p.file_path
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(p.patched_code, encoding="utf-8")
                subprocess.run([self.git_cmd, "add", p.file_path], cwd=cwd, check=True, capture_output=True, text=True)

            # 3. Commit
            subprocess.run([self.git_cmd, "commit", "-m", commit_message], cwd=cwd, check=True, capture_output=True, text=True)
            return True
        except Exception:
            return False

    def create_pull_request(
        self,
        repo_slug: str,  # owner/repo
        title: str,
        body: str,
        head_branch: str,
        base_branch: str = "main"
    ) -> Optional[str]:
        """Open a PR via GitHub REST API."""
        if not self.token:
            return None

        url = f"{self.api_base}/repos/{repo_slug}/pulls"
        payload = json.dumps({
            "title": title,
            "body": body,
            "head": head_branch,
            "base": base_branch
        }).encode("utf-8")

        req = urllib.request.Request(url, data=payload, headers=self._headers(), method="POST")
        try:
            with urllib.request.urlopen(req, timeout=30) as res:
                data = json.loads(res.read().decode("utf-8"))
                return data.get("html_url")
        except Exception:
            return None
