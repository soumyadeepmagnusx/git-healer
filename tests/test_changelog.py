from githealer.release.changelog import ChangelogGenerator

def test_parse_commits_categorization():
    commits = [
        "feat(api): add health check route",
        "fix(core): prevent zero division crash",
        "docs: update readme with quickstart",
        "perf(parser): speed up regex token matching",
        "chore: bump dependencies"
    ]
    categories, bump = ChangelogGenerator.parse_commits(commits)
    assert bump == "minor"
    assert len(categories["Features"]) == 1
    assert len(categories["Bug Fixes"]) == 1
    assert len(categories["Documentation"]) == 1
    assert len(categories["Performance"]) == 1

def test_breaking_change_bump():
    commits = [
        "feat(engine)!: rewrite core architecture",
        "fix: resolve null pointer"
    ]
    categories, bump = ChangelogGenerator.parse_commits(commits)
    assert bump == "major"
    assert any("BREAKING" in it for it in categories["Features"])

def test_semver_bumping():
    assert ChangelogGenerator.bump_semver("1.0.0", "patch") == "1.0.1"
    assert ChangelogGenerator.bump_semver("1.0.0", "minor") == "1.1.0"
    assert ChangelogGenerator.bump_semver("1.0.0", "major") == "2.0.0"

def test_generate_release_output(tmp_path):
    plan = ChangelogGenerator.generate_release(tmp_path, current_version="1.0.0")
    assert plan.current_version == "1.0.0"
    assert plan.next_version in ["1.0.1", "1.1.0", "2.0.0"]
    assert "## [" in plan.changelog_markdown
