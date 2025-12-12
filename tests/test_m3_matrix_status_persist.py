from __future__ import annotations

from datetime import datetime, timezone

from macrolens_poc.pipeline.run_series import SeriesRunResult
from macrolens_poc.sources.matrix_status import MatrixStatusFile, merge_matrix_status


def test_merge_matrix_status_deterministic_and_keeps_unaffected() -> None:
    existing = MatrixStatusFile(
        version=1,
        updated_at="2025-01-01T00:00:00+00:00",
        series={
            "A": {
                "status": "ok",
                "last_ok": "2025-01-01",
                "last_run_at": "2025-01-01T00:00:00+00:00",
                "last_error": None,
            },
            "B": {
                "status": "error",
                "last_ok": "2024-12-31",
                "last_run_at": "2025-01-01T00:00:00+00:00",
                "last_error": "boom",
            },
        },
    )

    run_at = datetime(2025, 2, 2, 12, 0, 0, tzinfo=timezone.utc)

    # Only B is in this run, and it becomes warn. last_ok must be preserved.
    results = [
        SeriesRunResult(
            series_id="B",
            provider="fred",
            status="warn",
            message="empty after normalize",
            stored_path=None,
            new_points=0,
            error_type=None,
            error_message=None,
        )
    ]

    merge1 = merge_matrix_status(existing=existing, run_results=results, run_at_utc=run_at)
    merge2 = merge_matrix_status(existing=existing, run_results=results, run_at_utc=run_at)

    assert merge1.merged.model_dump(mode="python") == merge2.merged.model_dump(mode="python")

    merged = merge1.merged

    # Unaffected series remains unchanged.
    assert merged.series["A"].model_dump(mode="python") == existing.series["A"].model_dump(mode="python")

    # Affected series: status updated, last_ok preserved, last_run_at updated, last_error written.
    b = merged.series["B"].model_dump(mode="python")
    assert b["status"] == "warn"
    assert b["last_ok"] == "2024-12-31"
    assert b["last_run_at"] == run_at.isoformat()
    assert b["last_error"] == "empty after normalize"

    # updated_entries counts only the series that actually changed.
    assert merge1.updated_entries == 1


def test_merge_matrix_status_updates_last_ok_only_on_ok() -> None:
    existing = MatrixStatusFile(
        version=1,
        updated_at=None,
        series={
            "X": {
                "status": "missing",
                "last_ok": "2020-01-01",
                "last_run_at": "2025-01-01T00:00:00+00:00",
                "last_error": "missing",
            }
        },
    )

    run_at = datetime(2025, 2, 2, 12, 0, 0, tzinfo=timezone.utc)

    results = [
        SeriesRunResult(
            series_id="X",
            provider="yfinance",
            status="ok",
            message="ok",
            stored_path=None,
            new_points=1,
            error_type=None,
            error_message=None,
        )
    ]

    merged = merge_matrix_status(existing=existing, run_results=results, run_at_utc=run_at).merged

    x = merged.series["X"].model_dump(mode="python")
    assert x["status"] == "ok"
    assert x["last_ok"] == "2025-02-02"
    assert x["last_run_at"] == run_at.isoformat()
    assert x["last_error"] is None
