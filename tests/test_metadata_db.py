from __future__ import annotations

from dataclasses import replace
from datetime import date, datetime, timezone
from pathlib import Path

from macrolens_poc.storage.metadata_db import (
    SeriesMetadataRecord,
    get_series_metadata,
    init_db,
    list_series_metadata,
    upsert_series_metadata,
)


def _sample_record(db_dir: Path) -> SeriesMetadataRecord:
    return SeriesMetadataRecord(
        series_id="spx",
        provider="yfinance",
        provider_symbol="^GSPC",
        category="equities",
        frequency_target="daily",
        timezone="UTC",
        units="index",
        transform="none",
        notes="S&P 500",
        enabled=True,
        status="ok",
        message="ok",
        last_run_at=datetime(2024, 1, 2, 12, 0, tzinfo=timezone.utc),
        last_ok_at=datetime(2024, 1, 2, 12, 0, tzinfo=timezone.utc),
        last_observation_date=date(2024, 1, 2),
        stored_path=db_dir / "series" / "spx.parquet",
        new_points=3,
    )


def test_init_and_roundtrip(tmp_path: Path) -> None:
    db_path = tmp_path / "meta.sqlite"

    init_db(db_path)
    record = _sample_record(tmp_path)

    upsert_series_metadata(db_path, record)

    fetched = get_series_metadata(db_path, record.series_id)
    assert fetched == record

    all_records = list_series_metadata(db_path)
    assert all_records == [record]


def test_upsert_overwrites_existing(tmp_path: Path) -> None:
    db_path = tmp_path / "meta.sqlite"
    init_db(db_path)

    record = _sample_record(tmp_path)
    upsert_series_metadata(db_path, record)

    updated = replace(
        record,
        status="warn",
        message="provider timeout",
        last_ok_at=None,
        new_points=0,
    )
    upsert_series_metadata(db_path, updated)

    fetched = get_series_metadata(db_path, record.series_id)
    assert fetched is not None
    assert fetched.status == "warn"
    assert fetched.message == "provider timeout"
    assert fetched.last_ok_at is None
    assert fetched.new_points == 0
