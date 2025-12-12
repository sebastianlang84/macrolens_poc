from __future__ import annotations

import json
import math
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Optional
from zoneinfo import ZoneInfo

import pandas as pd

from macrolens_poc.config import Settings
from macrolens_poc.sources import load_sources_matrix
from macrolens_poc.storage.parquet_store import load_series


@dataclass(frozen=True)
class SeriesRow:
    id: str
    category: str
    last: Optional[float]
    deltas: dict[str, Optional[float]]  # keys: d1, d5, d21


@dataclass(frozen=True)
class ReportV1:
    meta: dict[str, Any]
    table: list[SeriesRow]
    risk_flags: dict[str, Any]


@dataclass(frozen=True)
class ReportV1WriteResult:
    report: ReportV1
    md_path: Path
    json_path: Path


def _is_nan(x: object) -> bool:
    return isinstance(x, float) and math.isnan(x)


def _to_float_or_none(x: object) -> Optional[float]:
    if x is None:
        return None
    if isinstance(x, (int, float)):
        if _is_nan(x):
            return None
        return float(x)
    return None


def _format_md_number(x: Optional[float]) -> str:
    if x is None:
        return "—"
    if _is_nan(x):
        return "—"
    # deterministic formatting, but not overly verbose
    s = f"{float(x):.6f}"
    s = s.rstrip("0").rstrip(".")
    return s


def _series_last_and_deltas(
    df: Optional[pd.DataFrame],
    *,
    windows_days: list[int],
) -> tuple[Optional[float], dict[int, Optional[float]]]:
    """Return last non-null value and absolute deltas vs. (last_date - N days).

    Delta rule (PoC): use exact calendar day offsets in UTC.
    If the target date does not exist in the stored series, delta is None.
    """

    if df is None or df.empty:
        return None, {w: None for w in windows_days}

    if "date" not in df.columns or "value" not in df.columns:
        raise ValueError("stored series must have columns: date, value")

    s = df[["date", "value"]].copy()
    s["date"] = pd.to_datetime(s["date"], utc=True)
    s["value"] = pd.to_numeric(s["value"], errors="coerce")
    s = s.dropna(subset=["date"])
    s = s.sort_values("date")

    non_nan = s.dropna(subset=["value"])
    if non_nan.empty:
        return None, {w: None for w in windows_days}

    last_row = non_nan.iloc[-1]
    last_ts: pd.Timestamp = pd.Timestamp(last_row["date"]).tz_convert("UTC")
    last_day = last_ts.date()
    last_val = float(last_row["value"])

    # map UTC date -> last value for that day
    by_day: dict[datetime.date, float] = {}
    for row in non_nan.itertuples(index=False):
        ts: pd.Timestamp = pd.Timestamp(getattr(row, "date")).tz_convert("UTC")
        v = getattr(row, "value")
        if pd.isna(v):
            continue
        by_day[ts.date()] = float(v)

    deltas: dict[int, Optional[float]] = {}
    for w in windows_days:
        target_day = last_day - timedelta(days=w)
        if target_day not in by_day:
            deltas[w] = None
            continue
        deltas[w] = last_val - by_day[target_day]

    return last_val, deltas


def compute_risk_flags(*, rows_by_id: dict[str, SeriesRow]) -> dict[str, Any]:
    """Simple deterministic risk flags.

    v1 rule set:
      - risk_off if VIX Δ5d > 0 AND SPX Δ5d < 0
      - risk_on  if VIX Δ5d < 0 AND SPX Δ5d > 0
      - neutral otherwise
      - unknown if any required series/delta is missing

    Series IDs are the internal ids from sources-matrix (expected: vix, sp500).
    """

    vix = rows_by_id.get("vix")
    spx = rows_by_id.get("sp500")
    if vix is None or spx is None:
        return {"risk_regime": "unknown"}

    vix_d5 = _to_float_or_none(vix.deltas.get("d5"))
    spx_d5 = _to_float_or_none(spx.deltas.get("d5"))

    if vix_d5 is None or spx_d5 is None:
        return {"risk_regime": "unknown"}

    if vix_d5 > 0 and spx_d5 < 0:
        return {"risk_regime": "risk_off"}
    if vix_d5 < 0 and spx_d5 > 0:
        return {"risk_regime": "risk_on"}

    return {"risk_regime": "neutral"}


def render_report_markdown(report: ReportV1) -> str:
    meta = report.meta
    lines: list[str] = []
    lines.append(f"# macrolens_poc Report ({meta['as_of_date']})")
    lines.append("")
    lines.append(f"Generated at (UTC): {meta['generated_at_utc']}")
    lines.append("")
    lines.append("## Risk Flags")
    for k in sorted(report.risk_flags.keys()):
        lines.append(f"- {k}: {report.risk_flags[k]}")
    lines.append("")

    lines.append("## Series Table")
    lines.append("")
    lines.append("| id | category | last | Δ1d | Δ5d | Δ21d |")
    lines.append("|---|---|---:|---:|---:|---:|")
    for row in report.table:
        d1 = row.deltas.get("d1")
        d5 = row.deltas.get("d5")
        d21 = row.deltas.get("d21")
        lines.append(
            "| "
            + " | ".join(
                [
                    row.id,
                    row.category,
                    _format_md_number(row.last),
                    _format_md_number(_to_float_or_none(d1)),
                    _format_md_number(_to_float_or_none(d5)),
                    _format_md_number(_to_float_or_none(d21)),
                ]
            )
            + " |"
        )

    lines.append("")
    return "\n".join(lines)


def _report_paths(*, reports_dir: Path, as_of_date_str: str) -> tuple[Path, Path]:
    yyyymmdd = as_of_date_str.replace("-", "")
    return (
        reports_dir / f"report-{yyyymmdd}.md",
        reports_dir / f"report-{yyyymmdd}.json",
    )


def write_report_files(*, report: ReportV1, reports_dir: Path) -> tuple[Path, Path]:
    reports_dir.mkdir(parents=True, exist_ok=True)

    md_path, json_path = _report_paths(reports_dir=reports_dir, as_of_date_str=str(report.meta["as_of_date"]))

    md_path.write_text(render_report_markdown(report), encoding="utf-8")

    # JSON: deterministic ordering
    payload = {
        "meta": report.meta,
        "table": [asdict(r) for r in report.table],
        "risk_flags": report.risk_flags,
    }
    json_path.write_text(json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")

    return md_path, json_path


def generate_report_v1(*, settings: Settings, now_utc: Optional[datetime] = None) -> ReportV1WriteResult:
    """Generate Report v1 based on stored series files."""

    now_utc = now_utc or datetime.now(timezone.utc)

    report_tz = ZoneInfo(settings.report_tz)
    as_of_date = now_utc.astimezone(report_tz).date()
    as_of_date_str = as_of_date.strftime("%Y-%m-%d")

    matrix_result = load_sources_matrix(settings.sources_matrix_path)
    enabled = [s for s in matrix_result.matrix.series if s.enabled]

    table: list[SeriesRow] = []
    rows_by_id: dict[str, SeriesRow] = {}

    for spec in enabled:
        p = settings.paths.data_dir / "series" / f"{spec.id}.parquet"
        df = load_series(p)

        last, deltas = _series_last_and_deltas(df, windows_days=[1, 5, 21])
        row = SeriesRow(
            id=spec.id,
            category=spec.category,
            last=last,
            deltas={
                "d1": deltas[1],
                "d5": deltas[5],
                "d21": deltas[21],
            },
        )
        table.append(row)
        rows_by_id[row.id] = row

    risk_flags = compute_risk_flags(rows_by_id=rows_by_id)

    report = ReportV1(
        meta={
            "as_of_date": as_of_date_str,
            "generated_at_utc": now_utc.astimezone(timezone.utc).isoformat(),
        },
        table=table,
        risk_flags=risk_flags,
    )

    md_path, json_path = write_report_files(report=report, reports_dir=settings.paths.reports_dir)

    return ReportV1WriteResult(report=report, md_path=md_path, json_path=json_path)
