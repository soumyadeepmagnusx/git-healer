from __future__ import annotations

import os
import re
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional


def _resolve_git() -> str:
    which_git = shutil.which("git")
    if which_git:
        return which_git
    if os.name == "nt":
        for p in [r"C:\Program Files\Git\cmd\git.exe", os.path.expandvars(r"%LOCALAPPDATA%\Programs\Git\cmd\git.exe")]:
            if os.path.isfile(p):
                return p
    return "git"


@dataclass
class BranchInfo:
    name: str
    is_current: bool
    commit_hash: str
    upstream: Optional[str] = None
    ahead: int = 0
    behind: int = 0
    commit_message: str = ""


class BranchVisualizer:
    """Inspects Git branches, tracks ahead/behind status relative to remote, and formats summaries."""

    @classmethod
    def get_branches(cls, repo_path: str | Path = ".") -> List[BranchInfo]:
        root = Path(repo_path).resolve()
        branches = []
        git_cmd = _resolve_git()
        try:
            res = subprocess.run(
                [git_cmd, "branch", "-vv", "--no-color"],
                cwd=str(root),
                capture_output=True,
                text=True,
                check=True,
                encoding="utf-8",
                errors="replace"
            )

            pattern = re.compile(
                r"^(?P<current>\*|\s)\s+(?P<name>\S+)\s+(?P<hash>[a-f0-9]+)\s+(?:\[(?P<upstream>[^:\]]+)?(?::\s*(?P<tracking>[^\]]+))?\])?\s*(?P<msg>.*)$"
            )

            for line in res.stdout.splitlines():
                if not line.strip():
                    continue
                match = pattern.match(line)
                if not match:
                    continue

                is_curr = match.group("current") == "*"
                bname = match.group("name")
                chash = match.group("hash")
                upstream = match.group("upstream")
                track = match.group("tracking") or ""
                msg = match.group("msg") or ""

                ahead = 0
                behind = 0
                if "ahead" in track:
                    m_ahead = re.search(r"ahead\s+(\d+)", track)
                    if m_ahead:
                        ahead = int(m_ahead.group(1))
                if "behind" in track:
                    m_behind = re.search(r"behind\s+(\d+)", track)
                    if m_behind:
                        behind = int(m_behind.group(1))

                branches.append(
                    BranchInfo(
                        name=bname,
                        is_current=is_curr,
                        commit_hash=chash,
                        upstream=upstream,
                        ahead=ahead,
                        behind=behind,
                        commit_message=msg.strip()
                    )
                )
        except Exception:
            pass

        return branches

    @classmethod
    def format_status(cls, b: BranchInfo) -> str:
        if not b.upstream:
            return "[dim]Local only[/dim]"
        if b.ahead == 0 and b.behind == 0:
            return "[bold green]Up to date[/bold green]"
        parts = []
        if b.ahead > 0:
            parts.append(f"[bold yellow]{b.ahead} ahead[/bold yellow]")
        if b.behind > 0:
            parts.append(f"[bold red]{b.behind} behind[/bold red]")
        return ", ".join(parts)
