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
- Provider-Robustheit: Retry/Timeout/Backoff + Fehler-Isolation pro Serie (siehe [`src/macrolens_poc/retry_utils.py`](src/macrolens_poc/retry_utils.py:1), [`src/macrolens_poc/pipeline/run_series.py`](src/macrolens_poc/pipeline/run_series.py:1)).
- Persistente Matrix-Statuspflege (`data/matrix_status.json`) nach Runs (siehe [`src/macrolens_poc/sources/matrix_status.py`](src/macrolens_poc/sources/matrix_status.py:1), [`src/macrolens_poc/cli.py`](src/macrolens_poc/cli.py:1)).
- Revisionsdaten-Detektion beim Storage-Merge: `revision_overwrites_count` + Sample im `series_run` Log (siehe [`src/macrolens_poc/storage/parquet_store.py`](src/macrolens_poc/storage/parquet_store.py:1)).
- Report v1: Aggregator (last + Δ1d/5d/21d), Risk Flags, Markdown+JSON Export + CLI Command `report` (siehe [`src/macrolens_poc/report/v1.py`](src/macrolens_poc/report/v1.py:1), [`src/macrolens_poc/cli.py`](src/macrolens_poc/cli.py:1)).
- Tests:
  - Provider-Fehler-Isolation: [`tests/test_m2_provider_robustness.py`](tests/test_m2_provider_robustness.py:1)
  - Matrix-Status Merge/Persistenz: [`tests/test_m3_matrix_status_persist.py`](tests/test_m3_matrix_status_persist.py:1)
  - Report v1 Deltas/Risk Flags: [`tests/test_m3_report_v1_deltas.py`](tests/test_m3_report_v1_deltas.py:1), [`tests/test_m3_report_v1_risk_flags.py`](tests/test_m3_report_v1_risk_flags.py:1)
- Developer-Tasks für CLI und Checks via `Makefile`/`justfile` (`run_all`, `run_one`, `report`, `lint`, `format`, `smoke`)

### Changed

- CLI um Command `report` erweitert (siehe [`src/macrolens_poc/cli.py`](src/macrolens_poc/cli.py:1)).

### Fixed

- (keine)

## [0.0.1]

- Platzhalter für den ersten getaggten Release (Datum folgt).
