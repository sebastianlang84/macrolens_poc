from __future__ import annotations

from datetime import datetime, date, timezone
import pandas as pd
import pytest
from macrolens_poc.report.v1 import _series_last_and_deltas, find_nearest_value

def test_find_nearest_value_logic() -> None:
    # Setup: Friday and Monday exist, weekend missing
    # 2024-01-05 (Fri), 2024-01-08 (Mon)
    by_day = {
        date(2024, 1, 5): 100.0,
        date(2024, 1, 8): 105.0,
    }

    # 1. Exact Match
    assert find_nearest_value(by_day, date(2024, 1, 5)) == 100.0

    # 2. Lookback (Target Sunday, should find Friday)
    # Sunday (7th) - 2 days = Friday (5th) -> OK
    assert find_nearest_value(by_day, date(2024, 1, 7)) == 100.0

    # 3. Tie-break (Target Sunday, if Saturday and Monday existed)
    by_day_tie = {
        date(2024, 1, 6): 101.0, # Sat
        date(2024, 1, 8): 105.0, # Mon
    }
    # Target Sunday (7th). Both Sat and Mon are 1 day away.
    # Earlier (Sat) should win.
    assert find_nearest_value(by_day_tie, date(2024, 1, 7)) == 101.0

    # 4. Look-ahead (Target Saturday, only Monday exists in tolerance)
    by_day_future = {
        date(2024, 1, 8): 105.0,
    }
    # Target Saturday (6th). Monday is 2 days away.
    assert find_nearest_value(by_day_future, date(2024, 1, 6)) == 105.0

    # 5. Outside tolerance
    # Target Tuesday (2nd). Friday (5th) is 3 days away.
    assert find_nearest_value(by_day, date(2024, 1, 2), tolerance_days=2) is None

def test_robust_deltas_integration() -> None:
    # Last day is Monday 2024-01-08
    # d1 delta target is Sunday 2024-01-07 (missing)
    # Should find Friday 2024-01-05
    df = pd.DataFrame({
        "date": [
            datetime(2024, 1, 5, tzinfo=timezone.utc),
            datetime(2024, 1, 8, tzinfo=timezone.utc),
        ],
        "value": [100.0, 105.0]
    })

    last, deltas = _series_last_and_deltas(df, windows_days=[1])
    
    assert last == 105.0
    # d1 target was 2024-01-07. Nearest is 2024-01-05 (val 100)
    # Delta = 105 - 100 = 5
    assert deltas[1] == 5.0