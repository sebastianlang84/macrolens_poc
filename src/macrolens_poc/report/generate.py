from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from zoneinfo import ZoneInfo

import pandas as pd

from macrolens_poc.logging_utils import RunContext
from macrolens_poc.pipeline.status import DEFAULT_STALE_THRESHOLD_DAYS, compute_data_age_days, is_stale
from macrolens_poc.sources.matrix import SeriesSpec
from macrolens_poc.storage.parquet_store import load_series

DEFAULT_DELTA_WINDOWS: List[int] = [1, 5, 21]


@dataclass(frozen=True)
class SeriesReport:
    series_id: str
    provider: str
    status: str  # ok/warn/error/missing
    message: str
    last_date: Optional[pd.Timestamp]
    last_value: Optional[float]
    deltas: Dict[int, Optional[float]]
    data_age_days: Optional[int]
    path: Path


def compute_deltas(series: pd.DataFrame, *, windows: List[int]) -> Dict[int, Optional[float]]:
    """Compute absolute deltas to past observations.

    For each window (in calendar days), pick the most recent value *on or before*
    last_date - window_days. Returns None when no such value exists.
    """

    if series.empty:
        return {w: None for w in windows}

    sorted_series = series.sort_values("date")
    last_date = sorted_series["date"].iloc[-1]
    last_value = sorted_series["value"].iloc[-1]

    deltas: Dict[int, Optional[float]] = {}
    for w in windows:
        cutoff = last_date - pd.Timedelta(days=w)
        historical = sorted_series[sorted_series["date"] <= cutoff]
        if historical.empty:
            deltas[w] = None
            continue

        prev_value = historical["value"].iloc[-1]
        deltas[w] = float(last_value) - float(prev_value)

    return deltas


def generate_series_report(
    *,
    spec: SeriesSpec,
    data_dir: Path,
    data_tz: str = "UTC",
    stale_threshold_days: int = DEFAULT_STALE_THRESHOLD_DAYS,
    reference_time: Optional[datetime] = None,
    windows: List[int] = DEFAULT_DELTA_WINDOWS,
) -> SeriesReport:
    """Build a per-series report from stored Parquet data."""

    path = data_dir / "series" / f"{spec.id}.parquet"
    df = load_series(path)

    if df is None:
        return SeriesReport(
            series_id=spec.id,
            provider=spec.provider,
            status="missing",
            message="stored series not found",
            last_date=None,
            last_value=None,
            deltas={w: None for w in windows},
            data_age_days=None,
            path=path,
        )

    if df.empty:
        return SeriesReport(
            series_id=spec.id,
            provider=spec.provider,
            status="warn",
            message="stored series empty",
            last_date=None,
            last_value=None,
            deltas={w: None for w in windows},
            data_age_days=None,
            path=path,
        )

    last_row = df.sort_values("date").iloc[-1]
    deltas = compute_deltas(df, windows=windows)

    now = reference_time or datetime.now(ZoneInfo(data_tz))
    data_age_days = compute_data_age_days(last_date=last_row["date"], now=now)

    status = "ok" if all(v is not None for v in deltas.values()) else "warn"
    message = "ok" if status == "ok" else "insufficient history for some deltas"

    if is_stale(last_date=last_row["date"], now=now, threshold_days=stale_threshold_days):
        status = "stale"
        message = (
            f"stale: last update {last_row['date'].date()} age {data_age_days}d "
            f"(threshold {stale_threshold_days}d)"
        )

    return SeriesReport(
        series_id=spec.id,
        provider=spec.provider,
        status=status,
        message=message,
        last_date=last_row["date"],
        last_value=float(last_row["value"]),
        deltas=deltas,
        data_age_days=data_age_days,
        path=path,
    )


def _format_value(value: Optional[float]) -> str:
    if value is None or pd.isna(value):
        return "n/a"
    return f"{value:.4f}"


def _format_date(ts: Optional[pd.Timestamp], tz: ZoneInfo) -> str:
    if ts is None or pd.isna(ts):
        return "n/a"
    return ts.tz_convert(tz).strftime("%Y-%m-%d %H:%M %Z")


def write_report_artifacts(
    *,
    reports: List[SeriesReport],
    reports_dir: Path,
    report_tz: str,
    run_ctx: RunContext,
    windows: List[int] = DEFAULT_DELTA_WINDOWS,
) -> Dict[str, Path]:
    tz = ZoneInfo(report_tz)
    ts_tag = run_ctx.started_at_utc.strftime("%Y%m%d")

    md_path = reports_dir / f"report-{ts_tag}.md"
    json_path = reports_dir / f"report-{ts_tag}.json"

    reports_dir.mkdir(parents=True, exist_ok=True)

    md = _render_markdown(reports=reports, tz=tz, windows=windows, generated_at=run_ctx.started_at_utc)
    md_path.write_text(md, encoding="utf-8")

    payload = _render_json_payload(reports=reports, tz=tz, windows=windows, generated_at=run_ctx.started_at_utc)
    json_path.write_text(payload, encoding="utf-8")

    return {"markdown": md_path, "json": json_path}


def _render_markdown(
    *,
    reports: List[SeriesReport],
    tz: ZoneInfo,
    windows: List[int],
    generated_at: datetime,
) -> str:
    lines: List[str] = []
    lines.append("# MacroLens Daily Report")
    lines.append("")
    lines.append(f"Generated at {generated_at.astimezone(tz).isoformat()}")
    lines.append("")

    headers = ["ID", "Provider", "Last Date", "Last Value"] + [f"Δ{w}d" for w in windows] + ["Status", "Note"]
    lines.append(" | ".join(headers))
    lines.append(" | ".join(["---"] * len(headers)))

    for rep in reports:
        row: List[str] = [
            rep.series_id,
            rep.provider,
            _format_date(rep.last_date, tz),
            _format_value(rep.last_value),
        ]

        for w in windows:
            row.append(_format_value(rep.deltas.get(w)))

        row.extend([rep.status, rep.message])
        lines.append(" | ".join(row))

    return "\n".join(lines) + "\n"


def _render_json_payload(
    *,
    reports: List[SeriesReport],
    tz: ZoneInfo,
    windows: List[int],
    generated_at: datetime,
) -> str:
    serializable: Dict[str, object] = {
        "generated_at": generated_at.astimezone(tz).isoformat(),
        "windows_days": windows,
        "series": [],
    }

    for rep in reports:
        entry: Dict[str, object] = {
            "id": rep.series_id,
            "provider": rep.provider,
            "status": rep.status,
            "message": rep.message,
            "path": str(rep.path),
            "last_date": _format_date(rep.last_date, tz),
            "last_value": rep.last_value,
            "data_age_days": rep.data_age_days,
            "deltas": {f"d{w}": rep.deltas.get(w) for w in windows},
        }
        serializable["series"].append(entry)

    return json.dumps(serializable, indent=2, ensure_ascii=False)


def write_status_report(
    *, reports: List[SeriesReport], reports_dir: Path, report_tz: str, run_ctx: RunContext
) -> Dict[str, Path]:
    tz = ZoneInfo(report_tz)
    ts_tag = run_ctx.started_at_utc.strftime("%Y%m%d")

    reports_dir.mkdir(parents=True, exist_ok=True)

    json_path = reports_dir / f"status-{ts_tag}.json"
    csv_path = reports_dir / f"status-{ts_tag}.csv"

    payload: List[Dict[str, object]] = []
    for rep in reports:
        payload.append(
            {
                "id": rep.series_id,
                "provider": rep.provider,
                "status": rep.status,
                "message": rep.message,
                "last_date": _format_date(rep.last_date, tz),
                "data_age_days": rep.data_age_days,
                "path": str(rep.path),
            }
        )

    json_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

    df = pd.DataFrame(payload)
    df.to_csv(csv_path, index=False)

    return {"json": json_path, "csv": csv_path}
