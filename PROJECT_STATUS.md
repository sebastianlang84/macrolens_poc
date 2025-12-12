# Project Status (Snapshot)

## Overview
- Milestone M1/M2 goals met: ingestion pipeline for enabled sources via CLI, normalization, and Parquet storage are in place (see README scope and CLI usage).
- Current providers: FRED (`fetch_fred_series_observations`) and Yahoo Finance via `yfinance` (`fetch_yahoo_history`).
- CLI commands `run-all` and `run-one` execute pipeline runs with structured JSONL logging and per-series summaries.
- Configuration relies on `.env`/YAML for timezones and keys; storage/paths are centralized in `Settings`.

## Context & Decisions
- Data provider continuity needs a plan before further build-out.
- Additional coverage (regions/series) should align with reporting and storage constraints.

| Topic | Status | Next Step | Owner |
| --- | --- | --- | --- |
| Yahoo Finance dependency | Reliant on `yfinance`; no SLA and occasional blocking/changes. | Evaluate replacement provider (e.g., Polygon/Alphavantage) and prototype adapter with retry/backoff hooks. | @owner-product |
| Coverage expansion (regions/series) | Current matrix limited to enabled US macro series. | Define target regions/series list and storage impact; add to config matrix with `status`/`last_ok` fields. | @owner-data |

## Open Questions
- Welche Yahoo-Alternative priorisieren wir für Equity/FX/Commodities (Kosten, Limits, SLA)?
- Welche zusätzlichen Regionen/Serien sind für den nächsten Increment verbindlich (EU/UK/JP; Rates vs. Equities)?

## Observations
- Reporting command generates Markdown/JSON artifacts with last values and Δ windows, but risk flags remain TODO.
- Provider robustness gaps remain: no timeout/retry/backoff and no revision-overwrite policy for sources with backfilled changes.
- Matrix metadata still lacks automatic status fields like `last_ok`/`status`.
- Storage path layout is fixed to `data/series/{id}.parquet` without partitioning or metadata index.

## Suggested Next Steps
- Implement basic retry/backoff around provider fetches and capture HTTP/provider error metadata in logs.
- Extend matrix loader to track `last_ok` and derive series health from run outcomes; export a matrix status view.
- Add risk-flag heuristics to the report output and include contextual metadata (category/units).
- Add revision-aware storage policy for datasets with historical restatements to prevent silent overwrites.
- Introduce a lightweight index (e.g., SQLite or manifest) to query available series and their update timestamps.

## Review Cadence
- Wöchentliches Update der offenen Fragen/Entscheidungen im Planning; Kurz-Check im Standup bis Klarheit zu Provider- und Coverage-Entscheidungen.
