from pathlib import Path
from githealer.scoring.health_score import HealthScoreCalculator

def test_calculate_health_score(tmp_path):
    # Setup mock repo
    (tmp_path / ".gitignore").write_text(".venv/\n*.pyc\n", encoding="utf-8")
    (tmp_path / "pyproject.toml").write_text('[project]\nname="test"\n', encoding="utf-8")
    tests_dir = tmp_path / "tests"
    tests_dir.mkdir()
    (tests_dir / "test_sample.py").write_text("def test_ok(): pass\n", encoding="utf-8")

    score = HealthScoreCalculator.calculate(tmp_path)
    assert score.overall_score > 0
    assert score.grade in ["A+", "A", "B", "C", "D"]
    assert len(score.categories) == 4
    assert "[![GitHealer Score]" in score.badge_markdown
