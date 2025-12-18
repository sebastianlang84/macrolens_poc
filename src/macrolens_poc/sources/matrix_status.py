from __future__ import annotations

import json
import os
from dataclasses import dataclass
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Literal, Optional

from pydantic import BaseModel, Field, ValidationError

from macrolens_poc.pipeline.run_series import SeriesRunResult

MatrixStatus = Literal["ok", "warn", "error", "missing"]


class SeriesStatusEntry(BaseModel):
    status: MatrixStatus

    # Semantics:
    # - last_ok is only updated on status==ok
    # - last_run_at is updated on every run for affected series
    last_ok: Optional[str] = Field(default=None)
    last_run_at: Optional[str] = Field(default=None)
    last_observation_date: Optional[str] = Field(default=None)

    # Optional last error / warning message (cleared on ok).
    last_error: Optional[str] = Field(default=None)


class MatrixStatusFile(BaseModel):
    version: int = Field(default=1)
    updated_at: Optional[str] = Field(default=None)

    # Keyed by internal series id.
    series: Dict[str, SeriesStatusEntry] = Field(default_factory=dict)


@dataclass(frozen=True)
class MergeResult:
    merged: MatrixStatusFile
    updated_entries: int


def default_matrix_status_path(data_dir: Path) -> Path:
    return data_dir / "matrix_status.json"


def load_matrix_status(path: Path) -> MatrixStatusFile:
    """Load matrix status file.

    If the file does not exist, returns an empty default structure.
    """

    if not path.exists():
        return MatrixStatusFile()

    raw = path.read_text(encoding="utf-8")
    parsed = json.loads(raw) if raw.strip() else {}
    if not isinstance(parsed, dict):
        raise ValueError("matrix status must be a JSON object at the top level")

    try:
        return MatrixStatusFile.model_validate(parsed)
    except ValidationError as exc:
        raise ValueError(f"Invalid matrix status file: {exc}") from exc


def merge_matrix_status(
    *,
    existing: MatrixStatusFile,
    run_results: Iterable[SeriesRunResult],
    run_at_utc: datetime,
) -> MergeResult:
    """Merge per-series run results into an existing MatrixStatusFile.

    Deterministic merge rules:
    - Only series included in run_results are updated.
    - status is always overwritten for affected series.
    - last_ok is set to run_at_utc.date().isoformat() *only* when status=="ok".
      Otherwise last_ok remains unchanged.
    - last_run_at is always set for affected series.
    - last_error is set for non-ok statuses if any message is available; cleared on ok.
    """

    # Normalize timestamp once.
    if run_at_utc.tzinfo is None:
        run_at_utc = run_at_utc.replace(tzinfo=timezone.utc)
    else:
        run_at_utc = run_at_utc.astimezone(timezone.utc)

    run_at_iso = run_at_utc.isoformat()
    run_ok_date = run_at_utc.date().isoformat()

    # Copy existing mapping (keep untouched series).
    merged_series: Dict[str, SeriesStatusEntry] = dict(existing.series)

    updated_entries = 0

    for result in run_results:
        prev = merged_series.get(result.series_id)

        prev_dump = prev.model_dump(mode="python") if prev is not None else None

        next_entry = (
            prev.model_copy(deep=True) if prev is not None else SeriesStatusEntry(status=result.status)
        )  # type: ignore[arg-type]
        next_entry.status = result.status  # type: ignore[assignment]
        next_entry.last_run_at = run_at_iso

        if result.status == "ok":
            next_entry.last_ok = run_ok_date
            next_entry.last_error = None
        else:
            # Keep last_ok unchanged on non-ok outcomes.
            msg = result.error_message or result.message
            next_entry.last_error = msg or next_entry.last_error

        next_dump = next_entry.model_dump(mode="python")

        if prev_dump != next_dump:
            updated_entries += 1

        merged_series[result.series_id] = next_entry

    merged = MatrixStatusFile(
        version=existing.version,
        updated_at=run_at_iso,
        series=merged_series,
    )

    return MergeResult(merged=merged, updated_entries=updated_entries)


def save_matrix_status(path: Path, status_file: MatrixStatusFile) -> None:
    """Atomically write the matrix status file as stable JSON.

    Uses a temp file + os.replace to avoid partial writes.
    """

    path.parent.mkdir(parents=True, exist_ok=True)

    payload: Dict[str, Any] = status_file.model_dump(mode="python")
    content = json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2) + "\n"

    tmp_path = path.with_suffix(path.suffix + ".tmp")
    tmp_path.write_text(content, encoding="utf-8")
    os.replace(tmp_path, path)


def identify_stale_series(
    *,
    status_file: MatrixStatusFile,
    ref_date: date,
    default_threshold: int = 7,
    overrides: Optional[Dict[str, int]] = None,
) -> List[Dict[str, Any]]:
    """Identify series that haven't seen new data for a while.

    Returns a list of dicts with details about stale series.
    """
    stale = []
    overrides = overrides or {}

    for series_id, entry in status_file.series.items():
        if not entry.last_observation_date:
            continue

        threshold = overrides.get(series_id, default_threshold)
        last_obs = date.fromisoformat(entry.last_observation_date)
        delta = (ref_date - last_obs).days

        if delta > threshold:
            stale.append(
                {
                    "series_id": series_id,
                    "last_observation_date": last_obs,
                    "delta_days": delta,
                    "threshold": threshold,
                    "status": entry.status,
                }
            )

    return sorted(stale, key=lambda x: x["delta_days"], reverse=True)
