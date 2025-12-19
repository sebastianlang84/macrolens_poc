# TODO

## Now (M1/M2) — Matrix + Provider + Pipeline/Storage

- [x] Data-Source-Matrix: Schema + Datei definieren (YAML/CSV/JSON) gem. [`docs/PRD.md`](docs/PRD.md:65)
- [x] Matrix-Loader + Schema-Validation (z. B. pydantic)
- [x] Matrix-Statusfelder automatisch pflegen (`last_ok`, `status`)
- [x] Provider-Adapter: FRED (Series by id, start/end)
- [x] Provider-Adapter: Yahoo Finance (EOD Close für Ticker)
- [x] Provider-Robustheit: Timeout/Retry/Backoff (Provider-Fehler dürfen Run nicht crashen)
- [x] Normalize/Validate: einheitliches Datums-/Zeitzonen-Regime festlegen und konsequent umsetzen
- [x] Normalize: Dedupe + sort + gap handling (Daily Index, NaNs)
- [x] Validate: empty / stale / missing (Status `ok/warn/error/missing`)
- [x] Storage: Time series pro Serie (Parquet bevorzugt), Append/Merge ohne Duplikate
- [x] Revisionsdaten (z. B. FRED): Overwrite-Policy + Logging für rückwirkende Änderungen
- [x] CLI: Daily Run (alle `enabled=true`) + On-Demand Run (Liste von `id`s)
- [x] Run Summary: ok/warn/error/missing + Laufzeit + „0 neue Punkte“ bei No-Op Run

## Next (M3) — Report v1

- [x] Aggregator: letzter Wert + Δ1d/Δ5d/Δ21d
- [x] Simple Risk Flags (Heuristiken) gem. [`docs/PRD.md`](docs/PRD.md:93)
- [x] Export: Markdown + JSON (z. B. `reports/report-YYYYMMDD.md` + `.json`)

## Next (M4) — AI Analysis (The "Missing Link")

> Ziel: Den generierten JSON-Report an ein LLM füttern, um den narrativen Report zu erhalten.

- [x] **Prompt-Engineering**: Template erstellen (System-Prompt "Makro-Stratege" + JSON-Context Injection).
- [x] **LLM-Client**: Minimaler Client (z. B. OpenAI API) mit Interface für einfachen Austausch.
- [x] **CLI `analyze`**: Neuer Befehl `macrolens-poc analyze`, der Report lädt, LLM fragt und `analysis-YYYYMMDD.md` speichert.
- [x] **Config**: API-Keys (z. B. `OPENAI_API_KEY`) in `.env` und Config-Klasse aufnehmen.
- [x] **Multi-Model Support**: Integration von OpenRouter und Fallback-Logik für Reasoning-Modelle.

## Backlog (aus Review) — priorisiert, ausführbare Action Items

> Quelle: Repo-Review (siehe Task-Beschreibung). Fokus auf Konsolidierungen, Robustheit/Determinismus, Test-Stabilität, Docs, Tooling.

### 1) Konsolidierungen mit hohem Wartungsnutzen (Report-Duplikat; Task-Runner)

- [x] Decision: **Report-Implementierung konsolidieren** — welche Datei ist Single Source of Truth?
  - Option A: Canonical = [`src/macrolens_poc/report/v1.py`](src/macrolens_poc/report/v1.py:1); [`src/macrolens_poc/report/generate.py`](src/macrolens_poc/report/generate.py:1) wird Thin-Wrapper/Weiterleitung oder entfernt
  - Option B: Canonical = [`src/macrolens_poc/report/generate.py`](src/macrolens_poc/report/generate.py:1); [`src/macrolens_poc/report/v1.py`](src/macrolens_poc/report/v1.py:1) wird Thin-Wrapper/Weiterleitung oder entfernt
  - DoD/Output: Entscheidung (inkl. 1–2 Bulletpoints „warum“) in [`TODO.md`](TODO.md:1) festgehalten + **ein** klarer Entry Point benannt (Importpfad/CLI-Aufruf).
  - **Entscheidung:** Option A (v1.py). `generate.py` bleibt vorerst als Backwards-Compat/Legacy erhalten (Consolidation später).

- [x] Follow-up (abhängig von Decision): **Report-Duplikat entfernen + Tests auf *einen* Codepfad umstellen**
  - DoD/Output: genau *ein* Codepfad erzeugt Report-Artefakte; Tests decken *diesen* Pfad ab (mind. [`tests/test_report_generate.py`](tests/test_report_generate.py:1) und die v1-Tests wie [`tests/test_m3_report_v1_deltas.py`](tests/test_m3_report_v1_deltas.py:1), [`tests/test_m3_report_v1_risk_flags.py`](tests/test_m3_report_v1_risk_flags.py:1)).

- [x] Decision: **Task-Runner standardisieren** (nur ein Tool als primärer Entry Point)
  - Option A: primär [`Makefile`](Makefile:1), [`justfile`](justfile:1) wird Thin-Wrapper oder entfernt
  - Option B: primär [`justfile`](justfile:1), [`Makefile`](Makefile:1) wird Thin-Wrapper oder entfernt
  - DoD/Output: Entscheidung (inkl. DX/Portabilität) in [`TODO.md`](TODO.md:1) festgehalten.
  - **Entscheidung:** Option A (Makefile). `justfile` bleibt optional als Wrapper.

- [x] Follow-up (abhängig von Decision): **Targets/Recipes konsolidieren (1:1 Mapping)**
  - DoD/Output: einheitliche Befehle existieren (mind. `run_all`, `run_one`, `report`, `test`, `lint`, `format`); Referenz in [`README.md`](README.md:1) passt zum gewählten Runner.

### 2) Kritische Robustheit & Determinismus (Yahoo-Retry; Pipeline-TZ)

- [x] **Repro + Regression-Test für yfinance/Yahoo TypeError (ohne Netzwerk)**
  - Kontext: `TypeError: arg must be a list, tuple, 1-d array, or Series` in [`src/macrolens_poc/sources/yahoo.py`](src/macrolens_poc/sources/yahoo.py:1)
  - DoD/Output: Unit-Test (Monkeypatch/Stubs) reproduziert den Fehler; Run crasht nicht und liefert `error_type`/`error_message` (vgl. [`tests/test_m2_provider_robustness.py`](tests/test_m2_provider_robustness.py:1)).

- [x] **Yahoo-Retry härten: transient vs. permanent sauber trennen + Logging der Retry-Metadaten**
  - DoD/Output: Retry greift nur bei transienten Fehlern (Timeout/HTTP/Rate-Limit o. ä.); permanenter „Data/Schema“-Fehler (z. B. TypeError) wird **nicht** endlos retried; `series_run`-Event enthält konsistente `error_type`/`error_message` + Retry-Infos (z. B. `attempts`, `sleep_s`).

- [x] Decision: **Dependency-Strategie für yfinance**
  - Option A: Version pinning/constraints in [`pyproject.toml`](pyproject.toml:1)
  - Option B: separate Constraints-Datei + dokumentierter Install-Flow (z. B. `pip -c constraints.txt`)
  - DoD/Output: Entscheidung + konkretisiertes Folge-Item (Pin/Constraints + Doku/CI) angelegt.
  - **Entscheidung:** Option A (Version Pinning in `pyproject.toml`).

- [ ] Follow-up (abhängig von Decision): **Warnungen/Breaking Changes absichern** (z. B. `auto_adjust`-FutureWarning)
  - DoD/Output: Unit-Test deckt Verhalten ab; Doku-Hinweis in [`README.md`](README.md:1) falls Nutzer betroffen sind.

- [x] **Pipeline TZ-Determinismus: `date.today()` eliminieren (reproduzierbarer „as_of“ / UTC-Regime)**
  - Kontext: `date.today()` in [`src/macrolens_poc/pipeline/run_series.py`](src/macrolens_poc/pipeline/run_series.py:1)
  - DoD/Output: Pipeline verwendet explizites „as_of“ (z. B. aus CLI/Config) oder strikt UTC-basiertes „now“; gleicher Input ⇒ gleicher Lookback-Zeitraum unabhängig von Local-TZ/Daylight-Saving; Unit-Test deckt Grenzfall „Run um Mitternacht“ ab.

### 3) Test-Stabilität (fragiler Matrix-Test)

- [x] **Fragilen Matrix-Test stabilisieren (keine Order-/Snapshot-Flakes)**
  - Kontext: [`tests/test_m1_sources_matrix.py`](tests/test_m1_sources_matrix.py:1)
  - DoD/Output: Assertions sind robust gegen YAML-Key-Order/FS-Order (z. B. Vergleich über Sets/Maps oder vorheriges Sortieren); Test beschreibt klar, *was* Contract ist (Schema/Defaults) und *was nicht* (Input-Reihenfolge).

- [x] **Matrix-Loader: deterministische Ordnung/Normalisierung garantieren (Loader-Contract)**
  - DoD/Output: Loader liefert deterministisch sortierte Serien (z. B. by `id`); Test beweist deterministische Reihenfolge; keine Flakes.

- [x] **Matrix-Config-Regression: Beispiel-Datei muss immer validieren**
  - DoD/Output: Test lädt [`config/sources_matrix.yaml`](config/sources_matrix.yaml:1) und asserted Schema/Defaults; läuft deterministisch lokal/CI.

### 4) Docs & Repo-Hygiene (Entdriftung + Platzhalter entfernen)

- [x] Decision: **Single Source of Truth für Quickstart/Contracts festlegen (und Cross-Links definieren)**
  - Option A: Nutzer-Doku/Quickstart in [`README.md`](README.md:1); Contributor-Regeln in [`AGENTS.md`](AGENTS.md:1); Anforderungen in [`docs/PRD.md`](docs/PRD.md:1); Status-Snapshot nur in [`docs/PROJECT_STATUS.md`](docs/PROJECT_STATUS.md:1)
  - **Entscheidung:** Option A. Mapping-Tabelle in [`README.md`](README.md:5) integriert.
- [x] Follow-up: **Quickstart/Contracts deduplizieren (README ↔ AGENTS ↔ PRD ↔ PROJECT_STATUS)**
  - DoD/Output: keine widersprüchlichen Beispiele; README ist SSoT für Nutzer-Interaktion und Contracts.
- [x] **PRD TODO-Block konsolidieren (doppelte TODOs vermeiden)**
  - DoD/Output: PRD verlinkt auf [`TODO.md`](TODO.md:1); keine redundanten Aufgabenlisten im PRD.
- [x] **CHANGELOG Release-Platzhalter bereinigen und Release-Flow konsistent machen**
  - DoD/Output: `[Unreleased]` konsolidiert; keine toten Platzhalter.

- [x] **`.gitignore` härten (Artefakte zuverlässig ignorieren, `.gitkeep` intakt lassen)**
  - DoD/Output: Run-Artefakte (Parquet/JSONL/Reports) sind sicher ignoriert; `.gitkeep` bleibt tracked.
- [x] **Version/Docstring aktualisieren (Package-Metadata konsistent machen)**
  - DoD/Output: `__version__` und Docstring in [`src/macrolens_poc/__init__.py`](src/macrolens_poc/__init__.py:1) sind aktuell.

### 5) Tooling-Standardisierung (fehlende Ruff/Black-Konfiguration)

- [x] Decision: **Format/Lint-Toolchain festlegen**
  - Option A: Ruff only (lint + formatter)
  - Option B: Black (format) + Ruff (lint)
  - DoD/Output: Entscheidung in [`TODO.md`](TODO.md:1) festgehalten + gewünschte Commands (inkl. Exit-Codes/CI-Use) benannt.
  - **Entscheidung:** Option A (Ruff only).

- [x] Follow-up (abhängig von Decision): **Tooling zentral in [`pyproject.toml`](pyproject.toml:1) konfigurieren und Runner anbinden**
  - DoD/Output: Ruff/Black-Settings sind vollständig (Line length, target-version, excludes, per-file-ignores falls nötig); Task-Runner (vgl. [`Makefile`](Makefile:1)/[`justfile`](justfile:1)) bietet `lint` + `format` (falls getrennt) + `test`.

## Vulnerabilities & Security (aus [`docs/VULNERABILITIES.md`](docs/VULNERABILITIES.md:1))

- [x] **Robustheit**: Fehlerbehandlung beim Lesen von Parquet-Dateien implementieren ([`src/macrolens_poc/storage/parquet_store.py:34`](src/macrolens_poc/storage/parquet_store.py:34)) (Fix 1.1)
- [ ] **Robustheit**: Yahoo-Provider MultiIndex-Logik härten ([`src/macrolens_poc/sources/yahoo.py:145`](src/macrolens_poc/sources/yahoo.py:145))
- [x] **Sicherheit**: Secrets in Config als `SecretStr` markieren ([`src/macrolens_poc/config.py:21`](src/macrolens_poc/config.py:21)) (Fix 2.1)
- [x] **Sicherheit**: Pfadvalidierung in CLI (`_ensure_dirs`) hinzufügen ([`src/macrolens_poc/cli.py:39`](src/macrolens_poc/cli.py:39)) (Fix 2.2)
- [x] **Datenintegrität**: Atomare Schreibvorgänge für Parquet-Dateien (Temp-File + Rename) ([`src/macrolens_poc/storage/parquet_store.py:152`](src/macrolens_poc/storage/parquet_store.py:152)) (Fix 3.1)
- [ ] **LLM**: Modell-Identifier konsolidieren und fiktive Defaults entfernen ([`src/macrolens_poc/config.py:24`](src/macrolens_poc/config.py:24))
- [x] **Performance**: Logging-I/O optimieren (File-Handle offen halten) ([`src/macrolens_poc/logging_utils.py:38`](src/macrolens_poc/logging_utils.py:38)) (Fix 5.1)

- [x] **Sicherheit**: Path Traversal via `SeriesSpec.id` in Parquet-Pfaden verhindern ([`src/macrolens_poc/pipeline/run_series.py:176`](src/macrolens_poc/pipeline/run_series.py:176)) (Fix 2.3)
- [x] **Sicherheit**: `analyze`-Output-Pfad validieren (kein Truncate/Overwrite beliebiger Dateien) ([`src/macrolens_poc/cli.py:517`](src/macrolens_poc/cli.py:517)) (Fix 2.4)
- [x] **LLM**: Prompt-Injection mitigieren (Report-JSON nicht 1:1 in Prompt übernehmen) ([`src/macrolens_poc/llm/service.py:58`](src/macrolens_poc/llm/service.py:58)) (Fix 4.3)
- [x] **LLM/DoS**: Größen-/Token-Limits für Report-Injection + konservative Defaults für `max_tokens` ([`src/macrolens_poc/llm/openai_provider.py:82`](src/macrolens_poc/llm/openai_provider.py:82)) (Fix 4.4)
- [ ] **LLM/Privacy**: `base_url` Trust/Allowlist + Endpoint-Logging reduzieren/redacten ([`src/macrolens_poc/config.py:108`](src/macrolens_poc/config.py:108))
- [x] **Robustheit**: `matrix-status` gegen ungültige Datumsstrings härten (`date.fromisoformat`) ([`src/macrolens_poc/cli.py:591`](src/macrolens_poc/cli.py:591)) (Fix 1.3)
- [x] **Robustheit**: Report-TZ validieren/abfangen (ungültige `ZoneInfo`) ([`src/macrolens_poc/report/v1.py:231`](src/macrolens_poc/report/v1.py:231)) (Fix 1.4)
- [x] **Robustheit/DoS lokal**: SQLite Busy-/Timeout-Handling + CLI-Fehlerkapselung für Metadaten-Upsert ([`src/macrolens_poc/storage/metadata_db.py:68`](src/macrolens_poc/storage/metadata_db.py:68)) (Fix 1.5)
- [ ] **Datenintegrität**: Report-Artefakte (MD/JSON) atomar schreiben (Temp-File + Rename) ([`src/macrolens_poc/report/v1.py:209`](src/macrolens_poc/report/v1.py:209))
- [x] **Supply Chain/Repro**: Lockfile/Constraints einführen (Dependencies nicht nur `>=`) ([`pyproject.toml:7`](pyproject.toml:7)) (Fix 6.1)
- [ ] **Observability/Datenintegrität**: JSONL-Logfile pro Run eindeutig machen (kein Tages-Interleaving) ([`src/macrolens_poc/logging_utils.py:23`](src/macrolens_poc/logging_utils.py:23))

## Later — Monitoring, DX, Open Questions (bestehender Backlog)

- [x] (↪ siehe „Backlog (aus Review) / 2“) yfinance/Yahoo Robustheit: Fehler reproduzieren und Schema-/Kompatibilitäts-Fix für `TypeError: arg must be a list, tuple, 1-d array, or Series` (siehe [`src/macrolens_poc/sources/yahoo.py`](src/macrolens_poc/sources/yahoo.py:1))
- [x] (↪ siehe „Backlog (aus Review) / 2“) yfinance Dependency-Strategie: Version pinning/constraints evaluieren (ggf. lockfile/constraints) und `auto_adjust` FutureWarning im Verhalten absichern
- [x] FRED: Lookback/Serie-Frequenz-Handling verbessern (z. B. Default Lookback für niedrigfrequente Makroserien erhöhen oder frequenzabhängig wählen); dokumentierte Empfehlung aus Testlauf konsolidieren
- [x] Logging: FRED Error-Details in per-series Event/Report sicherstellen (bei `status=error` sollen `error_type`/`error_message` konsistent gesetzt werden; vgl. [`_log_series_run()`](src/macrolens_poc/cli.py:86))

- [x] Stale-series detection (z. B. „seit N Tagen unverändert“) + Matrix-Status-Export konsolidieren (`data/matrix_status.json`)
- [x] SQLite Index für Metadaten (`data/metadata.sqlite`)
- [x] DX: Makefile/justfile (z. B. `run_all`, `run_one`, `report`)
- [x] Tests: Matrix-Loader + Storage-Merge (kritische Logik)
- [ ] Open Questions sammeln/aktualisieren (Yahoo-Ersatz, weitere Regionen/Serien)
- [x] Individuelle `stale_days` pro Serie in `sources_matrix.yaml` ermöglichen
- [x] Lookback-Logik für Deltas bei lückenhaften Daten verbessern (intelligente Suche nach dem letzten validen Datenpunkt)
- [ ] CLI-Warnung bei fehlendem `--config` Flag für OpenRouter-Keys (Verbesserung der UX bei Secret-Handling)

## Docs — README/CHANGELOG Pflege

- [x] [`README.md`](README.md:1): Setup + minimale CLI-Usage dokumentieren
- [x] [`CHANGELOG.md`](CHANGELOG.md:1): „Keep a Changelog“ mit Pflichtsektion `[Unreleased]` initialisieren
- [x] [`TODO.md`](TODO.md:1): projektbezogene, priorisierte Aufgabenliste pflegen

## Done (M0) — Repo + Skeleton

- [x] Python-Projekt initialisiert (`pyproject.toml`)
- [x] CLI-Skeleton vorhanden
- [x] Konfig-Handling: `.env` + Beispiel-Konfig (`config/config.example.yaml`)
- [x] Logging-Skeleton (structured logs)
- [x] Repo-Struktur angelegt (`src/`, `tests/`, `data/`, `logs/`, `reports/`)
