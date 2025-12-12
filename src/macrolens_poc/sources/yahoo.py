from __future__ import annotations

from dataclasses import dataclass
from datetime import date
import time
from typing import Optional

import pandas as pd
import requests
import yfinance as yf


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
    timeout_s: float = 10.0,
    max_attempts: int = 3,
    backoff_factor: float = 1.5,
) -> FetchResult:
    """Fetch historical daily prices from Yahoo Finance via yfinance.

    Uses [`yfinance.download()`](/ranaroussi/yfinance:download) under the hood.

    Returns a DataFrame with columns:
      - date (timezone-aware UTC Timestamp)
      - value (float)  # Close

    Notes:
    - yfinance returns index as DatetimeIndex.
    - We normalize to UTC and pick Close.
    - Retry/backoff (max_attempts, backoff_factor) is applied to network errors/timeouts.
    """

    df = None
    last_error: Optional[str] = None
    attempts = max(1, max_attempts)

    for attempt in range(1, attempts + 1):
        try:
            df = yf.download(
                symbol,
                start=start,
                end=end,
                interval=interval,
                progress=False,
                timeout=timeout_s,
            )
        except requests.Timeout as exc:
            last_error = f"code=timeout; detail={exc}"
        except Exception as exc:  # yfinance can raise various runtime exceptions
            last_error = f"code=download_failed; detail={exc}"
        else:
            break

        if attempt < attempts:
            sleep_s = backoff_factor ** (attempt - 1)
            time.sleep(sleep_s)
        else:
            return FetchResult(status="error", message=last_error or "code=unknown_error", data=None)

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
