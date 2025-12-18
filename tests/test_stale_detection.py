import importlib
from datetime import date, datetime, timezone
from unittest.mock import MagicMock

import pandas as pd
import pytest

from macrolens_poc.config import Settings
from macrolens_poc.pipeline.run_series import run_series
from macrolens_poc.sources.matrix import SeriesSpec
from macrolens_poc.sources.matrix_status import (
    MatrixStatusFile,
    SeriesStatusEntry,
    identify_stale_series,
)

# Get the module object explicitly to avoid shadowing by the function in __init__
run_series_module = importlib.import_module("macrolens_poc.pipeline.run_series")


@pytest.fixture
def mock_settings(tmp_path):
    s = Settings()
    s.paths.data_dir = tmp_path / "data"
    s.stale_days_default = 5
    return s


def test_stale_detection_ok(mock_settings, monkeypatch):
    """Test that fresh data is OK."""

    # Mock fetch to return data from yesterday
    ref_date = date(2025, 1, 10)
    last_obs = date(2025, 1, 9)  # 1 day ago -> OK

    mock_fetch = MagicMock()
    mock_fetch.return_value.status = "ok"
    mock_fetch.return_value.data = pd.DataFrame({"date": [last_obs], "value": [100.0]})

    # Patch fetch_fred (assuming provider=fred)
    monkeypatch.setattr(run_series_module, "fetch_fred_series_observations", mock_fetch)

    spec = SeriesSpec(id="test_ok", provider="fred", provider_symbol="T1", category="test")

    as_of_dt = datetime.combine(ref_date, datetime.min.time()).replace(tzinfo=timezone.utc)
    result = run_series(settings=mock_settings, spec=spec, as_of=as_of_dt)

    assert result.status == "ok"
    assert result.message == "ok"


def test_identify_stale_series_logic():
    """Test the standalone stale identification logic."""
    ref_date = date(2025, 1, 10)

    status_file = MatrixStatusFile(
        series={
            "fresh": SeriesStatusEntry(
                status="ok",
                last_observation_date="2025-01-09",  # 1 day ago
            ),
            "stale_default": SeriesStatusEntry(
                status="ok",
                last_observation_date="2025-01-01",  # 9 days ago
            ),
            "stale_override": SeriesStatusEntry(
                status="ok",
                last_observation_date="2025-01-05",  # 5 days ago
            ),
        }
    )

    # Default threshold 7
    # overrides: stale_override has threshold 2
    stale = identify_stale_series(
        status_file=status_file,
        ref_date=ref_date,
        default_threshold=7,
        overrides={"stale_override": 2},
    )

    stale_ids = [s["series_id"] for s in stale]
    assert "stale_default" in stale_ids
    assert "stale_override" in stale_ids
    assert "fresh" not in stale_ids

    # Check details
    stale_map = {s["series_id"]: s for s in stale}
    assert stale_map["stale_default"]["delta_days"] == 9
    assert stale_map["stale_override"]["delta_days"] == 5


def test_stale_detection_warn(mock_settings, monkeypatch):
    """Test that stale data triggers warning."""

    # Mock fetch to return data from 10 days ago (default threshold 5)
    ref_date = date(2025, 1, 10)
    last_obs = date(2025, 1, 1)  # 9 days ago -> Stale

    mock_fetch = MagicMock()
    mock_fetch.return_value.status = "ok"
    mock_fetch.return_value.data = pd.DataFrame({"date": [last_obs], "value": [100.0]})

    monkeypatch.setattr(run_series_module, "fetch_fred_series_observations", mock_fetch)

    spec = SeriesSpec(id="test_stale", provider="fred", provider_symbol="T2", category="test")

    as_of_dt = datetime.combine(ref_date, datetime.min.time()).replace(tzinfo=timezone.utc)
    result = run_series(settings=mock_settings, spec=spec, as_of=as_of_dt)

    assert result.status == "warn"
    assert "stale" in result.message
    assert "9 days ago" in result.message


def test_stale_detection_override(mock_settings, monkeypatch):
    """Test that stale_days override works."""

    # Mock fetch to return data from 10 days ago
    ref_date = date(2025, 1, 10)
    last_obs = date(2025, 1, 1)  # 9 days ago

    mock_fetch = MagicMock()
    mock_fetch.return_value.status = "ok"
    mock_fetch.return_value.data = pd.DataFrame({"date": [last_obs], "value": [100.0]})

    monkeypatch.setattr(run_series_module, "fetch_fred_series_observations", mock_fetch)

    # Override threshold to 20 days -> should be OK
    spec = SeriesSpec(
        id="test_override", provider="fred", provider_symbol="T3", category="test", stale_days=20
    )

    as_of_dt = datetime.combine(ref_date, datetime.min.time()).replace(tzinfo=timezone.utc)
    result = run_series(settings=mock_settings, spec=spec, as_of=as_of_dt)

    assert result.status == "ok"
    assert result.message == "ok"
