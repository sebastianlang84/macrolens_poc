from __future__ import annotations

from datetime import date, datetime, timezone
from unittest.mock import MagicMock, patch

import pytest

from macrolens_poc.config import Settings
from macrolens_poc.pipeline.run_series import run_series
from macrolens_poc.sources.matrix import SeriesSpec


@pytest.fixture
def mock_settings(tmp_path):
    s = MagicMock(spec=Settings)
    s.fred_api_key = "fake_key"
    s.paths = MagicMock()
    s.paths.data_dir = tmp_path / "data"
    return s


@pytest.fixture
def mock_spec():
    return SeriesSpec(
        id="test_series",
        provider="fred",
        provider_symbol="TEST",
        category="test",
        frequency_target="D",
        timezone="UTC",
        units="idx",
        transform="none",
        notes="",
        enabled=True,
    )


@patch("macrolens_poc.pipeline.run_series.fetch_fred_series_observations")
def test_run_series_uses_as_of_date(mock_fetch, mock_settings, mock_spec):
    """Verify that as_of_date is passed as observation_end to the provider."""

    # Setup
    as_of = date(2023, 1, 1)
    mock_fetch.return_value = MagicMock(data=None, status="ok", message="ok")

    # Execute
    as_of_dt = datetime.combine(as_of, datetime.min.time()).replace(tzinfo=timezone.utc)
    run_series(
        settings=mock_settings,
        spec=mock_spec,
        lookback_days=10,
        as_of=as_of_dt,
    )

    # Verify
    mock_fetch.assert_called_once()
    call_kwargs = mock_fetch.call_args.kwargs
    assert call_kwargs["observation_end"] == as_of
    assert call_kwargs["observation_start"] == date(2022, 12, 22)  # 2023-01-01 - 10 days


@patch("macrolens_poc.pipeline.run_series.fetch_fred_series_observations")
def test_run_series_defaults_to_utc_today(mock_fetch, mock_settings, mock_spec):
    """Verify that without as_of_date, it defaults to UTC today."""

    # Setup
    mock_fetch.return_value = MagicMock(data=None, status="ok", message="ok")
    expected_today = datetime.now(timezone.utc).date()

    # Execute
    run_series(
        settings=mock_settings,
        spec=mock_spec,
        lookback_days=10,
        as_of=None,
    )

    # Verify
    mock_fetch.assert_called_once()
    call_kwargs = mock_fetch.call_args.kwargs
    assert call_kwargs["observation_end"] == expected_today
