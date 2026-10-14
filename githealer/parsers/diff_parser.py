from __future__ import annotations

import difflib
import ast
from pathlib import Path
from typing import Optional, Tuple
from githealer.models import CodePatch


class DiffParser:
    """Handles unified diff generation, application, and syntax validation."""

    @staticmethod
    def generate_diff(original: str, modified: str, filename: str = "file") -> str:
        """Create standard unified diff."""
        orig_lines = original.splitlines(keepends=True)
        mod_lines = modified.splitlines(keepends=True)
        diff = difflib.unified_diff(
            orig_lines,
            mod_lines,
            fromfile=f"a/{filename}",
            tofile=f"b/{filename}"
        )
        return "".join(diff)

    @staticmethod
    def validate_syntax(code: str, file_path: str) -> Tuple[bool, Optional[str]]:
        """Validate syntax for known languages like Python, JSON, YAML."""
        ext = Path(file_path).suffix.lower()
        if ext == ".py":
            try:
                ast.parse(code)
                return True, None
            except SyntaxError as e:
                return False, f"SyntaxError in {file_path}:{e.lineno} - {e.msg}"
        elif ext == ".json":
            import json
            try:
                json.loads(code)
                return True, None
            except Exception as e:
                return False, f"Invalid JSON in {file_path}: {e}"
        # For other languages, treat as valid or let the sandbox test suite catch it
        return True, None

    @classmethod
    def create_patch(cls, file_path: str, original_code: str, patched_code: str, explanation: str = "") -> CodePatch:
        diff = cls.generate_diff(original_code, patched_code, filename=file_path)
        return CodePatch(
            file_path=file_path,
            original_code=original_code,
            patched_code=patched_code,
            diff=diff,
            explanation=explanation
        )
