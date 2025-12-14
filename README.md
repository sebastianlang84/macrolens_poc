# macrolens_poc

Lokaler Python-PoC für Makro-/Marktdaten-Ingestion, Normalisierung, Storage und Report-Generierung.

## Dokumentation & Referenzen

| Dokument | Zielgruppe | Inhalt |
|---|---|---|
| [`README.md`](README.md:1) | **Nutzer** | Quickstart, Installation, Usage, Konfiguration. |
| [`PROJECT_STATUS.md`](PROJECT_STATUS.md:1) | **Alle** | Aktueller Status-Snapshot, bekannte Probleme, Entscheidungen. |
| [`PRD.md`](PRD.md:1) | **Alle** | Requirements, Scope, Architektur-Ziele. |
| [`AGENTS.md`](AGENTS.md:1) | **Contributor/Agents** | Arbeitsregeln, Coding-Standards, Commit-Konventionen. |
| [`TODO.md`](TODO.md:1) | **Contributor** | Aktive Tasks, Backlog, Roadmap. |
| [`CHANGELOG.md`](CHANGELOG.md:1) | **Alle** | Historie der Änderungen (Versionshinweise). |

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

## CLI Usage

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

## Report ausführen

Report-Erzeugung (separater Schritt):

```bash
macrolens-poc --config config/config.example.yaml report
```

Output:

- Reports unter [`reports/`](reports/.gitkeep:1)
- Logs weiterhin unter [`logs/`](logs/.gitkeep:1)

Details zum aktuellen Projektstatus siehe [`PROJECT_STATUS.md`](PROJECT_STATUS.md:1).
Nächste Arbeitspakete siehe [`TODO.md`](TODO.md:1).
