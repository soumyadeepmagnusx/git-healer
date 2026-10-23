from pathlib import Path
from githealer.bloat.analyzer import BloatAnalyzer

def test_scan_working_tree_empty(tmp_path):
    report = BloatAnalyzer.analyze(tmp_path, threshold_mb=1.0)
    assert report.total_bloat_mb == 0.0
    assert len(report.oversized_files) == 0
    assert "Repository is lean" in report.recommendations[0]

def test_scan_working_tree_with_oversized_file(tmp_path):
    heavy_file = tmp_path / "large_model.bin"
    # Write a 2MB dummy file
    heavy_file.write_bytes(b"0" * (2 * 1024 * 1024))

    report = BloatAnalyzer.analyze(tmp_path, threshold_mb=1.0)
    assert len(report.oversized_files) == 1
    assert report.oversized_files[0].path == "large_model.bin"
    assert report.oversized_files[0].size_mb >= 2.0
    assert report.total_bloat_mb >= 2.0
