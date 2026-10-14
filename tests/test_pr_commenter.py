from pathlib import Path
from githealer.github.pr_commenter import PRCommentBot

def test_format_quick_comment(tmp_path):
    report_file = tmp_path / "githealer-report.md"
    report_file.write_text("# Test Diagnosis\nAll tests passed.", encoding="utf-8")

    comment = PRCommentBot.format_quick_comment(report_file)
    assert "### 🩺 GitHealer CI Analysis & Patch Proposal" in comment
    assert "# Test Diagnosis" in comment
    assert "All tests passed." in comment
