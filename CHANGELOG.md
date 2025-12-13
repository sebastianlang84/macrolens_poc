# Changelog

Alle nennenswerten Änderungen an diesem Projekt werden in dieser Datei dokumentiert.

Das Format orientiert sich an **Keep a Changelog** und **Semantic Versioning**:

- https://keepachangelog.com/en/1.1.0/
- https://semver.org/

## [Unreleased]

### Added
- Pipeline: `last_observation_date` und `run_at` im `SeriesRunResult` und `series_run` Event.
- Yahoo Source: `timeout_s` Parameter für `fetch_yahoo_history` (Default: 10.0s).

## [0.1.0] - 2025-12-12

### Added
- Repo-/Paket-Skeleton (Python-Projekt + Packaging).
- CLI-Skeleton (Typer-App) mit `run-all`, `run-one`, `report`.
- Konfig-Templates (`.env.example`, `config/config.example.yaml`).
- Structured Logging (JSONL).
- Provider Adapter: FRED, Yahoo Finance (yfinance).
- Pipeline: Fetch → Normalize → Store (Parquet).
- SQLite Metadaten-Index.
- Report-Generation (Markdown + JSON).
- Tests für kritische Logik (Storage, Retry, Matrix-Status).

### Changed
- Provider-Fetcher robuster (Timeout, Retry/Backoff).
- Revisionsdaten-Detektion beim Storage-Merge.
- Refactoring: Report-Implementierung konsolidiert.
- Tooling: Task-Runner standardisiert auf `Makefile`.
- Docs: Konsolidierung von [`README.md`](README.md:1) und [`AGENTS.md`](AGENTS.md:1) (Single Source of Truth).
- Docs: Cleanup [`PRD.md`](PRD.md:1) (Entfernung veralteter TODOs).

### Fixed
- Yahoo/yfinance: `TypeError` Handling und Regression-Tests.
- Config: Laden nur der lokalen `.env`.
- Tests: Stabilisierung nicht-deterministischer Tests.
