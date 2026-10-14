import sys
from pathlib import Path
from githealer.config import GitHealerConfig
from githealer.orchestrator import GitHealerOrchestrator

def test_end_to_end_self_healing(tmp_path):
    # Setup mini project with intentional bug
    calc_file = tmp_path / "calculator.py"
    calc_file.write_text("""def divide(a, b):
    return a / b
""", encoding="utf-8")

    test_file = tmp_path / "test_calculator.py"
    test_file.write_text("""import pytest
from calculator import divide

def test_divide_zero():
    with pytest.raises(ValueError):
        divide(10, 0)
""", encoding="utf-8")

    cfg = GitHealerConfig(
        test_command=f'"{sys.executable}" -m pytest',
        max_retries=2,
        sandbox_timeout_seconds=30
    )
    orchestrator = GitHealerOrchestrator(cfg)
    report = orchestrator.heal(repo_path=tmp_path, test_command=cfg.test_command)

    assert report.success is True
    assert len(report.patches) >= 1
    assert "raise ValueError" in (tmp_path / "calculator.py").read_text(encoding="utf-8")
