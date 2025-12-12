"""Pipeline orchestration (fetch → normalize → store → validate)."""

from macrolens_poc.pipeline.run_series import SeriesRunResult, run_series

__all__ = ["SeriesRunResult", "run_series"]
