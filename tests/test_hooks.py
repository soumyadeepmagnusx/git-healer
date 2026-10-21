from pathlib import Path
from githealer.hooks.manager import HookManager

def test_hook_install_and_status(tmp_path):
    git_dir = tmp_path / ".git" / "hooks"
    git_dir.mkdir(parents=True)

    # Initial status
    status = HookManager.status(tmp_path)
    assert status["pre_commit"] is False
    assert status["commit_msg"] is False

    # Install
    ok, msg = HookManager.install(tmp_path)
    assert ok is True
    assert (git_dir / "pre-commit").is_file()
    assert (git_dir / "commit-msg").is_file()

    # Status after install
    status = HookManager.status(tmp_path)
    assert status["pre_commit"] is True
    assert status["commit_msg"] is True

    # Uninstall
    ok_un, msg_un = HookManager.uninstall(tmp_path)
    assert ok_un is True
    status = HookManager.status(tmp_path)
    assert status["pre_commit"] is False
