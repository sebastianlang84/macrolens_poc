from __future__ import annotations

import importlib

from macrolens_poc.config import Settings
from macrolens_poc.pipeline.run_series import run_series
from macrolens_poc.sources.matrix import SeriesSpec

run_series_module = importlib.import_module("macrolens_poc.pipeline.run_series")
yahoo_module = importlib.import_module("macrolens_poc.sources.yahoo")


def test_run_series_catches_provider_exception_and_returns_error(monkeypatch) -> None:
    def boom(**_kwargs):  # type: ignore[no-untyped-def]
        raise RuntimeError("boom")

    monkeypatch.setattr(run_series_module, "fetch_fred_series_observations", boom)

    settings = Settings()
    spec = SeriesSpec(id="x", provider="fred", provider_symbol="X", category="test", enabled=True)

    result = run_series(settings=settings, spec=spec, lookback_days=10)

    assert result.status == "error"
    assert result.message == "provider fetch failed"
    assert result.error_type == "RuntimeError"
    assert result.error_message == "boom"


def test_run_series_catches_provider_exception_for_yfinance(monkeypatch) -> None:
    def boom(**_kwargs):  # type: ignore[no-untyped-def]
        raise ValueError("nope")

    monkeypatch.setattr(run_series_module, "fetch_yahoo_history", boom)

    settings = Settings()
    spec = SeriesSpec(id="x", provider="yfinance", provider_symbol="SPY", category="test", enabled=True)

    result = run_series(settings=settings, spec=spec, lookback_days=10)

    assert result.status == "error"
    assert result.message == "provider fetch failed"
    assert result.error_type == "ValueError"
    assert result.error_message == "nope"


def test_run_series_yfinance_typeerror_is_captured_and_surfaces_error_fields(monkeypatch) -> None:
    """Regression: yfinance sometimes raises TypeError; we must not crash and must log error details."""

    def no_retry(fn, **_kwargs):  # type: ignore[no-untyped-def]
        return fn()

    def yfinance_boom(*_args, **_kwargs):  # type: ignore[no-untyped-def]
        raise TypeError("arg must be a list, tuple, 1-d array, or Series")

    # Avoid real sleeps from retry/backoff in unit tests.
    monkeypatch.setattr(yahoo_module, "retry_call", no_retry)
    monkeypatch.setattr(yahoo_module.yf, "download", yfinance_boom)

    settings = Settings()
    spec = SeriesSpec(id="x", provider="yfinance", provider_symbol="SPY", category="test", enabled=True)

    result = run_series(settings=settings, spec=spec, lookback_days=10)

    assert result.status in {"warn", "error"}
    assert result.error_type == "TypeError"
    assert "arg must be a list" in (result.error_message or "")
