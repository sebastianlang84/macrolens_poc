# Changelog

Alle nennenswerten Änderungen an diesem Projekt werden in dieser Datei dokumentiert.

Das Format orientiert sich an **Keep a Changelog** und **Semantic Versioning**:

- https://keepachangelog.com/en/1.1.0/
- https://semver.org/

## [Unreleased]

### Added

- Repo-/Paket-Skeleton (Python-Projekt + Packaging; siehe [`pyproject.toml`](pyproject.toml:1))
- CLI-Skeleton (Typer-App; siehe [`src/macrolens_poc/cli.py`](src/macrolens_poc/cli.py:1))
- Konfig-Templates für lokale Nutzung (siehe [`.env.example`](.env.example:1) und [`config/config.example.yaml`](config/config.example.yaml:1))
- Logging-Skeleton für strukturierte Logs (siehe [`src/macrolens_poc/logging_utils.py`](src/macrolens_poc/logging_utils.py:1))
- Minimaler Test für Milestone M0 (siehe [`tests/test_m0_skeleton.py`](tests/test_m0_skeleton.py:1))

- Status-Report-Snapshot: [`PROJECT_STATUS.md`](PROJECT_STATUS.md:1)

- Provider (M1/M2 minimal):
  - FRED Fetcher: [`src/macrolens_poc/sources/fred.py`](src/macrolens_poc/sources/fred.py:1)
  - Yahoo Finance Fetcher (yfinance): [`src/macrolens_poc/sources/yahoo.py`](src/macrolens_poc/sources/yahoo.py:1)
- Pipeline (fetch → normalize/dedupe → store): [`src/macrolens_poc/pipeline/run_series.py`](src/macrolens_poc/pipeline/run_series.py:1)
- Parquet Storage (merge ohne Duplikate + new_points): [`src/macrolens_poc/storage/parquet_store.py`](src/macrolens_poc/storage/parquet_store.py:1)
- Tests für Storage-Merge + Normalize: [`tests/test_m2_storage_merge.py`](tests/test_m2_storage_merge.py:1), [`tests/test_m2_pipeline_normalize.py`](tests/test_m2_pipeline_normalize.py:1)
- Report-Generation (Markdown + JSON mit Δ1d/Δ5d/Δ21d pro Serie): [`src/macrolens_poc/report/generate.py`](src/macrolens_poc/report/generate.py:1), CLI `report` in [`src/macrolens_poc/cli.py`](src/macrolens_poc/cli.py:1)
- Tests für Report-Deltas/Artifacts: [`tests/test_report_generate.py`](tests/test_report_generate.py:1)
- Stale-Detection mit neuem Serienstatus (`stale`) inkl. Altersberechnung und Status in Reports: [`src/macrolens_poc/pipeline/status.py`](src/macrolens_poc/pipeline/status.py:1), [`src/macrolens_poc/pipeline/run_series.py`](src/macrolens_poc/pipeline/run_series.py:1), [`src/macrolens_poc/report/generate.py`](src/macrolens_poc/report/generate.py:1)
- Status-Exports (JSON + CSV) für Sources-Matrix/Serienzustände: [`src/macrolens_poc/report/generate.py`](src/macrolens_poc/report/generate.py:1), CLI `report` in [`src/macrolens_poc/cli.py`](src/macrolens_poc/cli.py:1)

### Changed

- CLI `run-all`/`run-one` führen jetzt echte Runs aus und loggen `series_run` + `run_summary` inkl. `total_new_points` (siehe [`src/macrolens_poc/cli.py`](src/macrolens_poc/cli.py:1)).

### Fixed

- Packaging: Tippfehler in [`pyproject.toml`](pyproject.toml:1) (`rd[project]` → `[project]`).

## [0.0.1]

- Platzhalter für den ersten getaggten Release (Datum folgt).
