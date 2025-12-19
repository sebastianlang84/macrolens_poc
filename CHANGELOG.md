# Changelog

Alle nennenswerten Änderungen an diesem Projekt werden in dieser Datei dokumentiert.

Das Format orientiert sich an **Keep a Changelog** und **Semantic Versioning**:

- https://keepachangelog.com/en/1.1.0/
- https://semver.org/

## [Unreleased]

### Added
- Automatischer Default für `--config config/config.yaml` im CLI, falls die Datei existiert.
- CLI-Warnung im `analyze` Kommando, wenn ein OpenRouter-Key (`sk-or-v1-`) erkannt wird, aber die `base_url` nicht auf OpenRouter zeigt.
- Robuste Delta-Berechnung mit `find_nearest_value` (Toleranz +/- 2 Tage) in `report/v1.py`, um Gaps an Wochenenden/Feiertagen zu handhaben.
- Individuelle `stale_days` Overrides in `config/sources_matrix.yaml` für monatliche Serien (us_cpi, us_pce, us_unemployment_rate, us_m2, us_indpro).
- Anzeige des Staleness-Schwellenwerts im Report (`src/macrolens_poc/report/v1.py`).
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
- **LLM:** Synchronisation der Modell-Identifier in Code, Tests und Dokumentation mit der zentralen `config.yaml` (Entfernung veralteter/fiktiver Modelle).
- **Tests:** Syntaxfehler in `tests/test_llm_reasoning.py` behoben.
- **Robustness:** Fix 1.1 (Robustes Lesen): `pd.read_parquet` in `try-except` gekapselt ([`src/macrolens_poc/storage/parquet_store.py`](src/macrolens_poc/storage/parquet_store.py:34)).
- **Robustness:** Fix 1.3 (Robustes Datums-Parsing): `date.fromisoformat` in `matrix-status` Kommando gehärtet ([`src/macrolens_poc/cli.py`](src/macrolens_poc/cli.py:591)).
- **Robustness:** Fix 1.4 (Zeitzonen-Validierung): `ZoneInfo` Validierung in Report-Generierung und Config hinzugefügt ([`src/macrolens_poc/report/v1.py`](src/macrolens_poc/report/v1.py:231)).
- **Robustness:** Fix 1.5: SQLite Busy-Timeout (10s) und Fehlerkapselung beim Metadaten-Upsert im CLI implementiert ([`docs/VULNERABILITIES.md`](docs/VULNERABILITIES.md:30)).
- **Security:** Fix 2.1 (Secret-Exposition): Secrets in Config als `SecretStr` markiert ([`src/macrolens_poc/config.py`](src/macrolens_poc/config.py:21)).
- **Security:** Fix 2.2: Pfadvalidierung in `_ensure_dirs` (CLI) gegen Path Traversal (Resolve + `is_relative_to`).
- **Security:** Fix 2.3: Path Traversal Schutz für `SeriesSpec.id` via Pydantic-Validierung und Pfad-Normalisierung in Pipeline/Report.
- **Security:** Fix 2.4: Pfadvalidierung im `analyze` Kommando (CLI) zur Einschränkung des `--output` Pfads auf das Reports-Verzeichnis.
- **Data Integrity:** Fix 3.1 (Atomares Schreiben): Parquet-Dateien werden nun atomar via Temp-File + `os.replace` geschrieben ([`src/macrolens_poc/storage/parquet_store.py`](src/macrolens_poc/storage/parquet_store.py:152)).
- **LLM:** Fix 4.3 (Prompt-Härtung): Klare Delimiter (`<report_data>`) und Sicherheitsanweisungen im System-Prompt zur Vermeidung von Prompt-Injection.
- **LLM:** Fix 4.4 (Token-Limits): Größenbeschränkung für injizierte Reports (max. 50k Zeichen) und konservativere `max_tokens` Defaults für Reasoning-Modelle.
- **LLM:** `OpenAIProvider` Robustheit: Automatischer Fallback bei nicht unterstützten Reasoning-Parametern (HTTP 400/404) und verbesserte OpenRouter-Kompatibilität (`require_parameters: False`).
- **Performance:** Fix 5.1: Logging-I/O Optimierung. `JsonlLogger` hält nun den File-Handle während eines Runs offen (Context Manager), um Overhead zu reduzieren ([`docs/VULNERABILITIES.md`](docs/VULNERABILITIES.md:109)).
- **Supply Chain:** Fix 6.1: Einführung von `requirements.lock` für reproduzierbare Installationen ([`docs/VULNERABILITIES.md`](docs/VULNERABILITIES.md:116)).
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
