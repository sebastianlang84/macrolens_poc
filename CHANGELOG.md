# Changelog

Alle nennenswerten Änderungen an diesem Projekt werden in dieser Datei dokumentiert.

Das Format orientiert sich an **Keep a Changelog** und **Semantic Versioning**:

- https://keepachangelog.com/en/1.1.0/
- https://semver.org/

## [Unreleased]

## [0.4.1] - 2025-12-15

### Fixed
- **Config:** Korrektur des `.env` Lademechanismus (explizites Laden vor Config-Initialisierung), um sicherzustellen, dass Umgebungsvariablen korrekt priorisiert werden.
- **LLM:** Fix für `OpenAIProvider` Initialisierung (korrekte Handhabung von `api_key` und `base_url` aus der Konfiguration).
- **LLM:** Verbesserte Fehlerbehandlung bei fehlenden API-Keys (Graceful Degradation statt Crash).

### Added
- **Feat:** Neuer CLI-Befehl `run-selected` (Ausführung spezifischer Serien-IDs).
- **Config:** Neue Serien `us_hy_spread` und `us_indpro` zur Matrix hinzugefügt.

### Changed
- **Robustness:** Yahoo/yfinance Retry-Logik gehärtet und Version gepinnt.

## [0.4.0] - 2025-12-14

### Added
- **Feat:** KI-Analyse (`analyze` command) mit OpenAI Integration für Markt-Zusammenfassungen.
- **Feat:** Multi-Model Support: Analyse mit mehreren Modellen parallel (konfigurierbar via `LLM_MODELS` oder `--models`).
- **Feat:** OpenRouter Integration: Konfigurierbare `LLM_BASE_URL` ermöglicht Nutzung beliebiger OpenAI-kompatibler APIs.
- **Feat:** Stale-Series Detection (Warnung bei veralteten Daten basierend auf `frequency`).
- Pipeline: `last_observation_date` und `run_at` im `SeriesRunResult` und `series_run` Event.
- Yahoo Source: `timeout_s` Parameter für `fetch_yahoo_history` (Default: 10.0s).

### Changed
- **Refactor:** Pipeline Determinismus (strikte `as_of` Logik, UTC).
- **Chore:** Restrukturierung der Dokumentation in `/docs` (Konsolidierung).
- Matrix: Deterministische Sortierung der Serien beim Laden.
- Yahoo Source: Verbesserte Retry-Logik (transient vs. permanent errors).
- Docs: Härtung von `.gitignore` für Artefakte.

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
- Docs: Cleanup [`docs/PRD.md`](docs/PRD.md:1) (Entfernung veralteter TODOs).

### Fixed
- Yahoo/yfinance: `TypeError` Handling und Regression-Tests.
- Config: Laden nur der lokalen `.env`.
- Tests: Stabilisierung nicht-deterministischer Tests.
