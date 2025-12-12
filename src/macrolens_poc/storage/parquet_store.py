from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

import pandas as pd

REVISION_SAMPLE_MAX = 10


@dataclass(frozen=True)
class StoreResult:
    path: Path
    rows_before: int
    rows_after: int
    new_points: int
    revision_overwrites_count: int
    revision_overwrites_sample: list[dict[str, Any]]


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


def _revision_overwrite_sample(df: pd.DataFrame) -> list[dict[str, Any]]:
    if df.empty:
        return []

    out: list[dict[str, Any]] = []
    for row in df.itertuples(index=False):
        # row: date, value_old, value_new
        dt: pd.Timestamp = getattr(row, "date")
        old = getattr(row, "value_old")
        new = getattr(row, "value_new")
        out.append(
            {
                "date": dt.tz_convert("UTC").strftime("%Y-%m-%d"),
                "old": None if pd.isna(old) else float(old),
                "new": None if pd.isna(new) else float(new),
            }
        )
        if len(out) >= REVISION_SAMPLE_MAX:
            break

    return out


def merge_series(
    existing: Optional[pd.DataFrame],
    incoming: pd.DataFrame,
) -> tuple[pd.DataFrame, int, int, list[dict[str, Any]]]:
    """Merge incoming points into existing without duplicates.

    Rules:
    - de-duplicate on date (keep last)
    - sort by date ascending
    - if incoming contains a value for an already-stored date, incoming overwrites the existing point

    Additionally detects "revision overwrites": same date exists already, but value changes.

    Returns:
      merged dataframe,
      number of *new* dates added,
      revision_overwrites_count,
      revision_overwrites_sample (max REVISION_SAMPLE_MAX items)
    """

    if incoming.empty:
        if existing is None:
            out = incoming.copy()
            out["date"] = pd.to_datetime(out.get("date", pd.Series([], dtype="datetime64[ns]")), utc=True)
            return out, 0, 0, []
        return existing.copy(), 0, 0, []

    inc = incoming.copy()
    if "date" not in inc.columns or "value" not in inc.columns:
        raise ValueError("Incoming series must have columns: date, value")

    inc["date"] = pd.to_datetime(inc["date"], utc=True)
    inc["value"] = pd.to_numeric(inc["value"], errors="coerce")
    inc = inc.drop_duplicates(subset=["date"], keep="last").sort_values("date")

    if existing is None or existing.empty:
        return inc, len(inc), 0, []

    ex = existing.copy()
    ex["date"] = pd.to_datetime(ex["date"], utc=True)
    ex["value"] = pd.to_numeric(ex["value"], errors="coerce")
    ex = ex.drop_duplicates(subset=["date"], keep="last").sort_values("date")

    # --- revision overwrite detection (existing date AND value changes) ---
    overlap = ex.merge(inc, on="date", how="inner", suffixes=("_old", "_new"))
    if overlap.empty:
        revision_overwrites = overlap
    else:
        old = overlap["value_old"]
        new = overlap["value_new"]
        both_na = old.isna() & new.isna()
        diff = (old != new) & ~both_na
        revision_overwrites = overlap.loc[diff, ["date", "value_old", "value_new"]].sort_values("date")

    revision_overwrites_count = int(len(revision_overwrites))
    revision_overwrites_sample = _revision_overwrite_sample(revision_overwrites)

    # pandas prevents .astype("datetime64[ns]") on tz-aware; normalize via tz_localize(None)
    ex_dates_ns = set(ex["date"].dt.tz_convert("UTC").dt.tz_localize(None).astype("int64").tolist())

    combined = pd.concat([ex, inc], ignore_index=True)
    merged = combined.drop_duplicates(subset=["date"], keep="last").sort_values("date")

    merged_dates_ns = set(
        merged["date"].dt.tz_convert("UTC").dt.tz_localize(None).astype("int64").tolist()
    )
    new_points = len(merged_dates_ns - ex_dates_ns)

    return merged, new_points, revision_overwrites_count, revision_overwrites_sample


def store_series(path: Path, incoming: pd.DataFrame) -> StoreResult:
    """Merge and write series to Parquet."""

    path.parent.mkdir(parents=True, exist_ok=True)

    existing = load_series(path)
    rows_before = 0 if existing is None else len(existing)

    merged, new_points, revision_overwrites_count, revision_overwrites_sample = merge_series(existing, incoming)
    rows_after = len(merged)

    merged.to_parquet(path, index=False)

    return StoreResult(
        path=path,
        rows_before=rows_before,
        rows_after=rows_after,
        new_points=new_points,
        revision_overwrites_count=revision_overwrites_count,
        revision_overwrites_sample=revision_overwrites_sample,
    )
