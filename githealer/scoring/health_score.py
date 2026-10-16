from __future__ import annotations

import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Tuple
from githealer.git_doctor.commit_linter import CommitDoctor


@dataclass
class HealthCategory:
    name: str
    score: int
    max_score: int
    feedback: List[str] = field(default_factory=list)


@dataclass
class RepoHealthScore:
    overall_score: int  # 0 to 100
    grade: str          # A+, A, B, C, D, F
    categories: List[HealthCategory] = field(default_factory=list)

    @property
    def badge_markdown(self) -> str:
        color = "brightgreen" if self.overall_score >= 85 else ("yellow" if self.overall_score >= 70 else "red")
        return f"[![GitHealer Score](https://img.shields.io/badge/Health%20Score-{self.overall_score}%2F100%20({self.grade})-{color}?style=flat-square)](https://github.com/soumyadeepmagnusx/git-healer)"


class HealthScoreCalculator:
    """Evaluates comprehensive repository health and generates a graded score card."""

    @classmethod
    def calculate(cls, repo_path: str | Path = ".") -> RepoHealthScore:
        root = Path(repo_path).resolve()

        # 1. Git Hygiene (25 pts)
        git_score = 25
        git_feedback = []
        try:
            head_out = subprocess.run(["git", "symbolic-ref", "-q", "HEAD"], cwd=str(root), capture_output=True, text=True)
            if head_out.returncode != 0:
                git_score -= 10
                git_feedback.append("Detached HEAD state detected (-10)")
        except Exception:
            git_score -= 5

        try:
            status_out = subprocess.run(["git", "status", "--porcelain"], cwd=str(root), capture_output=True, text=True)
            uncommitted = [l for l in status_out.stdout.splitlines() if l.strip()]
            if len(uncommitted) > 10:
                git_score -= 5
                git_feedback.append(f"{len(uncommitted)} uncommitted files (-5)")
        except Exception:
            pass

        try:
            branch_out = subprocess.run(["git", "branch", "--merged"], cwd=str(root), capture_output=True, text=True)
            merged = [b.strip() for b in branch_out.stdout.splitlines() if b.strip() and not b.startswith("*") and b.strip() not in ["main", "master", "develop"]]
            if len(merged) > 3:
                git_score -= 5
                git_feedback.append(f"{len(merged)} stale merged branches (-5)")
        except Exception:
            pass

        cat_git = HealthCategory("Git Hygiene", max(0, git_score), 25, git_feedback or ["Clean branches and working tree"])

        # 2. CI/CD & Testing (25 pts)
        ci_score = 0
        ci_feedback = []
        if (root / ".github" / "workflows").is_dir() and any((root / ".github" / "workflows").glob("*.yml")):
            ci_score += 10
            ci_feedback.append("GitHub Actions CI workflow configured (+10)")
        else:
            ci_feedback.append("Missing .github/workflows CI pipeline (0/10)")

        if (root / "tests").is_dir() and any((root / "tests").glob("test_*.py")):
            ci_score += 10
            ci_feedback.append("Automated test suite detected (+10)")
        else:
            ci_feedback.append("No tests/ directory with test files found (0/10)")

        if (root / "pyproject.toml").is_file() or (root / "package.json").is_file():
            ci_score += 5
            ci_feedback.append("Standard project packaging configuration found (+5)")

        cat_ci = HealthCategory("CI/CD & Testing", ci_score, 25, ci_feedback)

        # 3. Security & Credentials (25 pts)
        sec_score = 25
        sec_feedback = []
        if not (root / ".gitignore").is_file():
            sec_score -= 10
            sec_feedback.append("Missing .gitignore file (-10)")

        for env_f in root.glob("**/.env*"):
            if ".git" not in env_f.parts and ".venv" not in env_f.parts:
                sec_score -= 10
                sec_feedback.append(f"Exposed env file: {env_f.name} (-10)")
                break

        cat_sec = HealthCategory("Security & Hygiene", max(0, sec_score), 25, sec_feedback or ["No exposed credentials, valid .gitignore"])

        # 4. Commit Quality (25 pts)
        commit_score = 25
        commit_feedback = []
        try:
            log_out = subprocess.run(["git", "log", "-5", "--pretty=%B"], cwd=str(root), capture_output=True, text=True)
            raw_commits = [c.strip() for c in log_out.stdout.split("\n\n") if c.strip()]
            if raw_commits:
                valid_count = sum(1 for c in raw_commits if CommitDoctor.lint(c).is_valid)
                ratio = valid_count / len(raw_commits)
                commit_score = int(25 * ratio)
                commit_feedback.append(f"{valid_count}/{len(raw_commits)} recent commits follow Conventional Commits")
        except Exception:
            commit_score = 20

        cat_commits = HealthCategory("Commit Quality", max(0, commit_score), 25, commit_feedback or ["Commit messages are clean"])

        total = cat_git.score + cat_ci.score + cat_sec.score + cat_commits.score
        if total >= 92:
            grade = "A+"
        elif total >= 85:
            grade = "A"
        elif total >= 75:
            grade = "B"
        elif total >= 65:
            grade = "C"
        else:
            grade = "D"

        return RepoHealthScore(
            overall_score=total,
            grade=grade,
            categories=[cat_git, cat_ci, cat_sec, cat_commits]
        )
