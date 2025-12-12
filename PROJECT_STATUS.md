# Project Status (Snapshot)

## Overview
- Milestone M1/M2 goals met: ingestion pipeline for enabled sources via CLI, normalization, and Parquet storage are in place (see README scope and CLI usage).
- Current providers: FRED (`fetch_fred_series_observations`) and Yahoo Finance via `yfinance` (`fetch_yahoo_history`).
- CLI commands `run-all` and `run-one` execute pipeline runs with structured JSONL logging and per-series summaries.
- Configuration relies on `.env`/YAML for timezones and keys; storage/paths are centralized in `Settings`.

## Observations
- Reporting command is a stub: `cli report` logs only a start/summary event and does not generate artifacts.
- Provider robustness gaps remain: no timeout/retry/backoff and no revision-overwrite policy for sources with backfilled changes.
- Matrix metadata still lacks automatic status fields like `last_ok`/`status`.
- Storage path layout is fixed to `data/series/{id}.parquet` without partitioning or metadata index.

## Suggested Next Steps
- Implement basic retry/backoff around provider fetches and capture HTTP/provider error metadata in logs.
- Extend matrix loader to track `last_ok` and derive series health from run outcomes; export a matrix status view.
- Flesh out `report` command with aggregator logic (last value plus Δ windows) and Markdown/JSON outputs under `reports/`.
- Add revision-aware storage policy for datasets with historical restatements to prevent silent overwrites.
- Introduce a lightweight index (e.g., SQLite or manifest) to query available series and their update timestamps.
