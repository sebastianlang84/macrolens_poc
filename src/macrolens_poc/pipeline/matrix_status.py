from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Iterable, Optional

import yaml

from macrolens_poc.pipeline.run_series import SeriesRunResult
from macrolens_poc.sources.matrix import MatrixLoadResult


def update_matrix_status(
    matrix_result: MatrixLoadResult,
    results: Iterable[SeriesRunResult],
    *,
    today: Optional[date] = None,
) -> Path:
    """Persist run statuses back to the sources matrix.

    Only status/last_ok fields are modified. All other fields remain untouched.
    """

    result_by_id = {res.series_id: res for res in results}
    if not result_by_id:
        return matrix_result.path

    raw = yaml.safe_load(matrix_result.path.read_text(encoding="utf-8")) or {}
    if not isinstance(raw, dict):
        raise ValueError("sources matrix must be a mapping/object at the top level")

    series_entries = raw.get("series")
    if not isinstance(series_entries, list):
        raise ValueError("sources matrix must contain a 'series' list")

    today_value = (today or date.today()).isoformat()

    for entry in series_entries:
        if not isinstance(entry, dict):
            continue

        series_id = entry.get("id")
        if series_id is None or series_id not in result_by_id:
            continue

        result = result_by_id[series_id]
        entry["status"] = result.status
        if result.status == "ok":
            entry["last_ok"] = today_value

    matrix_result.path.write_text(
        yaml.safe_dump(raw, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )

    return matrix_result.path
