from __future__ import annotations

from dataclasses import dataclass
from datetime import date
import time
from typing import Any, Dict, Optional

import pandas as pd
import requests


@dataclass(frozen=True)
class FetchResult:
    status: str  # ok/warn/error/missing
    message: str
    data: Optional[pd.DataFrame]


def fetch_fred_series_observations(
    *,
    series_id: str,
    api_key: Optional[str],
    observation_start: Optional[date] = None,
    observation_end: Optional[date] = None,
    timeout_s: float = 20.0,
    max_attempts: int = 3,
    backoff_factor: float = 1.5,
) -> FetchResult:
    """Fetch observations from FRED.

    Endpoint: https://api.stlouisfed.org/fred/series/observations

    Returns a DataFrame with columns:
      - date (timezone-aware UTC Timestamp)
      - value (float)

    Notes:
    - FRED may return "." for missing values.
    - We use file_type=json.
    - Retry/backoff (max_attempts, backoff_factor) is applied to network errors/timeouts.
    """

    if api_key is None:
        return FetchResult(status="missing", message="FRED_API_KEY missing", data=None)

    url = "https://api.stlouisfed.org/fred/series/observations"
    params: Dict[str, Any] = {
        "series_id": series_id,
        "api_key": api_key,
        "file_type": "json",
        "sort_order": "asc",
    }
    if observation_start is not None:
        params["observation_start"] = observation_start.isoformat()
    if observation_end is not None:
        params["observation_end"] = observation_end.isoformat()

    resp: Optional[requests.Response] = None
    last_error: Optional[str] = None
    attempts = max(1, max_attempts)

    for attempt in range(1, attempts + 1):
        try:
            resp = requests.get(url, params=params, timeout=timeout_s)
        except requests.Timeout as exc:
            last_error = f"code=timeout; detail={exc}"
        except requests.RequestException as exc:
            last_error = f"code=request_exception; detail={exc}"
        else:
            if resp.status_code == 404:
                return FetchResult(status="missing", message=f"FRED series not found: {series_id}", data=None)
            if 400 <= resp.status_code < 500:
                return FetchResult(
                    status="error",
                    message=f"code=http_error; status={resp.status_code}; detail={resp.text}",
                    data=None,
                )
            if resp.status_code >= 500:
                last_error = f"code=server_error; status={resp.status_code}"
            else:
                break

        if attempt < attempts:
            sleep_s = backoff_factor ** (attempt - 1)
            time.sleep(sleep_s)
        else:
            return FetchResult(status="error", message=last_error or "code=unknown_error", data=None)

    if resp is None:
        return FetchResult(status="error", message=last_error or "code=no_response", data=None)

    try:
        payload = resp.json()
    except ValueError as exc:
        return FetchResult(status="error", message=f"FRED invalid JSON: {exc}", data=None)

    observations = payload.get("observations")
    if not isinstance(observations, list):
        return FetchResult(status="error", message="FRED response missing observations list", data=None)

    if not observations:
        return FetchResult(status="warn", message="FRED returned 0 observations", data=pd.DataFrame(columns=["date", "value"]))

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
