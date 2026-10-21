from pathlib import Path
from githealer.gitignore.generator import GitignoreGenerator

def test_detect_python_ecosystem(tmp_path):
    (tmp_path / "main.py").write_text("print('hello')", encoding="utf-8")
    ecos = GitignoreGenerator.detect_ecosystems(tmp_path)
    assert "python" in ecos
    assert "security" in ecos

def test_generate_gitignore_content(tmp_path):
    content = GitignoreGenerator.generate(tmp_path, custom_sections=["python", "security"])
    assert "__pycache__/" in content
    assert ".env" in content
    assert ".venv/" in content

def test_audit_missing_gitignore(tmp_path):
    is_ok, issues = GitignoreGenerator.audit_existing(tmp_path)
    assert is_ok is False
    assert any("Missing .gitignore file" in i for i in issues)

def test_audit_and_apply_missing_rules(tmp_path):
    gi = tmp_path / ".gitignore"
    gi.write_text(".venv/\n", encoding="utf-8")
    
    is_ok, missing = GitignoreGenerator.audit_existing(tmp_path)
    assert is_ok is False
    assert any(".env" in m for m in missing)

    applied = GitignoreGenerator.apply_to_repo(tmp_path, append_missing=True)
    assert applied is True
    updated_content = gi.read_text(encoding="utf-8")
    assert ".env" in updated_content
