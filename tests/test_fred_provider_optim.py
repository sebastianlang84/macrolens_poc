from datetime import date, timedelta

import pandas as pd

from macrolens_poc.sources.fred import fetch_fred_series_observations


def test_fred_lookback_buffer(monkeypatch):
    captured_params = {}

    class MockResponse:
        def __init__(self):
            self.status_code = 200

        def json(self):
            return {"observations": []}

        def raise_for_status(self):
            pass

    def mock_get(url, params=None, **kwargs):
        nonlocal captured_params
        captured_params = params
        return MockResponse()

    monkeypatch.setattr("requests.get", mock_get)

    start_date = date(2023, 1, 1)
    fetch_fred_series_observations(series_id="TEST", api_key="fake", observation_start=start_date)

    # Expected: 2023-01-01 minus 90 days
    expected_start = (start_date - timedelta(days=90)).isoformat()
    assert captured_params["observation_start"] == expected_start


def test_fred_error_fields(monkeypatch):
    def mock_get_fail(*args, **kwargs):
        # We need to mock retry_call or make it fail fast
        raise RuntimeError("network down")

    # Mocking requests.get inside the retry loop
    monkeypatch.setattr("requests.get", mock_get_fail)

    result = fetch_fred_series_observations(series_id="TEST", api_key="fake", max_attempts=1)

    assert result.status == "error"
    assert result.error_type == "RuntimeError"
    assert "network down" in result.error_message


def test_fred_empty_df_columns(monkeypatch):
    class MockResponse:
        def __init__(self):
            self.status_code = 200

        def json(self):
            return {"observations": []}

        def raise_for_status(self):
            pass

    monkeypatch.setattr("requests.get", lambda *args, **kwargs: MockResponse())

    result = fetch_fred_series_observations(series_id="TEST", api_key="fake")

    assert result.status == "warn"
    assert isinstance(result.data, pd.DataFrame)
    assert list(result.data.columns) == ["date", "value"]
