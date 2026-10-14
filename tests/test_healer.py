import healer

def test_run_git_status():
    output = healer.run_git(["status"])
    assert not output.startswith("Error: Could not find")
    assert "On branch" in output or "fatal:" in output or len(output) > 0

def test_run_git_version():
    output = healer.run_git(["version"])
    assert "git version" in output
