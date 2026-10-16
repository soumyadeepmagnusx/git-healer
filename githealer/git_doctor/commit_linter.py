from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List, Optional, Tuple


CONVENTIONAL_TYPES = {
    "feat": "A new feature",
    "fix": "A bug fix",
    "docs": "Documentation only changes",
    "style": "Changes that do not affect the meaning of the code (white-space, formatting, etc)",
    "refactor": "A code change that neither fixes a bug nor adds a feature",
    "perf": "A code change that improves performance",
    "test": "Adding missing tests or correcting existing tests",
    "build": "Changes that affect the build system or external dependencies",
    "ci": "Changes to our CI configuration files and scripts",
    "chore": "Other changes that don't modify src or test files",
    "revert": "Reverts a previous commit",
}

CONVENTIONAL_PATTERN = re.compile(
    r"^(?P<type>feat|fix|docs|style|refactor|perf|test|build|ci|chore|revert)"
    r"(?:\((?P<scope>[a-zA-Z0-9_\-\.\/]+)\))?"
    r"(?P<breaking>!)?:\s+(?P<subject>.+)$"
)

VAGUE_PATTERNS = [
    r"^(?:update|updates|updated)\.?$",
    r"^(?:fix|fixes|fixed)\.?$",
    r"^(?:bugfix|bug fixes)\.?$",
    r"^(?:wip|work in progress)\.?$",
    r"^(?:changes|made changes)\.?$",
    r"^(?:minor changes|misc)\.?$",
    r"^(?:asdf|test|commit)\.?$",
]


@dataclass
class CommitLintResult:
    message: str
    is_valid: bool
    commit_type: Optional[str] = None
    scope: Optional[str] = None
    is_breaking: bool = False
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    suggestion: Optional[str] = None


class CommitDoctor:
    """Lints commit messages against Conventional Commits specs and detects vague messages."""

    @classmethod
    def lint(cls, message: str) -> CommitLintResult:
        trimmed = message.strip()
        lines = trimmed.splitlines()
        header = lines[0] if lines else ""

        errors: List[str] = []
        warnings: List[str] = []

        if not header:
            return CommitLintResult(message=message, is_valid=False, errors=["Commit message cannot be empty."])

        # Check for vague messages
        for vp in VAGUE_PATTERNS:
            if re.match(vp, header, re.IGNORECASE):
                errors.append(f"Vague commit message detected: '{header}'. Please provide descriptive context.")
                break

        # Check header length
        if len(header) > 72:
            warnings.append(f"Header length ({len(header)}) exceeds recommended 72 characters.")

        match = CONVENTIONAL_PATTERN.match(header)
        if not match:
            errors.append(
                "Header does not follow Conventional Commits format: `<type>(<scope>): <subject>`.\n"
                f"Valid types: {', '.join(CONVENTIONAL_TYPES.keys())}"
            )
            # Suggest a fix
            guessed_type = "chore"
            header_lower = header.lower()
            if any(k in header_lower for k in ["fix", "bug", "patch", "resolve", "error", "issue"]):
                guessed_type = "fix"
            elif any(k in header_lower for k in ["add", "feature", "new", "create"]):
                guessed_type = "feat"
            elif any(k in header_lower for k in ["doc", "readme", "comment"]):
                guessed_type = "docs"
            elif any(k in header_lower for k in ["test", "spec", "pytest"]):
                guessed_type = "test"
            elif any(k in header_lower for k in ["refactor", "cleanup", "clean", "rewrite"]):
                guessed_type = "refactor"

            clean_subj = re.sub(r"^(?:feat|fix|test|chore|docs|refactor)[\s\:\-]+", "", header, flags=re.IGNORECASE).strip()
            clean_subj = clean_subj[0].lower() + clean_subj[1:] if clean_subj else "update code"
            suggestion = f"{guessed_type}: {clean_subj}"

            return CommitLintResult(
                message=message,
                is_valid=False,
                errors=errors,
                warnings=warnings,
                suggestion=suggestion
            )

        ctype = match.group("type")
        scope = match.group("scope")
        breaking = bool(match.group("breaking"))
        subject = match.group("subject").strip()

        # Subject rules
        if subject.endswith("."):
            warnings.append("Subject line should not end with a period.")
        if subject and subject[0].isupper():
            warnings.append("Subject should preferably start in lowercase imperative mood (e.g. 'add feature' not 'Add feature').")

        return CommitLintResult(
            message=message,
            is_valid=(len(errors) == 0),
            commit_type=ctype,
            scope=scope,
            is_breaking=breaking,
            errors=errors,
            warnings=warnings
        )

    @classmethod
    def generate_conventional_message(cls, diff: str) -> str:
        """Heuristically infers a clean conventional commit message from a git diff."""
        lines = diff.splitlines()
        added_files = [l[6:] for l in lines if l.startswith("+++ b/")]

        if not added_files:
            return "chore: update workspace files"

        # Check types of files changed
        if all("test" in f.lower() for f in added_files):
            return "test: update unit and integration test suite"
        if all(f.lower().endswith(".md") or "doc" in f.lower() for f in added_files):
            return "docs: update documentation and usage guides"
        if any("fix" in l.lower() or "error" in l.lower() or "bug" in l.lower() for l in lines[:100]):
            primary = Path(added_files[0]).stem
            return f"fix({primary}): resolve issues and prevent runtime errors"
        
        primary = Path(added_files[0]).stem
        return f"feat({primary}): implement new functionality and enhancements"
