from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import List, Optional
import sqlite3


@dataclass(frozen=True)
class SeriesMetadataRecord:
    series_id: str
    provider: str
    provider_symbol: str
    category: str
    frequency_target: str
    timezone: str
    units: str
    transform: str
    notes: str
    enabled: bool
    status: str
    message: str
    last_run_at: datetime
    last_ok_at: Optional[datetime]
    last_observation_date: Optional[date]
    stored_path: Optional[Path]
    new_points: int


def init_db(path: Path) -> None:
    """Ensure metadata database exists with the expected schema."""

    path.parent.mkdir(parents=True, exist_ok=True)

    with sqlite3.connect(path) as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS series_metadata (
                series_id TEXT PRIMARY KEY,
                provider TEXT NOT NULL,
                provider_symbol TEXT NOT NULL,
                category TEXT NOT NULL,
                frequency_target TEXT NOT NULL,
                timezone TEXT NOT NULL,
                units TEXT NOT NULL,
                transform TEXT NOT NULL,
                notes TEXT NOT NULL,
                enabled INTEGER NOT NULL,
                status TEXT NOT NULL,
                message TEXT NOT NULL,
                last_run_at TEXT NOT NULL,
                last_ok_at TEXT,
                last_observation_date TEXT,
                stored_path TEXT,
                new_points INTEGER NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_series_metadata_status ON series_metadata(status);
            """
        )


def upsert_series_metadata(db_path: Path, record: SeriesMetadataRecord) -> None:
    """Insert or update a series metadata record."""

    payload = _serialize_record(record)

    with sqlite3.connect(db_path) as conn:
        conn.execute(
            """
            INSERT INTO series_metadata (
                series_id,
                provider,
                provider_symbol,
                category,
                frequency_target,
                timezone,
                units,
                transform,
                notes,
                enabled,
                status,
                message,
                last_run_at,
                last_ok_at,
                last_observation_date,
                stored_path,
                new_points
            ) VALUES (
                :series_id,
                :provider,
                :provider_symbol,
                :category,
                :frequency_target,
                :timezone,
                :units,
                :transform,
                :notes,
                :enabled,
                :status,
                :message,
                :last_run_at,
                :last_ok_at,
                :last_observation_date,
                :stored_path,
                :new_points
            )
            ON CONFLICT(series_id) DO UPDATE SET
                provider=excluded.provider,
                provider_symbol=excluded.provider_symbol,
                category=excluded.category,
                frequency_target=excluded.frequency_target,
                timezone=excluded.timezone,
                units=excluded.units,
                transform=excluded.transform,
                notes=excluded.notes,
                enabled=excluded.enabled,
                status=excluded.status,
                message=excluded.message,
                last_run_at=excluded.last_run_at,
                last_ok_at=excluded.last_ok_at,
                last_observation_date=excluded.last_observation_date,
                stored_path=excluded.stored_path,
                new_points=excluded.new_points;
            """,
            payload,
        )


def list_series_metadata(db_path: Path) -> List[SeriesMetadataRecord]:
    """Return all series metadata records ordered by series_id."""

    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            "SELECT * FROM series_metadata ORDER BY series_id"
        ).fetchall()

    return [_row_to_record(row) for row in rows]


def get_series_metadata(db_path: Path, series_id: str) -> Optional[SeriesMetadataRecord]:
    """Return one series metadata entry if present."""

    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        row = conn.execute(
            "SELECT * FROM series_metadata WHERE series_id = ?", (series_id,)
        ).fetchone()

    if row is None:
        return None

    return _row_to_record(row)


def _serialize_record(record: SeriesMetadataRecord) -> dict:
    return {
        "series_id": record.series_id,
        "provider": record.provider,
        "provider_symbol": record.provider_symbol,
        "category": record.category,
        "frequency_target": record.frequency_target,
        "timezone": record.timezone,
        "units": record.units,
        "transform": record.transform,
        "notes": record.notes,
        "enabled": 1 if record.enabled else 0,
        "status": record.status,
        "message": record.message,
        "last_run_at": record.last_run_at.isoformat(),
        "last_ok_at": record.last_ok_at.isoformat() if record.last_ok_at else None,
        "last_observation_date": record.last_observation_date.isoformat()
        if record.last_observation_date
        else None,
        "stored_path": str(record.stored_path) if record.stored_path else None,
        "new_points": record.new_points,
    }


def _row_to_record(row: sqlite3.Row) -> SeriesMetadataRecord:
    last_ok_at = row["last_ok_at"]
    last_observation_date = row["last_observation_date"]
    stored_path = row["stored_path"]

    return SeriesMetadataRecord(
        series_id=row["series_id"],
        provider=row["provider"],
        provider_symbol=row["provider_symbol"],
        category=row["category"],
        frequency_target=row["frequency_target"],
        timezone=row["timezone"],
        units=row["units"],
        transform=row["transform"],
        notes=row["notes"],
        enabled=bool(row["enabled"]),
        status=row["status"],
        message=row["message"],
        last_run_at=datetime.fromisoformat(row["last_run_at"]),
        last_ok_at=datetime.fromisoformat(last_ok_at) if last_ok_at else None,
        last_observation_date=date.fromisoformat(last_observation_date)
        if last_observation_date
        else None,
        stored_path=Path(stored_path) if stored_path else None,
        new_points=int(row["new_points"]),
    )


__all__ = [
    "SeriesMetadataRecord",
    "get_series_metadata",
    "init_db",
    "list_series_metadata",
    "upsert_series_metadata",
]
