from __future__ import annotations

import os
import stat
from pathlib import Path
from typing import Dict, List, Optional, Tuple

PRE_COMMIT_SCRIPT = """#!/usr/bin/env sh
# GitHealer Automated Pre-Commit Security & Syntax Gatekeeper

echo "[GitHealer] Running pre-commit security checks..."

# Check for staged secrets or .env files
if git diff --cached --name-only | grep -E '(\\.env|id_rsa|id_ed25519|\\.pem|\\.key)$' > /dev/null 2>&1; then
    echo "\\033[1;31m[GitHealer BLOCKED]\\033[0m Sensitive credential or .env file detected in staged files!"
    echo "Remove it from staging using: git rm --cached <file>"
    exit 1
fi

echo "[GitHealer] Pre-commit checks passed successfully."
exit 0
"""

COMMIT_MSG_SCRIPT = """#!/usr/bin/env sh
# [GitHealer] Conventional Commit Validator Hook

MSG_FILE="$1"
FIRST_LINE=$(head -n 1 "$MSG_FILE")

# Check if first line matches conventional commits regex
if ! echo "$FIRST_LINE" | grep -Eq '^(feat|fix|docs|style|refactor|perf|test|build|ci|chore|revert)(\\([a-zA-Z0-9_\\-\\./]+\\))?!?: .+'; then
    echo "\\033[1;33m[GitHealer Warning]\\033[0m Commit message does not strictly follow Conventional Commits format: <type>(<scope>): <subject>"
    echo "Example: feat(api): add new authentication endpoint"
fi

exit 0
"""


class HookManager:
    """Installs, manages, and audits Git pre-commit and commit-msg hooks."""

    @classmethod
    def get_hooks_dir(cls, repo_path: str | Path = ".") -> Optional[Path]:
        root = Path(repo_path).resolve()
        hooks_dir = root / ".git" / "hooks"
        return hooks_dir if hooks_dir.is_dir() else None

    @classmethod
    def install(cls, repo_path: str | Path = ".") -> Tuple[bool, str]:
        hooks_dir = cls.get_hooks_dir(repo_path)
        if not hooks_dir:
            return False, "Not a valid Git repository root (.git/hooks directory not found)."

        # 1. Install pre-commit hook
        pre_commit_file = hooks_dir / "pre-commit"
        pre_commit_file.write_text(PRE_COMMIT_SCRIPT, encoding="utf-8")
        # Ensure executable permissions on Unix/macOS
        try:
            pre_commit_file.chmod(pre_commit_file.stat().st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)
        except Exception:
            pass

        # 2. Install commit-msg hook
        commit_msg_file = hooks_dir / "commit-msg"
        commit_msg_file.write_text(COMMIT_MSG_SCRIPT, encoding="utf-8")
        try:
            commit_msg_file.chmod(commit_msg_file.stat().st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)
        except Exception:
            pass

        return True, "Successfully installed GitHealer pre-commit and commit-msg hooks!"

    @classmethod
    def status(cls, repo_path: str | Path = ".") -> Dict[str, bool]:
        hooks_dir = cls.get_hooks_dir(repo_path)
        if not hooks_dir:
            return {"pre_commit": False, "commit_msg": False}

        pre_c = hooks_dir / "pre-commit"
        com_m = hooks_dir / "commit-msg"

        return {
            "pre_commit": pre_c.is_file() and "[GitHealer]" in pre_c.read_text(encoding="utf-8", errors="ignore"),
            "commit_msg": com_m.is_file() and "[GitHealer]" in com_m.read_text(encoding="utf-8", errors="ignore"),
        }

    @classmethod
    def uninstall(cls, repo_path: str | Path = ".") -> Tuple[bool, str]:
        hooks_dir = cls.get_hooks_dir(repo_path)
        if not hooks_dir:
            return False, "Not a valid Git repository root."

        for hook_name in ["pre-commit", "commit-msg"]:
            target = hooks_dir / hook_name
            if target.is_file() and "[GitHealer]" in target.read_text(encoding="utf-8", errors="ignore"):
                target.unlink()

        return True, "Successfully uninstalled GitHealer git hooks."
