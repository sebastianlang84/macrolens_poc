from __future__ import annotations

import pandas as pd

from macrolens_poc.storage.parquet_store import merge_series


def test_merge_series_counts_new_points_and_dedupes() -> None:
    existing = pd.DataFrame(
        {
            "date": ["2024-01-01", "2024-01-02"],
            "value": [1.0, 2.0],
        }
    )
    incoming = pd.DataFrame(
        {
            "date": ["2024-01-02", "2024-01-03"],
            "value": [20.0, 3.0],
        }
    )

    merged, new_points, revision_overwrites_count, revision_overwrites_sample = merge_series(
        existing, incoming
    )

    assert new_points == 1
    assert revision_overwrites_count == 1
    assert len(merged) == 3

    # 2024-01-02 overwritten by incoming (keep last)
    v_0102 = merged.loc[merged["date"].dt.strftime("%Y-%m-%d") == "2024-01-02", "value"].iloc[0]
    assert v_0102 == 20.0

    # no duplicates on date
    assert merged["date"].dt.strftime("%Y-%m-%d").duplicated().sum() == 0

    # sample contains the overwritten point (date + old/new)
    assert any(
        s["date"] == "2024-01-02" and s["old"] == 2.0 and s["new"] == 20.0 for s in revision_overwrites_sample
    )
