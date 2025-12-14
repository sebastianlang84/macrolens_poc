from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

import pandas as pd

from macrolens_poc.config import Settings
from macrolens_poc.sources.fred import fetch_fred_series_observations
from macrolens_poc.sources.matrix import SeriesSpec
from macrolens_poc.sources.yahoo import fetch_yahoo_history
from macrolens_poc.storage.parquet_store import StoreResult, load_series, store_series


@dataclass(frozen=True)
class SeriesRunResult:
    series_id: str
    provider: str
    status: str  # ok/warn/error/missing
    message: str
    stored_path: Optional[Path]
    new_points: int
    revision_overwrites_count: int = 0
    revision_overwrites_sample: Optional[list[dict]] = None
    error_type: Optional[str] = None
    error_message: Optional[str] = None
    last_observation_date: Optional[date] = None
    run_at: Optional[datetime] = None


def _normalize_timeseries(df: pd.DataFrame) -> pd.DataFrame:
    """Normalize to canonical schema (date,value) sorted and deduped."""

    if df.empty:
        return df

    out = df.copy()
    if "date" not in out.columns or "value" not in out.columns:
        raise ValueError("timeseries must have columns date,value")

    out["date"] = pd.to_datetime(out["date"], utc=True)
    out["value"] = pd.to_numeric(out["value"], errors="coerce")

    out = out.dropna(subset=["date"])
    out = out.drop_duplicates(subset=["date"], keep="last")
    out = out.sort_values("date")

    return out[["date", "value"]]


def run_series(
    *,
    settings: Settings,
    spec: SeriesSpec,
    lookback_days: int = 3650,
    as_of: Optional[datetime] = None,
) -> SeriesRunResult:
    """Fetch + normalize + store one series.

    Storage layout (PoC):
      data/series/{id}.parquet

    lookback_days is a pragmatic default to avoid full-history fetch for some providers.
    as_of overrides the reference date/time (default: UTC now).
    """

    run_ts = as_of if as_of else datetime.now(timezone.utc)
    if run_ts.tzinfo is None:
        run_ts = run_ts.replace(tzinfo=timezone.utc)

    ref_date = run_ts.date()
    observation_start = ref_date - timedelta(days=lookback_days)

    if spec.provider == "fred":
        try:
            fetched = fetch_fred_series_observations(
                series_id=spec.provider_symbol,
                api_key=settings.fred_api_key,
                observation_start=observation_start,
                observation_end=ref_date,
            )
        except Exception as exc:
            return SeriesRunResult(
                series_id=spec.id,
                provider=str(spec.provider),
                status="error",
                message="provider fetch failed",
                stored_path=None,
                new_points=0,
                error_type=type(exc).__name__,
                error_message=str(exc),
            )
    elif spec.provider == "yfinance":
        try:
            fetched = fetch_yahoo_history(
                symbol=spec.provider_symbol,
                start=observation_start,
                end=ref_date + timedelta(days=1),
                interval="1d",
            )
        except Exception as exc:
            return SeriesRunResult(
                series_id=spec.id,
                provider=str(spec.provider),
                status="error",
                message="provider fetch failed",
                stored_path=None,
                new_points=0,
                error_type=type(exc).__name__,
                error_message=str(exc),
            )
    else:
        return SeriesRunResult(
            series_id=spec.id,
            provider=str(spec.provider),
            status="error",
            message=f"unsupported provider: {spec.provider}",
            stored_path=None,
            new_points=0,
            last_observation_date=None,
            run_at=run_ts,
        )

    if fetched.data is None:
        return SeriesRunResult(
            series_id=spec.id,
            provider=spec.provider,
            status=fetched.status,
            message=fetched.message,
            stored_path=None,
            new_points=0,
            last_observation_date=None,
            run_at=run_ts,
            error_type=getattr(fetched, "error_type", None),
            error_message=getattr(fetched, "error_message", None),
        )

    try:
        normalized = _normalize_timeseries(fetched.data)
    except Exception as exc:
        return SeriesRunResult(
            series_id=spec.id,
            provider=spec.provider,
            status="error",
            message=f"normalize failed: {exc}",
            stored_path=None,
            new_points=0,
            last_observation_date=None,
            run_at=run_ts,
            error_type=type(exc).__name__,
            error_message=str(exc),
        )

    # basic validation
    if normalized.empty:
        status = "warn" if fetched.status == "ok" else fetched.status
        msg = "empty after normalize" if fetched.status == "ok" else fetched.message
        return SeriesRunResult(
            series_id=spec.id,
            provider=spec.provider,
            status=status,
            message=msg,
            stored_path=None,
            new_points=0,
            last_observation_date=None,
            run_at=run_ts,
        )

    out_path = settings.paths.data_dir / "series" / f"{spec.id}.parquet"

    try:
        store_result: StoreResult = store_series(out_path, normalized)
    except Exception as exc:
        return SeriesRunResult(
            series_id=spec.id,
            provider=spec.provider,
            status="error",
            message=f"store failed: {exc}",
            stored_path=out_path,
            new_points=0,
            error_type=type(exc).__name__,
            error_message=str(exc),
        )

    final_series = load_series(out_path)
    last_observation_date = (
        final_series["date"].max().date() if final_series is not None and not final_series.empty else None
    )

    # Staleness check
    status = fetched.status
    message = "ok"

    if status == "ok" and last_observation_date is not None:
        threshold = spec.stale_days if spec.stale_days is not None else settings.stale_days_default
        delta_days = (ref_date - last_observation_date).days
        if delta_days > threshold:
            status = "warn"
            message = f"stale: last data {delta_days} days ago (threshold: {threshold})"

    return SeriesRunResult(
        series_id=spec.id,
        provider=spec.provider,
        status=status,
        message=message,
        stored_path=store_result.path,
        new_points=store_result.new_points,
        revision_overwrites_count=store_result.revision_overwrites_count,
        revision_overwrites_sample=store_result.revision_overwrites_sample,
        last_observation_date=last_observation_date,
        run_at=run_ts,
    )
