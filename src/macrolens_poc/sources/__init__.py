"""Provider adapters and source-matrix handling."""

from macrolens_poc.sources.fred import FetchResult as FredFetchResult
from macrolens_poc.sources.fred import fetch_fred_series_observations
from macrolens_poc.sources.matrix import (
    MatrixLoadResult,
    SeriesSpec,
    SourcesMatrix,
    load_sources_matrix,
)
from macrolens_poc.sources.yahoo import FetchResult as YahooFetchResult
from macrolens_poc.sources.yahoo import fetch_yahoo_history

__all__ = [
    "FredFetchResult",
    "YahooFetchResult",
    "fetch_fred_series_observations",
    "fetch_yahoo_history",
    "MatrixLoadResult",
    "SeriesSpec",
    "SourcesMatrix",
    "load_sources_matrix",
]
