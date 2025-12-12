from __future__ import annotations

from datetime import date

import yaml

from macrolens_poc.pipeline.matrix_status import update_matrix_status
from macrolens_poc.pipeline.run_series import SeriesRunResult
from macrolens_poc.sources.matrix import load_sources_matrix


def test_update_matrix_status_updates_ok_and_warn(tmp_path) -> None:
    matrix_path = tmp_path / "matrix.yaml"
    matrix_path.write_text(
        yaml.safe_dump(
            {
                "version": 1,
                "series": [
                    {
                        "id": "a",
                        "provider": "fred",
                        "provider_symbol": "AAA",
                        "category": "cat",
                        "enabled": True,
                        "notes": "keep-a",
                    },
                    {
                        "id": "b",
                        "provider": "yfinance",
                        "provider_symbol": "BBB",
                        "category": "cat",
                        "enabled": True,
                    },
                ],
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )

    matrix_result = load_sources_matrix(matrix_path)
    results = [
        SeriesRunResult(
            series_id="a",
            provider="fred",
            status="ok",
            message="ok",
            stored_path=None,
            new_points=3,
        ),
        SeriesRunResult(
            series_id="b",
            provider="yfinance",
            status="warn",
            message="empty after normalize",
            stored_path=None,
            new_points=0,
        ),
    ]

    update_matrix_status(matrix_result=matrix_result, results=results, today=date(2024, 1, 5))

    updated = yaml.safe_load(matrix_path.read_text(encoding="utf-8"))
    entries = {item["id"]: item for item in updated["series"]}

    assert entries["a"]["status"] == "ok"
    assert entries["a"]["last_ok"] == "2024-01-05"
    assert entries["a"]["notes"] == "keep-a"

    assert entries["b"]["status"] == "warn"
    assert "last_ok" not in entries["b"]


def test_update_matrix_status_preserves_last_ok_on_failures(tmp_path) -> None:
    matrix_path = tmp_path / "matrix.yaml"
    matrix_path.write_text(
        yaml.safe_dump(
            {
                "version": 1,
                "series": [
                    {
                        "id": "c",
                        "provider": "fred",
                        "provider_symbol": "CCC",
                        "category": "cat",
                        "enabled": True,
                        "last_ok": "2024-01-01",
                        "status": "ok",
                    },
                    {
                        "id": "d",
                        "provider": "fred",
                        "provider_symbol": "DDD",
                        "category": "cat",
                        "enabled": True,
                        "notes": "keep-d",
                    },
                ],
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )

    matrix_result = load_sources_matrix(matrix_path)
    results = [
        SeriesRunResult(
            series_id="c",
            provider="fred",
            status="error",
            message="store failed",
            stored_path=None,
            new_points=0,
        ),
        SeriesRunResult(
            series_id="d",
            provider="fred",
            status="missing",
            message="no data",
            stored_path=None,
            new_points=0,
        ),
    ]

    update_matrix_status(matrix_result=matrix_result, results=results, today=date(2024, 1, 6))

    updated = yaml.safe_load(matrix_path.read_text(encoding="utf-8"))
    entries = {item["id"]: item for item in updated["series"]}

    assert entries["c"]["status"] == "error"
    assert entries["c"]["last_ok"] == "2024-01-01"

    assert entries["d"]["status"] == "missing"
    assert "last_ok" not in entries["d"]
    assert entries["d"]["notes"] == "keep-d"
