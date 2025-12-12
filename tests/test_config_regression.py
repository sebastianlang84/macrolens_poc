from pathlib import Path
import pytest
from macrolens_poc.sources.matrix import load_sources_matrix

def test_sources_matrix_config_validity():
    """
    Regression test to ensure config/sources_matrix.yaml is valid, parseable,
    and contains a non-empty list of series.
    """
    config_path = Path("config/sources_matrix.yaml")
    
    # Ensure the file exists (it should in the repo)
    assert config_path.exists(), f"Configuration file not found at {config_path}"
    
    # Attempt to load and parse
    try:
        result = load_sources_matrix(config_path)
    except Exception as e:
        pytest.fail(f"Failed to load sources matrix: {e}")
        
    # Verify structure
    matrix = result.matrix
    assert matrix.version >= 1, "Version should be at least 1"
    assert len(matrix.series) > 0, "Sources matrix should contain at least one series"
    
    # Verify some expected series are present (sanity check)
    ids = [s.id for s in matrix.series]
    assert "us_cpi" in ids, "Expected 'us_cpi' to be in sources matrix"
    assert "sp500" in ids, "Expected 'sp500' to be in sources matrix"
    
    # Verify sorting (since we just implemented it)
    assert ids == sorted(ids), "Series should be sorted by ID after loading"