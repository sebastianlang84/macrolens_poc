import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from macrolens_poc.logging_utils import RunContext
from macrolens_poc.report.generate import (
    DEFAULT_DELTA_WINDOWS,
    compute_deltas,
    generate_series_report,
    write_status_report,
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


def test_generate_series_report_stale_vs_fresh(tmp_path: Path) -> None:
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    (data_dir / "series").mkdir()

    stale_series = pd.DataFrame(
        {
            "date": pd.to_datetime(["2024-01-01"], utc=True),
            "value": [10.0],
        }
    )
    fresh_series = pd.DataFrame(
        {
            "date": pd.to_datetime(["2024-01-08"], utc=True),
            "value": [20.0],
        }
    )

    stale_series.to_parquet(data_dir / "series" / "stale.parquet", index=False)
    fresh_series.to_parquet(data_dir / "series" / "fresh.parquet", index=False)

    reference_time = datetime(2024, 1, 10, tzinfo=timezone.utc)

    stale_spec = SeriesSpec(id="stale", provider="fred", provider_symbol="X", category="test")
    fresh_spec = SeriesSpec(id="fresh", provider="fred", provider_symbol="Y", category="test")

    stale_report = generate_series_report(
        spec=stale_spec,
        data_dir=data_dir,
        data_tz="UTC",
        stale_threshold_days=3,
        reference_time=reference_time,
        windows=[1],
    )
    fresh_report = generate_series_report(
        spec=fresh_spec,
        data_dir=data_dir,
        data_tz="UTC",
        stale_threshold_days=3,
        reference_time=reference_time,
        windows=[1],
    )

    assert stale_report.status == "stale"
    assert stale_report.data_age_days == 9
    assert fresh_report.status == "warn"  # insufficient history for delta window
    assert fresh_report.data_age_days == 2


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

    series_report = generate_series_report(
        spec=spec,
        data_dir=data_dir,
        windows=[1, 5],
        data_tz="UTC",
        reference_time=datetime(2024, 1, 3, tzinfo=timezone.utc),
    )
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


def test_write_status_report(tmp_path: Path) -> None:
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    (data_dir / "series").mkdir()

    df = pd.DataFrame(
        {
            "date": pd.to_datetime(["2024-01-01", "2024-01-05"], utc=True),
            "value": [1.0, 2.0],
        }
    )
    df.to_parquet(data_dir / "series" / "s1.parquet", index=False)

    spec = SeriesSpec(id="s1", provider="fred", provider_symbol="X", category="test")
    run_ctx = RunContext(run_id="test", started_at_utc=datetime(2024, 1, 10, tzinfo=timezone.utc))

    report = generate_series_report(
        spec=spec,
        data_dir=data_dir,
        data_tz="UTC",
        stale_threshold_days=3,
        reference_time=datetime(2024, 1, 10, tzinfo=timezone.utc),
        windows=[1],
    )

    artifacts = write_status_report(
        reports=[report],
        reports_dir=tmp_path / "reports",
        report_tz="UTC",
        run_ctx=run_ctx,
    )

    json_payload = json.loads(Path(artifacts["json"]).read_text(encoding="utf-8"))
    csv_rows = pd.read_csv(artifacts["csv"])  # type: ignore[call-arg]

    assert json_payload[0]["status"] == "stale"
    assert json_payload[0]["data_age_days"] == 5
    assert "status-20240110.json" in str(artifacts["json"])
    assert list(csv_rows["status"]) == ["stale"]
