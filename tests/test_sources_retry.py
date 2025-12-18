from __future__ import annotations

from datetime import date

import pandas as pd
import requests

from macrolens_poc.sources import fred, yahoo


class _DummyResponse:
    def __init__(self, *, status_code: int = 200, payload: dict | None = None, text: str = "") -> None:
        self.status_code = status_code
        self._payload = payload or {}
        self.text = text

    def json(self):  # type: ignore[override]
        return self._payload

    def raise_for_status(self) -> None:  # mimic requests.Response
        return None


def test_fetch_fred_retries_on_timeout(monkeypatch) -> None:
    # Keep unit tests fast/deterministic: disable actual sleeping in retry backoff.
    monkeypatch.setattr(fred.retry_call.__globals__["time"], "sleep", lambda *_: None)
    payload = {"observations": [{"date": "2020-01-01", "value": "1.0"}]}
    calls: list[int] = []

    def _fake_get(*_, **__):
        calls.append(1)
        if len(calls) < 2:
            raise requests.Timeout("network timeout")
        return _DummyResponse(payload=payload)

    monkeypatch.setattr(fred.requests, "get", _fake_get)

    result = fred.fetch_fred_series_observations(
        series_id="SERIES",
        api_key="dummy",
        observation_start=date(2020, 1, 1),
        observation_end=None,
        timeout_s=0.1,
        max_attempts=2,
    )

    assert len(calls) == 2
    assert result.status == "ok"
    assert result.data is not None and not result.data.empty


def test_fetch_fred_timeout_exhausted(monkeypatch) -> None:
    monkeypatch.setattr(fred.retry_call.__globals__["time"], "sleep", lambda *_: None)
    def _always_timeout(*_, **__):
        raise requests.Timeout("hard timeout")

    monkeypatch.setattr(fred.requests, "get", _always_timeout)

    result = fred.fetch_fred_series_observations(
        series_id="SERIES",
        api_key="dummy",
        observation_start=date(2020, 1, 1),
        observation_end=None,
        timeout_s=0.1,
        max_attempts=2,
    )

    assert result.status == "error"
    assert result.error_type == "Timeout"
    assert "hard timeout" in (result.error_message or "")


def test_fetch_yahoo_retries_download(monkeypatch) -> None:
    monkeypatch.setattr(yahoo.retry_call.__globals__["time"], "sleep", lambda *_: None)
    calls: list[int] = []

    def _fake_history(*_, **__):
        calls.append(1)
        if len(calls) < 2:
            raise requests.Timeout("download timeout")
        return pd.DataFrame({"Close": [1.0]}, index=pd.date_range("2020-01-01", periods=1))

    class MockTicker:
        def __init__(self, *args, **kwargs):
            pass

        def history(self, *args, **kwargs):
            return _fake_history(*args, **kwargs)

    monkeypatch.setattr(yahoo.yf, "Ticker", MockTicker)

    result = yahoo.fetch_yahoo_history(
        symbol="AAPL",
        start=date(2020, 1, 1),
        end=None,
        interval="1d",
        timeout_s=0.1,
        max_attempts=2,
    )

    assert len(calls) == 2
    assert result.status == "ok"
    assert result.data is not None and not result.data.empty


def test_fetch_yahoo_timeout_exhausted(monkeypatch) -> None:
    monkeypatch.setattr(yahoo.retry_call.__globals__["time"], "sleep", lambda *_: None)

    def _always_timeout(*_, **__):
        raise requests.Timeout("download timeout")

    class MockTicker:
        def __init__(self, *args, **kwargs):
            pass

        def history(self, *args, **kwargs):
            return _always_timeout(*args, **kwargs)

    monkeypatch.setattr(yahoo.yf, "Ticker", MockTicker)

    result = yahoo.fetch_yahoo_history(
        symbol="AAPL",
        start=date(2020, 1, 1),
        end=None,
        interval="1d",
        timeout_s=0.1,
        max_attempts=2,
    )

    assert result.status == "error"
    assert result.error_type == "Timeout"
    assert "download timeout" in (result.error_message or "")
