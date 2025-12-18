from __future__ import annotations

from pathlib import Path

from macrolens_poc.sources.matrix import load_sources_matrix


def test_sources_matrix_regression() -> None:
    """Regression test for the production sources matrix.

    Ensures that the matrix:
    1. Can be loaded without errors.
    2. Is sorted by ID (determinism).
    3. Contains all required fields for each series.
    """
    path = Path("config/sources_matrix.yaml")
    result = load_sources_matrix(path)

    # 1. Basic structure
    assert result.matrix.version >= 1
    assert len(result.matrix.series) > 0

    # 2. Deterministic order
    ids = [s.id for s in result.matrix.series]
    assert ids == sorted(ids), "Series must be sorted by ID for deterministic processing"

    # 3. Schema validation (Pydantic already does most of this, but we check key fields)
    for series in result.matrix.series:
        assert series.id, f"Series in {path} missing ID"
        assert series.provider in ["fred", "yfinance"], f"Invalid provider for {series.id}"
        assert series.provider_symbol, f"Missing provider_symbol for {series.id}"
        assert series.category, f"Missing category for {series.id}"
        assert series.frequency_target == "daily", f"PoC only supports daily frequency (series: {series.id})"
        assert series.timezone == "UTC", f"PoC expects UTC (series: {series.id})"


def test_sources_matrix_uniqueness() -> None:
    """Ensure no duplicate IDs exist in the matrix."""
    path = Path("config/sources_matrix.yaml")
    result = load_sources_matrix(path)

    ids = [s.id for s in result.matrix.series]
    assert len(ids) == len(set(ids)), "Duplicate IDs found in sources matrix"
