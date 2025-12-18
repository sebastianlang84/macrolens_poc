from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import date
from typing import Optional

import pandas as pd
import requests
import yfinance as yf

from macrolens_poc.retry_utils import RetryConfig, retry_call

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class FetchResult:
    status: str  # ok/warn/error/missing
    message: str
    data: Optional[pd.DataFrame]
    error_type: Optional[str] = None
    error_message: Optional[str] = None


def fetch_yahoo_history(
    *,
    symbol: str,
    start: Optional[date] = None,
    end: Optional[date] = None,
    interval: str = "1d",
    timeout_s: float = 10.0,
    max_attempts: int = 3,
) -> FetchResult:
    """Fetch historical daily prices from Yahoo Finance via yfinance.

    Uses `yfinance.Ticker(...).history()` under the hood.

    Returns a DataFrame with columns:
      - date (timezone-aware UTC Timestamp)
      - value (float)  # Close

    Notes:
    - yfinance returns index as DatetimeIndex.
    - We normalize to UTC and pick Close.
    - Provider robustness: retry + exponential backoff on transient failures.
    """

    def _download() -> pd.DataFrame:
        # Use Ticker.history which is often more robust.
        # Note: We do NOT inject a custom session anymore, as newer yfinance versions (>=0.2.66)
        # use curl_cffi internally to handle TLS fingerprinting and avoid 429s.
        # Injecting a standard requests.Session breaks this mechanism.
        ticker = yf.Ticker(symbol)

        # Ensure start/end are strings to avoid potential type issues in yfinance/pandas
        # some versions of yfinance/pandas have issues with date objects in certain contexts
        s_str = start.strftime("%Y-%m-%d") if start else None
        e_str = end.strftime("%Y-%m-%d") if end else None

        return ticker.history(
            start=s_str,
            end=e_str,
            interval=interval,
            auto_adjust=False,  # Explicitly set to suppress FutureWarnings
            back_adjust=False,
            actions=False,  # We only need prices
            timeout=float(timeout_s),
        )

    def _on_retry(attempt: int, exc: Exception, delay_s: float) -> None:
        logger.warning(
            "Retry attempt %d/%d for %s after error: %s. Waiting %.1fs.",
            attempt,
            max_attempts,
            symbol,
            exc,
            delay_s,
        )

    def _should_retry(exc: Exception) -> bool:
        # Transient errors (network, timeout, etc.)
        if isinstance(
            exc,
            (
                requests.exceptions.ConnectionError,
                requests.exceptions.Timeout,
                requests.exceptions.ChunkedEncodingError,
                ConnectionError,
                TimeoutError,
            ),
        ):
            return True

        # Handle HTTP errors
        if isinstance(exc, requests.exceptions.HTTPError):
            # Retry server errors (5xx), fail on client errors (4xx)
            if exc.response is not None and 400 <= exc.response.status_code < 500:
                return False
            return True

        # Generic RequestException (other network issues)
        if isinstance(exc, requests.exceptions.RequestException):
            return True

        # Explicitly DO NOT retry on TypeError, ValueError, IndexError, KeyError
        # These are likely data/schema issues (e.g. yfinance API changes)
        if isinstance(exc, (TypeError, ValueError, IndexError, KeyError)):
            return False

        # Fail fast on everything else by default to avoid infinite loops on logic errors
        return False

    try:
        df = retry_call(
            _download,
            cfg=RetryConfig(max_attempts=max_attempts, base_delay_s=0.5, max_delay_s=8.0, multiplier=2.0),
            should_retry=_should_retry,
            on_retry=_on_retry,
        )
    except TypeError as exc:
        # Regression: observed in the wild (TODO/PROJECT_STATUS). Treat as non-fatal provider error.
        return FetchResult(
            status="error",
            message=f"yfinance download failed: {type(exc).__name__}: {exc}",
            data=None,
            error_type=type(exc).__name__,
            error_message=str(exc),
        )
    except Exception as exc:  # yfinance can raise various runtime exceptions
        return FetchResult(
            status="error",
            message=f"yfinance download failed: {type(exc).__name__}: {exc}",
            data=None,
            error_type=type(exc).__name__,
            error_message=str(exc),
        )

    if df is None or df.empty:
        return FetchResult(
            status="warn", message="yfinance returned 0 rows", data=pd.DataFrame(columns=["date", "value"])
        )

    # Handle MultiIndex columns (Price, Ticker) - common in newer yfinance
    if isinstance(df.columns, pd.MultiIndex):
        try:
            # Attempt to extract data for the requested symbol
            if df.columns.nlevels > 1 and symbol in df.columns.get_level_values(1):
                df = df.xs(symbol, axis=1, level=1)
        except Exception:
            pass

        # If still MultiIndex, try to flatten or drop levels if possible
        if isinstance(df.columns, pd.MultiIndex):
            # If we have a 'Close' in level 0, we might need to select it carefully
            if "Close" in df.columns.get_level_values(0):
                # Select all columns where level 0 is Close
                close_cols = df.xs("Close", axis=1, level=0, drop_level=True)
                if not close_cols.empty:
                    # If multiple columns remain (multiple tickers?), pick the first one
                    # or the one matching symbol
                    if symbol in close_cols.columns:
                        df = close_cols[[symbol]]
                    else:
                        df = close_cols.iloc[:, [0]]
                    # Now df is single-level (Ticker) or Series-like.
                    # We want to rename it to 'value' later.
                    df.columns = ["Close"]  # Normalize to expected name

    # typical columns: Open High Low Close Adj Close Volume
    # Check if "Close" is in columns (single level)
    if "Close" not in df.columns:
        # If we have 'Adj Close' but no 'Close', use that as fallback
        if "Adj Close" in df.columns:
            df = df.rename(columns={"Adj Close": "Close"})
        else:
            return FetchResult(
                status="error",
                message=f"yfinance missing Close column. Columns: {list(df.columns)}",
                data=None,
                error_type="ColumnNotFoundError",
                error_message=f"Required column 'Close' not found in {list(df.columns)}",
            )

    # Extract Close column safely
    # Ensure we get a DataFrame with single level columns, not a Series, not MultiIndex
    try:
        # Use .loc to be explicit and avoid SettingWithCopy issues
        out = df.loc[:, ["Close"]].copy()
    except Exception as exc:
        # Fallback for edge cases (e.g. if Close is a Series for some reason)
        logger.debug("Fallback extraction for Close column due to: %s", exc)
        out = pd.DataFrame(df["Close"]).copy()
        out.columns = ["Close"]

    # Flatten columns if they are still MultiIndex (should not happen if logic above worked, but be safe)
    if isinstance(out.columns, pd.MultiIndex):
        out.columns = out.columns.get_level_values(0)

    out = out.rename(columns={"Close": "value"})

    out = out.reset_index()  # index becomes a column: Date

    # Identify date column
    if "Date" in out.columns:
        date_col = "Date"
    elif "index" in out.columns:
        date_col = "index"
    else:
        date_col = out.columns[0]

    out = out.rename(columns={date_col: "date"})

    # Ensure date is 1-d array/Series before to_datetime
    if isinstance(out["date"], pd.DataFrame):
        # This happens if we have duplicate columns named 'date' or similar mess
        out = out.loc[:, ~out.columns.duplicated()]
        if isinstance(out["date"], pd.DataFrame):
            # Still a DataFrame? Take first column
            out["date"] = out["date"].iloc[:, 0]

    try:
        out["date"] = pd.to_datetime(out["date"], utc=True)
    except Exception as exc:
        return FetchResult(
            status="error",
            message=f"date conversion failed: {exc}",
            data=None,
            error_type=type(exc).__name__,
            error_message=str(exc),
        )

    out["value"] = pd.to_numeric(out["value"], errors="coerce")
    out = out[["date", "value"]].sort_values("date")

    return FetchResult(status="ok", message="ok", data=out)
