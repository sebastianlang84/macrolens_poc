# macrolens_poc

Lokaler Python-PoC für Makro-/Marktdaten-Ingestion, Normalisierung, Storage und Report-Generierung.

**Wichtige Links:**
- **Requirements & Scope**: [`PRD.md`](PRD.md:1)
- **Aktueller Status**: [`PROJECT_STATUS.md`](PROJECT_STATUS.md:1)
- **Agent Rules**: [`AGENTS.md`](AGENTS.md:1)
- **Changelog**: [`CHANGELOG.md`](CHANGELOG.md:1)

## Quickstart

Voraussetzungen:

- Python >= 3.11 (siehe [`pyproject.toml`](pyproject.toml:6))

Setup (virtuelle Umgebung + editable install) und Smoke:

```bash
python3 -m venv .venv
. .venv/bin/activate

# Hinweis zur Umgebung: systemweit kann nur `python3` verfügbar sein; in der aktivierten venv ist i. d. R. auch `python` vorhanden.
python3 -m pip install -e '.[dev]'

macrolens-poc --help
python3 -m pytest
```

Hinweis: Alternativ funktioniert auch `python3 -m macrolens_poc.cli --help` (z. B. in Targets/CI), entspricht aber dem gleichen Entry-Point wie [`pyproject.toml`](pyproject.toml:27).

## Developer Commands (Make)

Nach `python3 -m pip install -e '.[dev]'` stehen Targets in [`Makefile`](Makefile:1) bereit:

- `run_all` – alle enabled Serien backfillen (`LOOKBACK_DAYS` optional, Default: `3650`).
- `run_one` – eine Serie per `--id` (`make run_one ID=<series_id> ...`).
- `report` – Markdown/JSON-Report unter [`reports/.gitkeep`](reports/.gitkeep:1) erzeugen.
- `lint` – statische Prüfung via `ruff` auf `src/` und `tests/`.
- `format` – Formatierung via `black` auf `src/` und `tests/`.
- `smoke` – kurzer Check via `pytest -q` (Minimaltest).

Beispiele:

```bash
make run_all
make run_one ID=us_cpi LOOKBACK_DAYS=180
make report
make lint
make format
make smoke
```

## Konfiguration

Konfiguration ist bewusst lokal gehalten (keine Secrets in Git). Vorlagen im Repo:

- Env-Variablen: [`.env.example`](.env.example:1)
- YAML-Konfiguration: [`config/config.example.yaml`](config/config.example.yaml:1)

### Secrets / `.env` (lokal)

- Lege lokal eine Datei `.env` an (z. B. via `cp .env.example .env`) und setze Werte nur dort.
- `.env` und `.env.*` dürfen **niemals** committet werden; Git ignoriert diese Dateien (siehe [`.gitignore`](.gitignore:21)).
- Provider-Key-Beispiel: FRED liest `FRED_API_KEY` aus der Umgebung (siehe [`.env.example`](.env.example:10)).

Zeitzonen-Regeln (konsequent in Code/Outputs beibehalten):

- `DATA_TZ=UTC` (kanonische Zeitzone für gespeicherte Timestamps; siehe [`.env.example`](.env.example:4))
- `REPORT_TZ=Europe/Vienna` (Darstellung/Reports; siehe [`.env.example`](.env.example:7))

Die gleichen Konventionen existieren auch in der YAML-Konfiguration (`data_tz`, `report_tz`; siehe [`config/config.example.yaml`](config/config.example.yaml:2)).

## Output-Pfade

Repo-Verzeichnisse sind angelegt (Platzhalter via `.gitkeep`):

- Datenablage: [`data/.gitkeep`](data/.gitkeep:1) (Time-Series Output: `data/series/{id}.parquet`)
- Metadaten-Index: `data/metadata.sqlite` (Serien-Metadaten + Status/letzte Aktualisierung)
- Matrix-Status-Snapshot: `data/matrix_status.json` (per-series `status/last_ok/last_run_at`)
- Logs: [`logs/.gitkeep`](logs/.gitkeep:1) (JSONL: `logs/run-YYYYMMDD.jsonl`)
- Reports: [`reports/.gitkeep`](reports/.gitkeep:1)

## Status / Scope

- M0: Repo + Skeleton ✅
- M1/M2 (minimal): Provider (FRED + Yahoo via yfinance) + Pipeline + Parquet-Storage ✅

CLI Usage:

```bash
# optional: YAML config (sonst Defaults + .env)
# --config ist globaler Parameter (Typer callback) und gilt für alle Subcommands.

# einzelne Serie (id aus [`config/sources_matrix.yaml`](config/sources_matrix.yaml:1))
macrolens-poc --config config/config.example.yaml run-one --id us_cpi --lookback-days 3650

# alle enabled Serien
macrolens-poc --config config/config.example.yaml run-all --lookback-days 3650

# Report aus gespeicherten Serien (Markdown + JSON unter `reports/`)
macrolens-poc --config config/config.example.yaml report
```

## Minimal Run (durchgeführt)

Ausgeführter Minimal-Run:

```bash
macrolens-poc --config config/config.example.yaml run-all --lookback-days 10
```

Beobachtungen aus dem Testlauf (Exit-Code 0):

- Smoke war grün: `macrolens-poc --help` ok, `python3 -m pytest` → 22 passed.
- Run-Summary im JSONL: `ok=4`, `warn=5`, `error=6`, `missing=0`.
- Artefakte wurden unter [`data/`](data/.gitkeep:1) geschrieben; Logs unter [`logs/`](logs/.gitkeep:1), Beispiel: [`logs/run-20251212.jsonl`](logs/run-20251212.jsonl:1).
- Durch [`run_all()`](src/macrolens_poc/cli.py:160) werden **keine** Reports erzeugt; Reports laufen separat über [`report()`](src/macrolens_poc/cli.py:302).

### Häufige Warnungen/Errors (aus dem Testlauf)

- FRED: bei `--lookback-days 10` können für niedrigfrequente Makroserien `0 observations` auftreten (Status `warn`). Empfehlung: Lookback erhöhen (z. B. `3650`).
- Yahoo/yfinance: mehrere Serien schlugen fehl mit `TypeError: arg must be a list, tuple, 1-d array, or Series` (Status `error`) sowie einer `FutureWarning` bzgl. `auto_adjust` (siehe [`src/macrolens_poc/sources/yahoo.py`](src/macrolens_poc/sources/yahoo.py:1)).
- FRED: ein Error (Serie `gold_usd`) wurde als `error` gezählt, aber ohne `error_type`/`error_message` im Subtask-Report; Details stehen im JSONL (Logfelder werden nur geschrieben, wenn sie im Ergebnis gesetzt sind; siehe [`_log_series_run()`](src/macrolens_poc/cli.py:86)).

## Report danach ausführen

Report-Erzeugung (separater Schritt):

```bash
macrolens-poc --config config/config.example.yaml report
```

Output:

- Reports unter [`reports/`](reports/.gitkeep:1)
- Logs weiterhin unter [`logs/`](logs/.gitkeep:1)

Nächste Arbeitspakete (M3+) siehe [`TODO.md`](TODO.md:1) und Roadmap / Anforderungen in [`PRD.md`](PRD.md:195).
