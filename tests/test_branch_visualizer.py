from githealer.branch.visualizer import BranchVisualizer, BranchInfo

def test_format_branch_status():
    b_local = BranchInfo(name="feature", is_current=False, commit_hash="1234567")
    assert "Local only" in BranchVisualizer.format_status(b_local)

    b_synced = BranchInfo(name="main", is_current=True, commit_hash="1234567", upstream="origin/main")
    assert "Up to date" in BranchVisualizer.format_status(b_synced)

    b_ahead = BranchInfo(name="dev", is_current=False, commit_hash="1234567", upstream="origin/dev", ahead=2)
    assert "2 ahead" in BranchVisualizer.format_status(b_ahead)

    b_behind = BranchInfo(name="dev", is_current=False, commit_hash="1234567", upstream="origin/dev", behind=3)
    assert "3 behind" in BranchVisualizer.format_status(b_behind)

def test_get_branches_in_current_repo():
    branches = BranchVisualizer.get_branches(".")
    assert len(branches) >= 1
    assert any(b.name == "main" for b in branches)
    assert any(b.is_current for b in branches)
