# Changelog

Alle nennenswerten Änderungen an diesem Projekt werden in dieser Datei dokumentiert.

Das Format orientiert sich an **Keep a Changelog** und **Semantic Versioning**:

- https://keepachangelog.com/en/1.1.0/
- https://semver.org/

## [Unreleased]

### Added
- **Feat:** Stale-Series Detection Logik in `matrix_status.py` implementiert.
- **CLI:** Neuer Befehl `matrix-status` zur Anzeige des Status aller Serien inkl. Staleness-Warnungen.
- **Tooling:** Standardisierung auf **Ruff** für Linting und Formatting (ersetzt Black/Flake8).
- **Docs:** Gap-Analyse des Live-Tests ([`docs/GAP_ANALYSIS_LIVE_TEST.md`](docs/GAP_ANALYSIS_LIVE_TEST.md:1)) und Design für robuste Analysen ([`docs/design/DESIGN_ROBUST_ANALYSIS.md`](docs/design/DESIGN_ROBUST_ANALYSIS.md:1)).
- **LLM:** Konzept für Multi-Model Redundanz (OpenAI + Gemini) ausgearbeitet.
- **Tests:** Regression-Test für die Sources-Matrix ([`tests/test_matrix_regression.py`](tests/test_matrix_regression.py:1)) hinzugefügt.
- **Tests:** Unit-Tests für Stale-Detection Logik in `tests/test_stale_detection.py`.
- **Report:** Legacy Report-Generator in [`src/macrolens_poc/report/generate.py`](src/macrolens_poc/report/generate.py:1) (Backwards-Compat).

### Changed
- **Docs:** Dokumentation bereinigt und konsolidiert (Deduplizierung README/AGENTS/PRD).
- **Docs:** `README.md` aktualisiert (Config Priority, Happy Path, Data Contract, Troubleshooting, SSoT-Mapping).
- **Docs:** `docs/PRD.md` aktualisiert (Matrix Extensions, Data Contract, Idempotency, Report Logic).
- **Pipeline:** Strikter TZ-Determinismus implementiert. Alle Zeitstempel basieren nun auf UTC oder einem expliziten `as_of` Datum.
- **Source:** FRED Provider optimiert (Lookback-Puffer, Fehlerdetails, Spaltenkonsistenz).
- **LLM:** Prompts (`system.md`, `user.md`) aktualisiert.
- **Matrix-Status:** `SeriesStatusEntry` speichert nun `last_observation_date`.

### Fixed
- **Source:** Yahoo Finance Stabilisierung: Upgrade auf `yfinance>=0.2.50`, behobener `TypeError` und verbessertes Session-Handling.
- **Source:** Yahoo Finance: `FutureWarning` bzgl. `auto_adjust` unterdrückt.
- **Tests:** Veraltete Yahoo-Mocks auf `yf.Ticker.history` umgestellt.

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
