from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Set, Tuple

TEMPLATES: Dict[str, List[str]] = {
    "python": [
        "__pycache__/",
        "*.py[cod]",
        "*$py.class",
        "*.so",
        ".Python",
        "build/",
        "develop-eggs/",
        "dist/",
        "downloads/",
        "eggs/",
        ".eggs/",
        "lib/",
        "lib64/",
        "parts/",
        "sdist/",
        "var/",
        "wheels/",
        "*.egg-info/",
        ".installed.cfg",
        "*.egg",
        ".venv/",
        "venv/",
        "ENV/",
        ".pytest_cache/",
        ".coverage",
        "htmlcov/",
        ".tox/",
        ".nox/",
        "coverage.xml",
    ],
    "node": [
        "node_modules/",
        "npm-debug.log*",
        "yarn-debug.log*",
        "yarn-error.log*",
        "lerna-debug.log*",
        ".pnpm-debug.log*",
        "dist/",
        ".next/",
        ".nuxt/",
        ".turbo/",
        "build/",
        ".env*.local",
    ],
    "rust": [
        "/target/",
        "**/*.rs.bk",
        "Cargo.lock",
    ],
    "go": [
        "bin/",
        "pkg/",
        "*.exe",
        "*.test",
        "*.out",
    ],
    "security": [
        ".env",
        ".env.local",
        ".env.production",
        "*.pem",
        "*.key",
        "id_rsa",
        "id_ed25519",
        "*.p12",
        "*.pfx",
    ],
    "ide_os": [
        ".vscode/",
        ".idea/",
        "*.swp",
        "*.swo",
        ".DS_Store",
        "Thumbs.db",
        "*.bak",
    ],
}


class GitignoreGenerator:
    """Smart engine to detect languages, generate tailored .gitignore files, and audit security."""

    @classmethod
    def detect_ecosystems(cls, repo_path: str | Path = ".") -> List[str]:
        root = Path(repo_path).resolve()
        detected = ["security", "ide_os"]

        if any(root.glob("*.py")) or (root / "requirements.txt").exists() or (root / "pyproject.toml").exists():
            detected.append("python")
        if (root / "package.json").exists() or (root / "node_modules").exists():
            detected.append("node")
        if (root / "Cargo.toml").exists():
            detected.append("rust")
        if (root / "go.mod").exists() or any(root.glob("*.go")):
            detected.append("go")

        return detected

    @classmethod
    def generate(cls, repo_path: str | Path = ".", custom_sections: List[str] | None = None) -> str:
        sections = custom_sections or cls.detect_ecosystems(repo_path)
        blocks = []

        for sec in sections:
            rules = TEMPLATES.get(sec, [])
            if rules:
                header = f"# ==========================================\n# {sec.upper()} Rules\n# =========================================="
                blocks.append(f"{header}\n" + "\n".join(rules))

        return "\n\n".join(blocks) + "\n"

    @classmethod
    def audit_existing(cls, repo_path: str | Path = ".") -> Tuple[bool, List[str]]:
        """Checks existing .gitignore for critical missing security or build patterns."""
        root = Path(repo_path).resolve()
        gitignore_path = root / ".gitignore"

        if not gitignore_path.is_file():
            return False, ["Missing .gitignore file entirely."]

        content = gitignore_path.read_text(encoding="utf-8", errors="replace")
        lines = [line.strip() for line in content.splitlines() if line.strip() and not line.startswith("#")]
        existing_rules = set(lines)

        missing_critical = []
        critical_checks = [".env", "*.pem", "*.key", ".venv/", "__pycache__/"]
        for crit in critical_checks:
            if not any(crit in rule or rule in crit for rule in existing_rules):
                missing_critical.append(f"Missing critical rule: `{crit}`")

        return len(missing_critical) == 0, missing_critical

    @classmethod
    def apply_to_repo(cls, repo_path: str | Path = ".", append_missing: bool = True) -> bool:
        root = Path(repo_path).resolve()
        gitignore_path = root / ".gitignore"

        if not gitignore_path.exists():
            content = cls.generate(repo_path)
            gitignore_path.write_text(content, encoding="utf-8")
            return True

        if append_missing:
            _, missing = cls.audit_existing(repo_path)
            if missing:
                extra = "\n# Auto-added by GitHealer Security Audit\n" + "\n".join(
                    m.split("`")[1] for m in missing if "`" in m
                ) + "\n"
                with open(gitignore_path, "a", encoding="utf-8") as f:
                    f.write(extra)
                return True

        return False
