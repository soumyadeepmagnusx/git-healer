from __future__ import annotations

import os
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple


@dataclass
class BloatItem:
    path: str
    size_bytes: int
    size_mb: float
    is_tracked: bool = True
    object_hash: Optional[str] = None


@dataclass
class BloatReport:
    total_bloat_mb: float
    oversized_files: List[BloatItem]
    recommendations: List[str]


class BloatAnalyzer:
    """Detects heavy binary files, oversized datasets, and repository bloat."""

    @classmethod
    def scan_working_tree(cls, repo_path: str | Path = ".", threshold_mb: float = 5.0) -> List[BloatItem]:
        root = Path(repo_path).resolve()
        oversized = []
        threshold_bytes = int(threshold_mb * 1024 * 1024)

        for p in root.rglob("*"):
            if not p.is_file():
                continue
            rel = p.relative_to(root)
            if any(part in [".git", ".venv", "venv", "__pycache__", "node_modules"] for part in rel.parts):
                continue

            try:
                size = p.stat().st_size
                if size >= threshold_bytes:
                    oversized.append(
                        BloatItem(
                            path=str(rel).replace("\\", "/"),
                            size_bytes=size,
                            size_mb=round(size / (1024 * 1024), 2),
                            is_tracked=True
                        )
                    )
            except Exception:
                pass

        return sorted(oversized, key=lambda x: x.size_bytes, reverse=True)

    @classmethod
    def scan_git_history(cls, repo_path: str | Path = ".", top_n: int = 5) -> List[BloatItem]:
        """Inspects Git rev-list to find the largest historical blob objects."""
        root = Path(repo_path).resolve()
        try:
            # Query all git objects with their size and path
            cmd = ["git", "rev-list", "--objects", "--all"]
            res = subprocess.run(cmd, cwd=str(root), capture_output=True, text=True, check=True, encoding="utf-8", errors="replace")
            objects = [l.strip().split(maxsplit=1) for l in res.stdout.splitlines() if len(l.strip().split(maxsplit=1)) == 2]

            bloat_items = []
            for obj_hash, obj_path in objects[:100]:
                cat_cmd = ["git", "cat-file", "-s", obj_hash]
                cat_res = subprocess.run(cat_cmd, cwd=str(root), capture_output=True, text=True, check=True)
                size = int(cat_res.stdout.strip())
                if size >= 1024 * 1024:  # >= 1MB
                    bloat_items.append(
                        BloatItem(
                            path=obj_path,
                            size_bytes=size,
                            size_mb=round(size / (1024 * 1024), 2),
                            object_hash=obj_hash
                        )
                    )

            bloat_items.sort(key=lambda x: x.size_bytes, reverse=True)
            return bloat_items[:top_n]
        except Exception:
            return []

    @classmethod
    def analyze(cls, repo_path: str | Path = ".", threshold_mb: float = 5.0) -> BloatReport:
        items = cls.scan_working_tree(repo_path, threshold_mb=threshold_mb)
        total_mb = sum(i.size_mb for i in items)

        recs = []
        if items:
            recs.append("Add detected large files to `.gitignore` to prevent further repository growth.")
            recs.append("Consider migrating heavy media or dataset files to Git Large File Storage (Git LFS).")
            recs.append("Use `git filter-repo` or BFG Repo-Cleaner if these files were accidentally committed.")
        else:
            recs.append("Repository is lean and free of oversized files.")

        return BloatReport(
            total_bloat_mb=round(total_mb, 2),
            oversized_files=items,
            recommendations=recs
        )
