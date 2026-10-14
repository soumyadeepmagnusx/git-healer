from pathlib import Path
from githealer.safety.checkpoint import CheckpointManager

def test_checkpoint_and_rollback(tmp_path):
    f = tmp_path / "hello.py"
    f.write_text("print('version 1')", encoding="utf-8")

    # Create checkpoint
    chk_id = CheckpointManager.create_checkpoint(tmp_path, label="v1")
    assert chk_id.startswith("chk_")

    # Modify file
    f.write_text("print('version 2')", encoding="utf-8")
    assert f.read_text(encoding="utf-8") == "print('version 2')"

    # Rollback
    success = CheckpointManager.rollback(tmp_path, chk_id)
    assert success is True
    assert f.read_text(encoding="utf-8") == "print('version 1')"
