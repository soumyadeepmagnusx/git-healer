from githealer.git_doctor.commit_linter import CommitDoctor

def test_valid_conventional_commit():
    res = CommitDoctor.lint("feat(parser): add support for Go test logs")
    assert res.is_valid is True
    assert res.commit_type == "feat"
    assert res.scope == "parser"
    assert len(res.errors) == 0

def test_invalid_vague_commit():
    res = CommitDoctor.lint("wip")
    assert res.is_valid is False
    assert any("Vague commit message" in e for e in res.errors)

def test_missing_type_suggestion():
    res = CommitDoctor.lint("Fixed the broken login error on auth page")
    assert res.is_valid is False
    assert res.suggestion is not None
    assert res.suggestion.startswith("fix:")

def test_generate_from_test_diff():
    diff = """
--- a/tests/test_core.py
+++ b/tests/test_core.py
@@ -1,3 +1,4 @@
+def test_new(): pass
"""
    msg = CommitDoctor.generate_conventional_message(diff)
    assert msg.startswith("test:")
