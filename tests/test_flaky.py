import sys
from pathlib import Path
from githealer.sandbox.runner import SandboxRunner
from githealer.flaky.detector import FlakyTestDetector

def test_flaky_detector_deterministic_pass(tmp_path):
    runner = SandboxRunner(working_dir=tmp_path)
    detector = FlakyTestDetector(runner)
    report = detector.analyze(f'"{sys.executable}" -c "print(1)"', runs=2)
    assert report.is_flaky is False
    assert report.passes == 2
    assert report.failures == 0

def test_flaky_detector_deterministic_failure(tmp_path):
    runner = SandboxRunner(working_dir=tmp_path)
    detector = FlakyTestDetector(runner)
    report = detector.analyze(f'"{sys.executable}" -c "import sys; sys.exit(1)"', runs=2)
    assert report.is_flaky is False
    assert report.failures == 2
