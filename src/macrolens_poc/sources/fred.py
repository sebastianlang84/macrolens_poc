from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from typing import Any, Dict, Optional

import pandas as pd
import requests

from macrolens_poc.retry_utils import RetryConfig, retry_call


@dataclass(frozen=True)
class FetchResult:
    status: str  # ok/warn/error/missing
    message: str
    data: Optional[pd.DataFrame]
    error_type: Optional[str] = None
    error_message: Optional[str] = None


class RetryableHttpStatus(Exception):
    def __init__(self, status_code: int) -> None:
        super().__init__(f"retryable http status: {status_code}")
        self.status_code = status_code


def fetch_fred_series_observations(
    *,
    series_id: str,
    api_key: Optional[str],
    observation_start: Optional[date] = None,
    observation_end: Optional[date] = None,
    timeout_s: float = 20.0,
    max_attempts: int = 3,
) -> FetchResult:
    """Fetch observations from FRED.

    Endpoint: https://api.stlouisfed.org/fred/series/observations

    Returns a DataFrame with columns:
      - date (timezone-aware UTC Timestamp)
      - value (float)

    Notes:
    - FRED may return "." for missing values.
    - We use file_type=json.
    - Provider robustness: retry + exponential backoff on transient failures.
    - Lookback buffer: we add 90 days to observation_start to ensure we have
      enough data points for delta calculations (e.g. for monthly/quarterly series).
    """

    if not api_key:
        # Fallback: try env var directly if not passed
        import os

        api_key = os.getenv("FRED_API_KEY")

    if not api_key:
        return FetchResult(status="missing", message="FRED_API_KEY missing (checked arg and env)", data=None)

    url = "https://api.stlouisfed.org/fred/series/observations"
    params: Dict[str, Any] = {
        "series_id": series_id,
        "api_key": api_key,
        "file_type": "json",
        "sort_order": "asc",
    }
    if observation_start is not None:
        # Lookback buffer: ensure we have enough history for downstream delta windows.
        buffered_start = observation_start - timedelta(days=90)
        params["observation_start"] = buffered_start.isoformat()
    if observation_end is not None:
        params["observation_end"] = observation_end.isoformat()

    retryable_status = {429, 500, 502, 503, 504}

    def _do_request() -> requests.Response:
        # requests' timeout can be (connect, read)
        timeout = (min(5.0, float(timeout_s)), float(timeout_s))
        resp = requests.get(url, params=params, timeout=timeout)

        if resp.status_code == 404:
            return resp

        if resp.status_code in retryable_status:
            raise RetryableHttpStatus(resp.status_code)

        resp.raise_for_status()
        return resp

    def _should_retry(exc: Exception) -> bool:
        if isinstance(exc, RetryableHttpStatus):
            return True
        if isinstance(exc, (requests.Timeout, requests.ConnectionError)):
            return True
        return False

    try:
        resp = retry_call(
            _do_request,
            cfg=RetryConfig(max_attempts=max_attempts, base_delay_s=0.5, max_delay_s=8.0, multiplier=2.0),
            should_retry=_should_retry,
        )
    except Exception as exc:
        return FetchResult(
            status="error",
            message=f"FRED request failed: {type(exc).__name__}: {exc}",
            data=None,
            error_type=type(exc).__name__,
            error_message=str(exc),
        )

    if resp.status_code == 404:
        return FetchResult(status="missing", message=f"FRED series not found: {series_id}", data=None)

    try:
        payload = resp.json()
    except ValueError as exc:
        return FetchResult(
            status="error",
            message=f"FRED invalid JSON: {exc}",
            data=None,
            error_type=type(exc).__name__,
            error_message=str(exc),
        )

    observations = payload.get("observations")
    if not isinstance(observations, list):
        return FetchResult(
            status="error",
            message="FRED response missing observations list",
            data=None,
            error_type="InvalidResponseError",
            error_message="observations is not a list",
        )

    if not observations:
        return FetchResult(
            status="warn",
            message="FRED returned 0 observations",
            data=pd.DataFrame(columns=["date", "value"]),
        )

    rows = []
    for o in observations:
        if not isinstance(o, dict):
            continue
        d = o.get("date")
        v = o.get("value")
        if not d:
            continue
        # value can be '.' meaning missing
        if v is None or v == ".":
            val = float("nan")
        else:
            try:
                val = float(v)
            except (TypeError, ValueError):
                val = float("nan")

        rows.append({"date": d, "value": val})

    df = pd.DataFrame(rows)
    if df.empty:
        return FetchResult(status="warn", message="FRED observations parsed empty", data=df)

    df["date"] = pd.to_datetime(df["date"], utc=True)
    df = df.sort_values("date")

    return FetchResult(status="ok", message="ok", data=df)
