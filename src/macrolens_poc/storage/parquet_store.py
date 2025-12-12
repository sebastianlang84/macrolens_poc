from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import pandas as pd


@dataclass(frozen=True)
class StoreResult:
    path: Path
    rows_before: int
    rows_after: int
    new_points: int


def load_series(path: Path) -> Optional[pd.DataFrame]:
    """Load an existing stored series.

    Storage format:
    - Parquet with columns: date (datetime64[ns, UTC] or datetime64[ns]), value (float)

    Returns None if file does not exist.
    """

    if not path.exists():
        return None

    df = pd.read_parquet(path)
    if df.empty:
        return df

    if "date" not in df.columns or "value" not in df.columns:
        raise ValueError(f"Invalid stored series schema in {path}: expected columns date,value")

    df = df.copy()
    df["date"] = pd.to_datetime(df["date"], utc=True)
    df = df.sort_values("date")
    return df


def merge_series(existing: Optional[pd.DataFrame], incoming: pd.DataFrame) -> tuple[pd.DataFrame, int]:
    """Merge incoming points into existing without duplicates.

    Rules:
    - de-duplicate on date (keep last)
    - sort by date ascending

    Returns merged dataframe and number of *new* dates added.
    """

    if incoming.empty:
        if existing is None:
            out = incoming.copy()
            out["date"] = pd.to_datetime(out.get("date", pd.Series([], dtype="datetime64[ns]")), utc=True)
            return out, 0
        return existing.copy(), 0

    inc = incoming.copy()
    if "date" not in inc.columns or "value" not in inc.columns:
        raise ValueError("Incoming series must have columns: date, value")

    inc["date"] = pd.to_datetime(inc["date"], utc=True)

    if existing is None or existing.empty:
        merged = inc.drop_duplicates(subset=["date"], keep="last").sort_values("date")
        return merged, len(merged)

    ex = existing.copy()
    ex["date"] = pd.to_datetime(ex["date"], utc=True)

    # pandas prevents .astype("datetime64[ns]") on tz-aware; normalize via tz_localize(None)
    ex_dates_ns = set(ex["date"].dt.tz_convert("UTC").dt.tz_localize(None).astype("int64").tolist())

    combined = pd.concat([ex, inc], ignore_index=True)
    merged = combined.drop_duplicates(subset=["date"], keep="last").sort_values("date")

    merged_dates_ns = set(
        merged["date"].dt.tz_convert("UTC").dt.tz_localize(None).astype("int64").tolist()
    )
    new_points = len(merged_dates_ns - ex_dates_ns)

    return merged, new_points


def store_series(path: Path, incoming: pd.DataFrame) -> StoreResult:
    """Merge and write series to Parquet."""

    path.parent.mkdir(parents=True, exist_ok=True)

    existing = load_series(path)
    rows_before = 0 if existing is None else len(existing)

    merged, new_points = merge_series(existing, incoming)
    rows_after = len(merged)

    merged.to_parquet(path, index=False)

    return StoreResult(
        path=path,
        rows_before=rows_before,
        rows_after=rows_after,
        new_points=new_points,
    )
