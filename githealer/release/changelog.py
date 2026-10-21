from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple


@dataclass
class ChangelogCategory:
    title: str
    items: List[str] = field(default_factory=list)


@dataclass
class ReleasePlan:
    current_version: str
    next_version: str
    bump_type: str  # major, minor, patch
    changelog_markdown: str


class ChangelogGenerator:
    """Parses Conventional Commits and generates automated Semantic Release changelogs."""

    @classmethod
    def get_commit_history(cls, repo_path: str | Path = ".", limit: int = 50) -> List[str]:
        root = Path(repo_path).resolve()
        try:
            res = subprocess.run(
                ["git", "log", f"-{limit}", "--pretty=%s"],
                cwd=str(root),
                capture_output=True,
                text=True,
                check=True,
                encoding="utf-8",
                errors="replace"
            )
            return [line.strip() for line in res.stdout.splitlines() if line.strip()]
        except Exception:
            return []

    @classmethod
    def parse_commits(cls, commits: List[str]) -> Tuple[Dict[str, List[str]], str]:
        """Categorize commits and determine the required SemVer bump."""
        categories: Dict[str, List[str]] = {
            "Features": [],
            "Bug Fixes": [],
            "Performance": [],
            "Documentation": [],
            "Refactoring": [],
            "Chore & Maintenance": [],
        }

        has_breaking = False
        has_feature = False

        pattern = re.compile(
            r"^(?P<type>feat|fix|docs|style|refactor|perf|test|build|ci|chore|revert)"
            r"(?:\((?P<scope>[^)]+)\))?"
            r"(?P<breaking>!)?:\s+(?P<subject>.+)$"
        )

        for c in commits:
            match = pattern.match(c)
            if not match:
                categories["Chore & Maintenance"].append(c)
                continue

            ctype = match.group("type")
            scope = match.group("scope")
            is_break = bool(match.group("breaking"))
            subj = match.group("subject").strip()
            item = f"**{scope}**: {subj}" if scope else subj

            if is_break:
                has_breaking = True
                item = f"💥 **BREAKING:** {item}"

            if ctype == "feat":
                has_feature = True
                categories["Features"].append(item)
            elif ctype == "fix":
                categories["Bug Fixes"].append(item)
            elif ctype == "perf":
                categories["Performance"].append(item)
            elif ctype == "docs":
                categories["Documentation"].append(item)
            elif ctype == "refactor":
                categories["Refactoring"].append(item)
            else:
                categories["Chore & Maintenance"].append(item)

        if has_breaking:
            bump_type = "major"
        elif has_feature:
            bump_type = "minor"
        else:
            bump_type = "patch"

        return categories, bump_type

    @classmethod
    def bump_semver(cls, version: str, bump_type: str) -> str:
        clean = version.lstrip("v").strip()
        parts = clean.split(".")
        if len(parts) < 3:
            parts = (parts + ["0", "0", "0"])[:3]

        major, minor, patch = int(parts[0]), int(parts[1]), int(parts[2])

        if bump_type == "major":
            return f"{major + 1}.0.0"
        elif bump_type == "minor":
            return f"{major}.{minor + 1}.0"
        else:
            return f"{major}.{minor}.{patch + 1}"

    @classmethod
    def generate_release(
        cls,
        repo_path: str | Path = ".",
        current_version: str = "1.0.0",
        commit_limit: int = 50
    ) -> ReleasePlan:
        commits = cls.get_commit_history(repo_path, limit=commit_limit)
        categories, bump = cls.parse_commits(commits)
        next_ver = cls.bump_semver(current_version, bump)
        date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")

        md_lines = [
            f"## [{next_ver}] - {date_str}",
            f"*Semantic Bump: `{bump.upper()}`*",
            ""
        ]

        icons = {
            "Features": "🚀",
            "Bug Fixes": "🐛",
            "Performance": "⚡",
            "Documentation": "📝",
            "Refactoring": "♻️",
            "Chore & Maintenance": "🔧",
        }

        for cat_name, items in categories.items():
            if items:
                icon = icons.get(cat_name, "•")
                md_lines.append(f"### {icon} {cat_name}")
                for it in items:
                    md_lines.append(f"- {it}")
                md_lines.append("")

        changelog_md = "\n".join(md_lines).strip()

        return ReleasePlan(
            current_version=current_version,
            next_version=next_ver,
            bump_type=bump,
            changelog_markdown=changelog_md
        )
