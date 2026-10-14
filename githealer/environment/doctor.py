from __future__ import annotations

import os
import sys
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Tuple


class EnvironmentDoctor:
    """Diagnoses environment issues, missing dependencies, and package manager configurations."""

    @staticmethod
    def detect_ecosystem(repo_path: str | Path) -> Dict[str, bool]:
        root = Path(repo_path)
        return {
            "python": (root / "requirements.txt").exists() or (root / "pyproject.toml").exists() or (root / "setup.py").exists(),
            "node": (root / "package.json").exists(),
            "rust": (root / "Cargo.toml").exists(),
            "go": (root / "go.mod").exists() or any(root.glob("*.go")),
        }

    @staticmethod
    def diagnose_missing_dependencies(log_content: str) -> List[Tuple[str, str]]:
        """Extract missing packages from error logs (e.g. ModuleNotFoundError, Cannot find module)."""
        import re
        missing = []

        # Python: ModuleNotFoundError: No module named 'xyz'
        py_matches = re.findall(r"ModuleNotFoundError:\s+No module named\s+['\"]([^'\"]+)['\"]", log_content)
        for pkg in py_matches:
            missing.append(("python", pkg))

        # Python: ImportError: cannot import name 'xyz'
        py_import = re.findall(r"ImportError:\s+cannot import name\s+['\"]([^'\"]+)['\"]", log_content)
        for pkg in py_import:
            missing.append(("python_import", pkg))

        # Node: Cannot find module 'xyz'
        node_matches = re.findall(r"Cannot find module\s+['\"]([^'\"]+)['\"]", log_content)
        for pkg in node_matches:
            missing.append(("node", pkg))

        return list(dict.fromkeys(missing))

    @staticmethod
    def suggest_remediation(missing_deps: List[Tuple[str, str]]) -> List[str]:
        suggestions = []
        for ecosystem, pkg in missing_deps:
            if ecosystem == "python":
                suggestions.append(f"pip install {pkg}")
            elif ecosystem == "node":
                suggestions.append(f"npm install --save-dev {pkg}")
        return suggestions
