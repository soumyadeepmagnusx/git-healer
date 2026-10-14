from githealer.environment.doctor import EnvironmentDoctor

def test_detect_ecosystems(tmp_path):
    (tmp_path / "requirements.txt").write_text("pytest\n", encoding="utf-8")
    ecosystems = EnvironmentDoctor.detect_ecosystem(tmp_path)
    assert ecosystems["python"] is True
    assert ecosystems["rust"] is False

def test_diagnose_missing_dependencies():
    log = """
Traceback (most recent call last):
  File "app.py", line 1, in <module>
    import fastapi
ModuleNotFoundError: No module named 'fastapi'
"""
    missing = EnvironmentDoctor.diagnose_missing_dependencies(log)
    assert len(missing) == 1
    assert missing[0] == ("python", "fastapi")

    remedy = EnvironmentDoctor.suggest_remediation(missing)
    assert remedy == ["pip install fastapi"]
