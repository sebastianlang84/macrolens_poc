from __future__ import annotations

from datetime import datetime
from typing import Optional

import pandas as pd

DEFAULT_STALE_THRESHOLD_DAYS = 3


def compute_data_age_days(*, last_date: Optional[pd.Timestamp], now: datetime) -> Optional[int]:
    """Return age of the latest data point in whole days.

    Returns None when last_date is missing/NaN. The calculation is done in UTC to
    avoid timezone drift between stored data and the reference time.
    """

    if last_date is None or pd.isna(last_date):
        return None

    normalized_last = pd.to_datetime(last_date, utc=True)
    normalized_now = pd.to_datetime(now, utc=True)

    return int((normalized_now - normalized_last).days)


def is_stale(
    *, last_date: Optional[pd.Timestamp], now: datetime, threshold_days: int = DEFAULT_STALE_THRESHOLD_DAYS
) -> bool:
    age_days = compute_data_age_days(last_date=last_date, now=now)
    return age_days is not None and age_days > threshold_days

