from githealer.observability.tracker import MetricsTracker, SessionMetrics

def test_record_and_summarize_metrics(tmp_path):
    m1 = SessionMetrics(
        timestamp="2026-10-14T10:00:00",
        target_repo="my-app",
        duration_seconds=1.5,
        total_iterations=1,
        success=True,
        estimated_cost_usd=0.0002
    )
    m2 = SessionMetrics(
        timestamp="2026-10-14T10:05:00",
        target_repo="my-app",
        duration_seconds=2.5,
        total_iterations=2,
        success=False,
        estimated_cost_usd=0.0004
    )

    MetricsTracker.record_session(m1, tmp_path)
    MetricsTracker.record_session(m2, tmp_path)

    summary = MetricsTracker.get_summary(tmp_path)
    assert summary["total_runs"] == 2
    assert summary["successful_runs"] == 1
    assert summary["success_rate"] == 50.0
    assert summary["avg_duration"] == 2.0
