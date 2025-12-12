from __future__ import annotations

from pathlib import Path

from macrolens_poc.sources.matrix import load_sources_matrix


def test_load_sources_matrix_ok() -> None:
    path = Path("config/sources_matrix.yaml")
    result = load_sources_matrix(path)

    assert result.path == path
    assert result.matrix.version == 1
    assert len(result.matrix.series) >= 10
    assert any(s.provider == "fred" for s in result.matrix.series)
    assert any(s.provider == "yfinance" for s in result.matrix.series)
