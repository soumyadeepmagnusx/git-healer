from __future__ import annotations

import os
import yaml
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional, List


@dataclass
class GitHealerConfig:
    gemini_api_key: Optional[str] = None
    github_token: Optional[str] = None
    model_name: str = "gemini-2.5-flash"
    test_command: Optional[str] = None
    max_retries: int = 3
    sandbox_timeout_seconds: int = 60
    auto_create_pr: bool = False
    pr_base_branch: str = "main"
    git_executable: str = "git"
    allowed_file_extensions: List[str] = field(
        default_factory=lambda: [".py", ".js", ".ts", ".go", ".rs", ".java", ".json", ".yaml", ".yml"]
    )

    @classmethod
    def load(cls, config_path: Optional[str] = None, repo_root: Optional[str] = None) -> "GitHealerConfig":
        """Load configuration from .githealer.yaml or environment variables."""
        cfg = cls()

        # Check environment variables
        cfg.gemini_api_key = os.environ.get("GEMINI_API_KEY")
        cfg.github_token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
        cfg.model_name = os.environ.get("GITHEALER_MODEL", cfg.model_name)
        cfg.test_command = os.environ.get("GITHEALER_TEST_CMD")

        # Locate Git executable on Windows if not standard in PATH
        if os.name == "nt":
            standard_paths = [
                r"C:\Program Files\Git\cmd\git.exe",
                os.path.expandvars(r"%LOCALAPPDATA%\Programs\Git\cmd\git.exe")
            ]
            for p in standard_paths:
                if os.path.isfile(p):
                    cfg.git_executable = p
                    break

        # Check file config
        search_paths = []
        if config_path:
            search_paths.append(Path(config_path))
        if repo_root:
            search_paths.append(Path(repo_root) / ".githealer.yaml")
            search_paths.append(Path(repo_root) / ".githealer.yml")
        search_paths.append(Path(".githealer.yaml"))

        for p in search_paths:
            if p.is_file():
                try:
                    with open(p, "r", encoding="utf-8") as f:
                        data = yaml.safe_load(f) or {}
                        if "gemini_api_key" in data and not cfg.gemini_api_key:
                            cfg.gemini_api_key = data["gemini_api_key"]
                        if "github_token" in data and not cfg.github_token:
                            cfg.github_token = data["github_token"]
                        if "model" in data:
                            cfg.model_name = data["model"]
                        if "test_command" in data and not cfg.test_command:
                            cfg.test_command = data["test_command"]
                        if "max_retries" in data:
                            cfg.max_retries = int(data["max_retries"])
                        if "sandbox_timeout" in data:
                            cfg.sandbox_timeout_seconds = int(data["sandbox_timeout"])
                        if "auto_create_pr" in data:
                            cfg.auto_create_pr = bool(data["auto_create_pr"])
                except Exception:
                    pass
                break

        return cfg
