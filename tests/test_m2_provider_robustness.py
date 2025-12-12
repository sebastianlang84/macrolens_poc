from __future__ import annotations

import importlib

from macrolens_poc.config import Settings
from macrolens_poc.pipeline.run_series import run_series
from macrolens_poc.sources.matrix import SeriesSpec

run_series_module = importlib.import_module("macrolens_poc.pipeline.run_series")


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
