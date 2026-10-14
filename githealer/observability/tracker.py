from __future__ import annotations

import json
import time
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Dict, List, Optional


@dataclass
class SessionMetrics:
    timestamp: str
    target_repo: str
    duration_seconds: float
    total_iterations: int
    triage_time_seconds: float = 0.0
    coder_time_seconds: float = 0.0
    sandbox_time_seconds: float = 0.0
    success: bool = False
    estimated_input_tokens: int = 0
    estimated_output_tokens: int = 0
    estimated_cost_usd: float = 0.0


class MetricsTracker:
    """Records performance, latency, and token estimates across self-healing sessions."""

    METRICS_FILE = ".githealer_metrics.json"

    @classmethod
    def record_session(cls, metrics: SessionMetrics, repo_path: str | Path):
        root = Path(repo_path).resolve()
        file_path = root / cls.METRICS_FILE

        records: List[Dict] = []
        if file_path.is_file():
            try:
                records = json.loads(file_path.read_text(encoding="utf-8"))
            except Exception:
                records = []

        records.append(asdict(metrics))
        file_path.write_text(json.dumps(records, indent=2), encoding="utf-8")

    @classmethod
    def get_summary(cls, repo_path: str | Path) -> Dict:
        root = Path(repo_path).resolve()
        file_path = root / cls.METRICS_FILE

        if not file_path.is_file():
            return {
                "total_runs": 0,
                "successful_runs": 0,
                "success_rate": 0.0,
                "avg_duration": 0.0,
                "total_cost_usd": 0.0
            }

        try:
            records = json.loads(file_path.read_text(encoding="utf-8"))
        except Exception:
            records = []

        if not records:
            return {
                "total_runs": 0,
                "successful_runs": 0,
                "success_rate": 0.0,
                "avg_duration": 0.0,
                "total_cost_usd": 0.0
            }

        total = len(records)
        successes = sum(1 for r in records if r.get("success"))
        durations = [r.get("duration_seconds", 0) for r in records]
        costs = [r.get("estimated_cost_usd", 0) for r in records]

        return {
            "total_runs": total,
            "successful_runs": successes,
            "success_rate": round((successes / total) * 100, 1),
            "avg_duration": round(sum(durations) / total, 2),
            "total_cost_usd": round(sum(costs), 5)
        }
