from __future__ import annotations

from dataclasses import dataclass
from datetime import date
import time
from typing import Optional

import pandas as pd
import requests
import yfinance as yf

from macrolens_poc.retry_utils import RetryConfig, retry_call


@dataclass(frozen=True)
class FetchResult:
    status: str  # ok/warn/error/missing
    message: str
    data: Optional[pd.DataFrame]


def fetch_yahoo_history(
    *,
    symbol: str,
    start: Optional[date] = None,
    end: Optional[date] = None,
    interval: str = "1d",
    max_attempts: int = 3,
) -> FetchResult:
    """Fetch historical daily prices from Yahoo Finance via yfinance.

    Uses [`yfinance.download()`](/ranaroussi/yfinance:download) under the hood.

    Returns a DataFrame with columns:
      - date (timezone-aware UTC Timestamp)
      - value (float)  # Close

    Notes:
    - yfinance returns index as DatetimeIndex.
    - We normalize to UTC and pick Close.
    - Provider robustness: retry + exponential backoff on transient failures.
    """

    def _download() -> pd.DataFrame:
        return yf.download(symbol, start=start, end=end, interval=interval, progress=False)

    try:
        df = retry_call(
            _download,
            cfg=RetryConfig(max_attempts=max_attempts, base_delay_s=0.5, max_delay_s=8.0, multiplier=2.0),
            should_retry=lambda exc: True,
        )
    except Exception as exc:  # yfinance can raise various runtime exceptions
        return FetchResult(status="error", message=f"yfinance download failed: {type(exc).__name__}: {exc}", data=None)

    if df is None or df.empty:
        return FetchResult(status="warn", message="yfinance returned 0 rows", data=pd.DataFrame(columns=["date", "value"]))

    # typical columns: Open High Low Close Adj Close Volume
    if "Close" not in df.columns:
        return FetchResult(status="error", message="yfinance missing Close column", data=None)

    out = df[["Close"]].copy()
    out = out.rename(columns={"Close": "value"})

    out = out.reset_index()  # index becomes a column: Date
    date_col = "Date" if "Date" in out.columns else out.columns[0]
    out = out.rename(columns={date_col: "date"})

    out["date"] = pd.to_datetime(out["date"], utc=True)
    out = out[["date", "value"]].sort_values("date")

    return FetchResult(status="ok", message="ok", data=out)
