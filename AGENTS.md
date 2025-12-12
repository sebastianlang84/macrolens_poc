# AGENTS.md — macrolens_poc: Agent Rules

Dieses Dokument definiert verbindliche Arbeitsregeln für KI-Coding-Agenten in diesem Repository.

Quelle/Referenz (Pattern): [`../llmstack/AGENTS.md`](../llmstack/AGENTS.md:1)

---

## 1) Kernprinzipien (Arbeitsstil)

- **Protocol before content (Stop & Ask)**
  - Bei unklaren Zielen, Datenbasis oder Constraints: **1–3 gezielte Rückfragen** stellen, bevor größerer Output entsteht.
  - Wenn Rückfragen nicht möglich sind: **Annahmen explizit nennen** und nur minimalen, klar markierten Vorschlag liefern.
- **No Fluff**
  - Keine Einleitungen/Schlussfloskeln; direkt mit Ergebnis, Analyse oder Code starten.
  - Begründungen kurz als Bulletpoints.
- **Fakten- und Evidenzpflicht**
  - **Keine erfundenen API-Signaturen, Zahlen, Zitate oder Bibliotheksdetails.**
  - Unsicherheit klar markieren (z. B. „gesichert / wahrscheinlich / unsicher“).
- **Repo-first (Grounding)**
  - Zuerst Repo-Dateien/Configs lesen (z. B. [`PRD.md`](PRD.md:1)), dann erst externe Quellen.
- **Kleine, nachvollziehbare Diffs**
  - Änderungen in kleinen Schritten; keine „Mega-PRs“.

---

## 2) Projekt-Kontext & Links

- **Primary Entry Point**: [`README.md`](README.md:1) (Quickstart, Installation, Usage).
- **Requirements**: [`PRD.md`](PRD.md:1).
- **Status**: [`PROJECT_STATUS.md`](PROJECT_STATUS.md:1).

---

## 3) Repo-Regeln (Do/Don’t)

### 3.1 Secrets & Konfiguration

- **Keine Secrets einchecken** (API-Keys, Tokens, Passwörter).
- Secrets ausschließlich über `.env` / lokale Konfig (z. B. `config/`) beziehen; `.env` gehört in `.gitignore`.
- Wenn Beispielwerte nötig sind: `*.example`/`*.template` Dateien verwenden.

### 3.2 Determinismus & Reproduzierbarkeit

- Ziel: reproduzierbarer Run (Lockfile/Dependencies, deterministische Outputs bei gleichem Input) gemäß [`PRD.md`](PRD.md:122).
- Zeit/Zeitzone explizit dokumentieren und im Code konsequent umsetzen.

### 3.3 Logging & Robustheit

- Logging **strukturiert** (JSON/JSONL), inkl. klarer Run-Summary.
- Provider-Fehler sollen **nicht** den gesamten Run crashen: Timeouts/Retry/Backoff, Statusfelder (ok/warn/error/missing).

### 3.4 Datenhaltung

- Append-/Merge-Logik ohne Duplikate; keine stillen Overwrites.
- Revisionen (z. B. FRED) nur mit klarer, geloggter Overwrite-Policy.

### 3.5 Code-/DX-Standards

- Bevorzugt: klarer Modul-Schnitt (config/sources/pipeline/storage/report) analog [`PRD.md`](PRD.md:99).
- Minimal-Tests für kritische Logik (z. B. Matrix-Loader, Storage-Merge).
- CLI-Kommandos sollen dokumentiert und stabil sein (help-Text, deterministisches Verhalten).

### 3.6 Versionierung, Changelog, Doku-Pflege

- **Versionierung**: Default **SemVer** (`MAJOR.MINOR.PATCH`), in der Frühphase **`0.y.z`** (Features = `0.MINOR`, Fixes = `0.PATCH`).
- **Changelog**: Format **Keep a Changelog**, Sektion **`[Unreleased]`** ist Pflicht.
- **Commits**: **Conventional Commits** empfohlen (z. B. `feat:`, `fix:`, `docs:`); Breaking via `!` oder `BREAKING CHANGE:`.
- **Breaking Change (Repo-Definition)**: Änderungen an **CLI** (Commands/Flags/Output), **Config** (Keys/Schema/Defaults), **Storage/DB-Schema** (Layout/Partitioning/Dateiformat).
- **Doku-Pflicht**: [`README.md`](README.md:1), [`CHANGELOG.md`](CHANGELOG.md:1), [`TODO.md`](TODO.md:1) aktuell halten.

### 3.7 Git-Workflow & Commit-Messages

- **Workflow**: Wir arbeiten nach **GitFlow**.
  - langlebige Branches: `main`, `develop`
  - Feature-Branches: `feature/<kurz-beschreibung>` (von `develop`)
  - Release-Branches: `release/<version>` (von `develop` → nach `main` + `develop` zurück mergen)
  - Hotfix-Branches: `hotfix/<kurz-beschreibung>` (von `main` → nach `main` + `develop` zurück mergen)
- **Commit-Messages**: **Conventional Commits** sind verbindlich (mindestens Type + Summary), z. B.:
  - `feat: add fred provider`
  - `fix: prevent duplicate points in parquet merge`
  - `docs: update README quickstart`
- **Pre-Commit Pflicht**: Vor **jedem** Commit muss die Doku vollständig/aktuell sein (mind. [`README.md`](README.md:1), [`CHANGELOG.md`](CHANGELOG.md:1), [`TODO.md`](TODO.md:1)) und ein lokaler Smoke-Check grün sein (mind. `python -m pytest`).

---

## 4) Tooling-Regeln (Terminal/Docs)

- **Umgebung zuerst feststellen**: Zu Beginn eines Tasks (und bevor Tool-Commands/Installs vorgeschlagen werden) die lokale Umgebung kurz verifizieren:
  - Betriebssystem / Shell
  - Laufzeitumgebung (z. B. `python` vs `python3`, Version)
  - Paketmanager/Tools (z. B. `pip`, `pytest`, `poetry`, `uv`, `conda`) und ob sie verfügbar sind
  - ggf. aktive Terminals/Running Processes (Dev-Server, Jobs)
- **Terminal-Kommandos**: Immer kurz erklären, was der Befehl macht und warum er nötig ist.
- **Context7 nutzen**: Bei Bibliotheks-/Framework-Fragen (APIs, Signaturen, Verhalten) zuerst Context7 verwenden, statt zu raten.
- Externe Web-Recherche nur, wenn Repo/Docs nicht ausreichen oder das Thema zeitkritisch ist.

---

## 5) Arbeitsabfolge (Standard)

1. Relevante Repo-Dateien lesen (mind. [`PRD.md`](PRD.md:1), ggf. [`README.md`](README.md:1)).
2. Plan in 3–7 Schritten (klein, überprüfbar).
3. Implementieren in kleinen Diffs.
4. Minimaler Smoke-Check (z. B. Import/CLI Help/Unit-Test) sofern möglich.
5. Doku aktualisieren (README/Changelog) nur wenn es echten Nutzwert hat.

---

## 6) Quickstart / Smoke-Checklist (lokal)

Siehe [`README.md`](README.md:5) für detaillierte Installationsanweisungen.

**Minimal Smoke-Check vor Commit:**

1.  **Environment**: `source .venv/bin/activate`
2.  **CLI Help**: `macrolens-poc --help`
3.  **Tests**: `python -m pytest`
4.  **Docs**: `README.md`, `CHANGELOG.md` aktuell?

---

## 7) Artefakte & Repo-Sauberkeit

- Laufzeit-Artefakte (Outputs) werden **nicht** committet.
- Standard-Orte (konfigurierbar via [`config/config.example.yaml`](config/config.example.yaml:16)):
  - Daten: [`data/`](data/.gitkeep:1) (z. B. `data/series/*.parquet`)
  - Logs: [`logs/`](logs/.gitkeep:1) (z. B. `logs/run-YYYYMMDD.jsonl`)
  - Reports: [`reports/`](reports/.gitkeep:1) (z. B. `reports/*.md`, `reports/*.json`)
- Wenn neue Artefakt-Typen entstehen: Pfad/Pattern dokumentieren und `.gitignore` aktualisieren (keine stillen Overwrites).

---

## 8) Observability Contract (JSONL)

Logging ist strukturiert als **JSONL**: eine JSON-Map pro Zeile (Writer: `JsonlLogger` in [`src/macrolens_poc/logging_utils.py`](src/macrolens_poc/logging_utils.py:26)).

Minimalfelder (jede Zeile):
- `event` (string, Event-Name)
- `run_id` (string, korreliert alle Events eines Runs)

Erwartete Kern-Events (aktuell in [`src/macrolens_poc/cli.py`](src/macrolens_poc/cli.py:55)):
- `command_start`: mindestens `command`, optional Parameter (z. B. `lookback_days`, `sources_matrix_path`)
- `series_run`: mindestens `series_id`, `provider`, `status`, `message`, `new_points`, optional `stored_path`, `error_type`, `error_message`, `revision_overwrites_*`
- `run_summary`: mindestens `started_at`, `ended_at`, `duration_s`, `status_counts` (siehe `run_summary_event()` in [`src/macrolens_poc/logging_utils.py`](src/macrolens_poc/logging_utils.py:42))

(Optional) Breaking Change Klarstellung:
- Änderungen am JSONL-Schema gelten als Breaking Change, wenn Keys entfernt/umbenannt werden oder sich Datentypen/Bedeutung ändern (z. B. `status_counts` von Map → Liste). Reine **Hinzufügungen** neuer optionaler Keys sind nicht-breaking.

---

## 9) Tests: Netzwerkzugriff (Unit vs. Integration)

- Unit-Tests (Default, `python -m pytest`) dürfen **keinen Netzwerkzugriff** benötigen. Provider-Aufrufe werden via Monkeypatch/Stubs isoliert (Beispiel: [`tests/test_m2_provider_robustness.py`](tests/test_m2_provider_robustness.py:12)).
- Integration-Tests (opt-in) dürfen Netzwerkzugriff nutzen, müssen aber:
  - klar markiert sein (z. B. pytest marker `integration`)
  - nur bei explizitem Opt-in laufen (z. B. Environment-Flag wie `MACROLENS_INTEGRATION=1`)
  - Secrets über `.env`/Environment beziehen (siehe Abschnitt 3.1 und [`config/config.example.yaml`](config/config.example.yaml:12))

---

## 10) Provider- & Normalization-Contract

Provider-Contract (Output in `FetchResult.data`):
- DataFrame mit Spalten **`date`** und **`value`** (1D Time Series), siehe Provider-Docs/Code:
  - FRED: [`src/macrolens_poc/sources/fred.py`](src/macrolens_poc/sources/fred.py:26)
  - Yahoo/yfinance: [`src/macrolens_poc/sources/yahoo.py`](src/macrolens_poc/sources/yahoo.py:20)
- `date` ist UTC-normalisiert (timezone-aware), `value` ist numerisch (float; NaNs erlaubt für „missing“ Werte).
- Status ist einer aus `ok|warn|error|missing`.

Normalization-Contract (Pipeline):
- `_normalize_timeseries()` erzwingt Schema `(date,value)`, dedupliziert auf `date` (keep last) und sortiert (siehe [`src/macrolens_poc/pipeline/run_series.py`](src/macrolens_poc/pipeline/run_series.py:31)).
- Storage-Contract (Parquet): `date,value` Spalten; Merge ohne Duplikate; bei Revisionen überschreibt Incoming und loggt Overwrite-Sample (siehe [`src/macrolens_poc/storage/parquet_store.py`](src/macrolens_poc/storage/parquet_store.py:70)).

---

## 11) Minimal Definition of Done (DoD)

- [ ] Änderung ist klein & nachvollziehbar (kein „Mega-Diff“)
- [ ] Repo-first eingehalten: relevante Dateien gelesen/gelinkt (z. B. [`PRD.md`](PRD.md:1))
- [ ] Smoke: `macrolens-poc --help` funktioniert (Entry: [`pyproject.toml`](pyproject.toml:25))
- [ ] Tests: `python -m pytest` grün
- [ ] Keine Secrets/Outputs committet (siehe Abschnitt 3.1 und 7)
- [ ] Logging/Robustheit nicht verschlechtert; JSONL Contract beachtet (Abschnitt 8)
- [ ] Doku aktualisiert, falls Nutzer-/DX-Wert entsteht (mind. [`README.md`](README.md:1), [`CHANGELOG.md`](CHANGELOG.md:1), [`TODO.md`](TODO.md:1))
