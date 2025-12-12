from __future__ import annotations

from datetime import datetime, timezone

import pandas as pd

from macrolens_poc.report.v1 import _series_last_and_deltas


def test_series_last_and_deltas_missing_days_returns_none() -> None:
    # last day is 2024-01-10 with value 110
    # target day for 5d delta is 2024-01-05 (missing) => None
    df = pd.DataFrame(
        {
            "date": [
                datetime(2024, 1, 1, tzinfo=timezone.utc),
                datetime(2024, 1, 2, tzinfo=timezone.utc),
                datetime(2024, 1, 9, tzinfo=timezone.utc),
                datetime(2024, 1, 10, tzinfo=timezone.utc),
            ],
            "value": [100.0, 101.0, 109.0, 110.0],
        }
    )

    last, deltas = _series_last_and_deltas(df, windows_days=[1, 5, 21])

    assert last == 110.0
    assert deltas[1] == 110.0 - 109.0
    assert deltas[5] is None
    assert deltas[21] is None
