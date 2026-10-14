import sys
from pathlib import Path
from githealer.sandbox.runner import SandboxRunner

def test_sandbox_runner_success(tmp_path):
    runner = SandboxRunner(working_dir=tmp_path)
    res = runner.run(f'"{sys.executable}" -c "print(1 + 1)"')
    assert res.success is True
    assert res.exit_code == 0
    assert "2" in res.stdout

def test_sandbox_runner_failure(tmp_path):
    runner = SandboxRunner(working_dir=tmp_path)
    res = runner.run(f'"{sys.executable}" -c "import sys; sys.exit(42)"')
    assert res.success is False
    assert res.exit_code == 42
