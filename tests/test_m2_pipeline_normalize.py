from __future__ import annotations

import pandas as pd

from macrolens_poc.pipeline.run_series import _normalize_timeseries


def test_normalize_dedupes_and_sorts() -> None:
    df = pd.DataFrame(
        {
            "date": ["2024-01-02", "2024-01-01", "2024-01-02"],
            "value": [2.0, 1.0, 20.0],
        }
    )

    out = _normalize_timeseries(df)

    assert list(out.columns) == ["date", "value"]
    assert len(out) == 2
    assert out.iloc[0]["date"].strftime("%Y-%m-%d") == "2024-01-01"

    v_0102 = out.loc[out["date"].dt.strftime("%Y-%m-%d") == "2024-01-02", "value"].iloc[0]
    assert v_0102 == 20.0
