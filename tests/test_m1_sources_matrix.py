from __future__ import annotations

from pathlib import Path

from macrolens_poc.sources.matrix import load_sources_matrix


def test_load_sources_matrix_ok() -> None:
    path = Path("config/sources_matrix.yaml")
    result = load_sources_matrix(path)

    assert result.path == path
    assert result.matrix.version == 1
    assert len(result.matrix.series) >= 10

    # Create a dict for deterministic lookups
    series_by_id = {s.id: s for s in result.matrix.series}

    # Check specific series to ensure correct loading regardless of order
    assert "us_cpi" in series_by_id
    assert series_by_id["us_cpi"].provider == "fred"
    assert series_by_id["us_cpi"].provider_symbol == "CPIAUCSL"

    assert "sp500" in series_by_id
    assert series_by_id["sp500"].provider == "yfinance"
    assert series_by_id["sp500"].provider_symbol == "^GSPC"

    # Verify the list is sorted by ID
    ids = [s.id for s in result.matrix.series]
    assert ids == sorted(ids), "Series list must be sorted by ID for determinism"
