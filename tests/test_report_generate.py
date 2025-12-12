from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from macrolens_poc.logging_utils import RunContext
from macrolens_poc.report.generate import (
    DEFAULT_DELTA_WINDOWS,
    compute_deltas,
    generate_series_report,
    write_report_artifacts,
)
from macrolens_poc.sources.matrix import SeriesSpec


def test_compute_deltas_calendar_days() -> None:
    df = pd.DataFrame(
        {
            "date": pd.date_range("2024-01-01", periods=5, freq="D", tz="UTC"),
            "value": [1, 2, 3, 4, 5],
        }
    )

    deltas = compute_deltas(df, windows=[1, 3])

    assert deltas[1] == 1  # 5 - 4
    assert deltas[3] == 3  # 5 - 2


def test_generate_series_report_missing(tmp_path: Path) -> None:
    spec = SeriesSpec(
        id="missing_series",
        provider="fred",
        provider_symbol="X",
        category="test",
    )

    report = generate_series_report(spec=spec, data_dir=tmp_path, windows=DEFAULT_DELTA_WINDOWS)

    assert report.status == "missing"
    assert report.last_value is None


def test_write_report_artifacts(tmp_path: Path) -> None:
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    stored = pd.DataFrame(
        {
            "date": pd.to_datetime(["2024-01-01", "2024-01-02"], utc=True),
            "value": [10.0, 12.0],
        }
    )
    (data_dir / "series").mkdir()
    stored.to_parquet(data_dir / "series" / "s1.parquet", index=False)

    spec = SeriesSpec(
        id="s1",
        provider="fred",
        provider_symbol="X",
        category="test",
    )

    series_report = generate_series_report(spec=spec, data_dir=data_dir, windows=[1, 5])
    run_ctx = RunContext(run_id="test", started_at_utc=datetime(2024, 1, 3, tzinfo=timezone.utc))

    artifacts = write_report_artifacts(
        reports=[series_report],
        reports_dir=tmp_path / "reports",
        report_tz="UTC",
        run_ctx=run_ctx,
        windows=[1, 5],
    )

    md_text = Path(artifacts["markdown"]).read_text(encoding="utf-8")
    json_text = Path(artifacts["json"]).read_text(encoding="utf-8")

    assert "MacroLens Daily Report" in md_text
    assert "Δ1d" in md_text and "Δ5d" in md_text
    assert "report-20240103.md" in str(artifacts["markdown"])
    assert "\"id\": " in json_text and "s1" in json_text
