# TODO

## Now (M1/M2) — Matrix + Provider + Pipeline/Storage

- [x] Data-Source-Matrix: Schema + Datei definieren (YAML/CSV/JSON) gem. [`PRD.md`](PRD.md:65)
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
- [x] Simple Risk Flags (Heuristiken) gem. [`PRD.md`](PRD.md:93)
- [x] Export: Markdown + JSON (z. B. `reports/report-YYYYMMDD.md` + `.json`)

## Next (M4) — AI Analysis (The "Missing Link")

> Ziel: Den generierten JSON-Report an ein LLM füttern, um den narrativen Report zu erhalten.

- [ ] **Prompt-Engineering**: Template erstellen (System-Prompt "Makro-Stratege" + JSON-Context Injection).
- [ ] **LLM-Client**: Minimaler Client (z. B. OpenAI API) mit Interface für einfachen Austausch.
- [ ] **CLI `analyze`**: Neuer Befehl `macrolens-poc analyze`, der Report lädt, LLM fragt und `analysis-YYYYMMDD.md` speichert.
- [ ] **Config**: API-Keys (z. B. `OPENAI_API_KEY`) in `.env` und Config-Klasse aufnehmen.

## Backlog (aus Review) — priorisiert, ausführbare Action Items

> Quelle: Repo-Review (siehe Task-Beschreibung). Fokus auf Konsolidierungen, Robustheit/Determinismus, Test-Stabilität, Docs, Tooling.

### 1) Konsolidierungen mit hohem Wartungsnutzen (Report-Duplikat; Task-Runner)

- [x] Decision: **Report-Implementierung konsolidieren** — welche Datei ist Single Source of Truth?
  - Option A: Canonical = [`src/macrolens_poc/report/v1.py`](src/macrolens_poc/report/v1.py:1); [`src/macrolens_poc/report/generate.py`](src/macrolens_poc/report/generate.py:1) wird Thin-Wrapper/Weiterleitung oder entfernt
  - Option B: Canonical = [`src/macrolens_poc/report/generate.py`](src/macrolens_poc/report/generate.py:1); [`src/macrolens_poc/report/v1.py`](src/macrolens_poc/report/v1.py:1) wird Thin-Wrapper/Weiterleitung oder entfernt
  - DoD/Output: Entscheidung (inkl. 1–2 Bulletpoints „warum“) in [`TODO.md`](TODO.md:1) festgehalten + **ein** klarer Entry Point benannt (Importpfad/CLI-Aufruf).
  - **Entscheidung:** Option A (v1.py). `generate.py` wurde entfernt.

- [x] Follow-up (abhängig von Decision): **Report-Duplikat entfernen + Tests auf *einen* Codepfad umstellen**
  - DoD/Output: genau *ein* Codepfad erzeugt Report-Artefakte; Tests decken *diesen* Pfad ab (mind. [`tests/test_report_generate.py`](tests/test_report_generate.py:1) und die v1-Tests wie [`tests/test_m3_report_v1_deltas.py`](tests/test_m3_report_v1_deltas.py:1), [`tests/test_m3_report_v1_risk_flags.py`](tests/test_m3_report_v1_risk_flags.py:1)).

- [x] Decision: **Task-Runner standardisieren** (nur ein Tool als primärer Entry Point)
  - Option A: primär [`Makefile`](Makefile:1), [`justfile`](justfile:1) wird Thin-Wrapper oder entfernt
  - Option B: primär [`justfile`](justfile:1), [`Makefile`](Makefile:1) wird Thin-Wrapper oder entfernt
  - DoD/Output: Entscheidung (inkl. DX/Portabilität) in [`TODO.md`](TODO.md:1) festgehalten.
  - **Entscheidung:** Option A (Makefile). `justfile` wurde entfernt.

- [x] Follow-up (abhängig von Decision): **Targets/Recipes konsolidieren (1:1 Mapping)**
  - DoD/Output: einheitliche Befehle existieren (mind. `run_all`, `run_one`, `report`, `test`, `lint`, `format`); Referenz in [`README.md`](README.md:1) passt zum gewählten Runner.

### 2) Kritische Robustheit & Determinismus (Yahoo-Retry; Pipeline-TZ)

- [x] **Repro + Regression-Test für yfinance/Yahoo TypeError (ohne Netzwerk)**
  - Kontext: `TypeError: arg must be a list, tuple, 1-d array, or Series` in [`src/macrolens_poc/sources/yahoo.py`](src/macrolens_poc/sources/yahoo.py:1)
  - DoD/Output: Unit-Test (Monkeypatch/Stubs) reproduziert den Fehler; Run crasht nicht und liefert `error_type`/`error_message` (vgl. [`tests/test_m2_provider_robustness.py`](tests/test_m2_provider_robustness.py:1)).

- [ ] **Yahoo-Retry härten: transient vs. permanent sauber trennen + Logging der Retry-Metadaten**
  - DoD/Output: Retry greift nur bei transienten Fehlern (Timeout/HTTP/Rate-Limit o. ä.); permanenter „Data/Schema“-Fehler (z. B. TypeError) wird **nicht** endlos retried; `series_run`-Event enthält konsistente `error_type`/`error_message` + Retry-Infos (z. B. `attempts`, `sleep_s`).

- [ ] Decision: **Dependency-Strategie für yfinance**
  - Option A: Version pinning/constraints in [`pyproject.toml`](pyproject.toml:1)
  - Option B: separate Constraints-Datei + dokumentierter Install-Flow (z. B. `pip -c constraints.txt`)
  - DoD/Output: Entscheidung + konkretisiertes Folge-Item (Pin/Constraints + Doku/CI) angelegt.

- [ ] Follow-up (abhängig von Decision): **Warnungen/Breaking Changes absichern** (z. B. `auto_adjust`-FutureWarning)
  - DoD/Output: Unit-Test deckt Verhalten ab; Doku-Hinweis in [`README.md`](README.md:1) falls Nutzer betroffen sind.

- [ ] **Pipeline TZ-Determinismus: `date.today()` eliminieren (reproduzierbarer „as_of“ / UTC-Regime)**
  - Kontext: `date.today()` in [`src/macrolens_poc/pipeline/run_series.py`](src/macrolens_poc/pipeline/run_series.py:1)
  - DoD/Output: Pipeline verwendet explizites „as_of“ (z. B. aus CLI/Config) oder strikt UTC-basiertes „now“; gleicher Input ⇒ gleicher Lookback-Zeitraum unabhängig von Local-TZ/Daylight-Saving; Unit-Test deckt Grenzfall „Run um Mitternacht“ ab.

### 3) Test-Stabilität (fragiler Matrix-Test)

- [x] **Fragilen Matrix-Test stabilisieren (keine Order-/Snapshot-Flakes)**
  - Kontext: [`tests/test_m1_sources_matrix.py`](tests/test_m1_sources_matrix.py:1)
  - DoD/Output: Assertions sind robust gegen YAML-Key-Order/FS-Order (z. B. Vergleich über Sets/Maps oder vorheriges Sortieren); Test beschreibt klar, *was* Contract ist (Schema/Defaults) und *was nicht* (Input-Reihenfolge).

- [ ] **Matrix-Loader: deterministische Ordnung/Normalisierung garantieren (Loader-Contract)**
  - DoD/Output: Loader liefert deterministisch sortierte Serien (z. B. by `id`); Test beweist deterministische Reihenfolge; keine Flakes.

- [ ] **Matrix-Config-Regression: Beispiel-Datei muss immer validieren**
  - DoD/Output: Test lädt [`config/sources_matrix.yaml`](config/sources_matrix.yaml:1) und asserted Schema/Defaults; läuft deterministisch lokal/CI.

### 4) Docs & Repo-Hygiene (Entdriftung + Platzhalter entfernen)

- [ ] Decision: **Single Source of Truth für Quickstart/Contracts festlegen (und Cross-Links definieren)**
  - Option A: Nutzer-Doku/Quickstart in [`README.md`](README.md:1); Contributor-Regeln in [`AGENTS.md`](AGENTS.md:1); Anforderungen in [`PRD.md`](PRD.md:1); Status-Snapshot nur in [`PROJECT_STATUS.md`](PROJECT_STATUS.md:1)
  - Option B: Alternative Aufteilung (explizit begründen) + Mapping-Tabelle in [`README.md`](README.md:1)
  - DoD/Output: Entscheidung + Mapping-Tabelle (Dokument → Zweck/Owner) festgehalten.

- [ ] Follow-up: **Quickstart/Contracts deduplizieren (README ↔ AGENTS ↔ PRD ↔ PROJECT_STATUS)**
  - DoD/Output: keine widersprüchlichen Beispiele/Flags/Artefaktpfade; globaler `--config` Callback explizit genannt (vgl. [`src/macrolens_poc/cli.py`](src/macrolens_poc/cli.py:35)); README enthält nur „current“ Quickstart, Snapshots wandern nach [`PROJECT_STATUS.md`](PROJECT_STATUS.md:1).

- [ ] **PRD TODO-Block konsolidieren (doppelte TODOs vermeiden)**
  - Kontext: TODO-Block in [`PRD.md`](PRD.md:1)
  - DoD/Output: PRD enthält nur Requirements/Scope; aktive Tasks sind in [`TODO.md`](TODO.md:1) (oder PRD verlinkt sauber auf TODO ohne Doppelung).

- [ ] **CHANGELOG Release-Platzhalter bereinigen und Release-Flow konsistent machen**
  - Kontext: Platzhalter/Release-Struktur in [`CHANGELOG.md`](CHANGELOG.md:1)
  - DoD/Output: `[Unreleased]` bleibt Pflicht; keine toten Platzhalter; SemVer-Policy ist konsistent mit Repo-Konventionen.

- [ ] **`.gitignore` härten (Artefakte zuverlässig ignorieren, `.gitkeep` intakt lassen)**
  - Kontext: [`.gitignore`](.gitignore:1) + Artefakt-Dirs [`data/`](data/.gitkeep:1), [`logs/`](logs/.gitkeep:1), [`reports/`](reports/.gitkeep:1)
  - DoD/Output: Run-Artefakte (Parquet/JSONL/Reports) sind sicher ignoriert; `.gitkeep` bleibt tracked; Doku referenziert die Artefakt-Orte konsistent.

- [ ] **Version/Docstring aktualisieren (Package-Metadata konsistent machen)**
  - Kontext: [`src/macrolens_poc/__init__.py`](src/macrolens_poc/__init__.py:1)
  - DoD/Output: `__version__`/Package-Docstring (falls vorhanden) sind konsistent zu [`pyproject.toml`](pyproject.toml:1) und [`CHANGELOG.md`](CHANGELOG.md:1); keine veralteten Beschreibungen.

### 5) Tooling-Standardisierung (fehlende Ruff/Black-Konfiguration)

- [ ] Decision: **Format/Lint-Toolchain festlegen**
  - Option A: Ruff only (lint + formatter)
  - Option B: Black (format) + Ruff (lint)
  - DoD/Output: Entscheidung in [`TODO.md`](TODO.md:1) festgehalten + gewünschte Commands (inkl. Exit-Codes/CI-Use) benannt.

- [ ] Follow-up (abhängig von Decision): **Tooling zentral in [`pyproject.toml`](pyproject.toml:1) konfigurieren und Runner anbinden**
  - DoD/Output: Ruff/Black-Settings sind vollständig (Line length, target-version, excludes, per-file-ignores falls nötig); Task-Runner (vgl. [`Makefile`](Makefile:1)/[`justfile`](justfile:1)) bietet `lint` + `format` (falls getrennt) + `test`.

## Later — Monitoring, DX, Open Questions (bestehender Backlog)

- [ ] (↪ siehe „Backlog (aus Review) / 2“) yfinance/Yahoo Robustheit: Fehler reproduzieren und Schema-/Kompatibilitäts-Fix für `TypeError: arg must be a list, tuple, 1-d array, or Series` (siehe [`src/macrolens_poc/sources/yahoo.py`](src/macrolens_poc/sources/yahoo.py:1))
- [ ] (↪ siehe „Backlog (aus Review) / 2“) yfinance Dependency-Strategie: Version pinning/constraints evaluieren (ggf. lockfile/constraints) und `auto_adjust` FutureWarning im Verhalten absichern
- [ ] FRED: Lookback/Serie-Frequenz-Handling verbessern (z. B. Default Lookback für niedrigfrequente Makroserien erhöhen oder frequenzabhängig wählen); dokumentierte Empfehlung aus Testlauf konsolidieren
- [ ] Logging: FRED Error-Details in per-series Event/Report sicherstellen (bei `status=error` sollen `error_type`/`error_message` konsistent gesetzt werden; vgl. [`_log_series_run()`](src/macrolens_poc/cli.py:86))

- [ ] Stale-series detection (z. B. „seit N Tagen unverändert“) + Matrix-Status-Export konsolidieren (`data/matrix_status.json`)
- [x] SQLite Index für Metadaten (`data/metadata.sqlite`)
- [x] DX: Makefile/justfile (z. B. `run_all`, `run_one`, `report`)
- [x] Tests: Matrix-Loader + Storage-Merge (kritische Logik)
- [ ] Open Questions sammeln/aktualisieren (Yahoo-Ersatz, weitere Regionen/Serien)

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
