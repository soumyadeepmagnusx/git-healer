from __future__ import annotations

import json
import shutil
import time
from pathlib import Path
from typing import Dict, List, Optional


class CheckpointManager:
    """Manages working directory snapshots and safe rollbacks."""

    CHECKPOINT_DIR = ".githealer_checkpoints"

    @classmethod
    def create_checkpoint(cls, repo_path: str | Path, label: str = "pre-heal") -> str:
        """Saves current state of all files in the repository."""
        root = Path(repo_path).resolve()
        storage = root / cls.CHECKPOINT_DIR
        storage.mkdir(parents=True, exist_ok=True)

        checkpoint_id = f"chk_{int(time.time())}_{label}"
        chk_folder = storage / checkpoint_id
        chk_folder.mkdir(parents=True, exist_ok=True)

        snapshot: Dict[str, str] = {}
        for p in root.rglob("*"):
            if not p.is_file():
                continue
            # Ignore git, venv, and checkpoints dir
            rel = p.relative_to(root)
            parts = rel.parts
            if any(part in [".git", ".venv", "venv", "__pycache__", cls.CHECKPOINT_DIR] for part in parts):
                continue
            try:
                snapshot[str(rel).replace("\\", "/")] = p.read_text(encoding="utf-8", errors="replace")
            except Exception:
                pass

        meta_file = chk_folder / "metadata.json"
        meta_file.write_text(json.dumps({
            "id": checkpoint_id,
            "label": label,
            "created_at": time.ctime(),
            "files_count": len(snapshot)
        }, indent=2), encoding="utf-8")

        data_file = chk_folder / "snapshot.json"
        data_file.write_text(json.dumps(snapshot), encoding="utf-8")

        return checkpoint_id

    @classmethod
    def rollback(cls, repo_path: str | Path, checkpoint_id: Optional[str] = None) -> bool:
        """Restores repository files from the specified or latest checkpoint."""
        root = Path(repo_path).resolve()
        storage = root / cls.CHECKPOINT_DIR
        if not storage.is_dir():
            return False

        if not checkpoint_id:
            # Find latest checkpoint
            checkpoints = sorted([d for d in storage.iterdir() if d.is_dir()], key=lambda d: d.stat().st_mtime, reverse=True)
            if not checkpoints:
                return False
            target_chk = checkpoints[0]
        else:
            target_chk = storage / checkpoint_id
            if not target_chk.is_dir():
                return False

        data_file = target_chk / "snapshot.json"
        if not data_file.is_file():
            return False

        snapshot: Dict[str, str] = json.loads(data_file.read_text(encoding="utf-8"))
        for rel_path, content in snapshot.items():
            dest = root / rel_path
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text(content, encoding="utf-8")

        return True

    @classmethod
    def list_checkpoints(cls, repo_path: str | Path) -> List[Dict[str, str]]:
        root = Path(repo_path).resolve()
        storage = root / cls.CHECKPOINT_DIR
        if not storage.is_dir():
            return []

        results = []
        for d in sorted(storage.iterdir(), key=lambda x: x.stat().st_mtime, reverse=True):
            if d.is_dir() and (d / "metadata.json").is_file():
                try:
                    meta = json.loads((d / "metadata.json").read_text(encoding="utf-8"))
                    results.append(meta)
                except Exception:
                    pass
        return results
