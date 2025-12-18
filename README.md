# macrolens_poc

Lokaler Python-PoC für Makro-/Marktdaten-Ingestion, Normalisierung, Storage und Report-Generierung.

## Dokumentation & Referenzen (Single Source of Truth)

| Dokument | Zielgruppe | Zweck / SSoT für... |
|---|---|---|
| [`README.md`](README.md:1) | **Nutzer** | **Quickstart, Installation, Usage, Contracts.** |
| [`docs/PRD.md`](docs/PRD.md:1) | **Alle** | **Requirements, Scope, Architektur-Ziele.** |
| [`AGENTS.md`](AGENTS.md:1) | **Agents** | **Arbeitsregeln für KI-Agenten, Coding-Standards.** |
| [`docs/PROJECT_STATUS.md`](docs/PROJECT_STATUS.md:1) | **Alle** | Aktueller Status-Snapshot, bekannte Probleme. |
| [`TODO.md`](TODO.md:1) | **Contributor** | Aktive Tasks, Backlog, Roadmap. |
| [`CHANGELOG.md`](CHANGELOG.md:1) | **Alle** | Historie der Änderungen (Versionshinweise). |

## Quickstart

### Systemvoraussetzungen

- **OS**: Linux, macOS (Windows via WSL empfohlen).
- **Python**: Version **3.11+** (fixiert in [`pyproject.toml`](pyproject.toml:6)).
- **Dependency Management**: Standard `pip` (oder modern via `uv`).

### Setup & Installation

Setup (virtuelle Umgebung + editable install) und Smoke:

```bash
python3 -m venv .venv
. .venv/bin/activate

# Hinweis zur Umgebung: systemweit kann nur `python3` verfügbar sein; in der aktivierten venv ist i. d. R. auch `python` vorhanden.
python3 -m pip install -e '.[dev]'

macrolens-poc --help
python3 -m pytest
```

### 60-Sekunden Happy Path

```bash
cp .env.example .env
# FRED_API_KEY in .env setzen oder exportieren
export FRED_API_KEY=abcdef123456

# Daten laden (Beispiel: US CPI)
make run_one ID=us_cpi LOOKBACK_DAYS=30

# Report generieren
make report
```

Hinweis: Alternativ funktioniert auch `python3 -m macrolens_poc.cli --help` (z. B. in Targets/CI), entspricht aber dem gleichen Entry-Point wie [`pyproject.toml`](pyproject.toml:27).

## Developer Commands (Make)

Nach `python3 -m pip install -e '.[dev]'` stehen Targets in [`Makefile`](Makefile:1) bereit. Hier das Mapping zu den CLI-Befehlen:

| Make Target | CLI Equivalent | Beschreibung |
|---|---|---|
| `make run_all` | `macrolens-poc run-all` | Ingestion aller aktiven Serien. |
| `make run_one ID=...` | `macrolens-poc run-one --id ...` | Ingestion einer einzelnen Serie. |
| `make report` | `macrolens-poc report` | Generierung des Reports (Markdown/JSON). |
| `make lint` | `ruff check ...` | Statische Code-Analyse (Linting). |
| `make format` | `ruff format ...` | Code-Formatierung. |
| `make smoke` | `pytest -q` | Minimaler Funktionstest. |

*Hinweis: `analyze` ist aktuell nur direkt über das CLI verfügbar (siehe unten).*

Optional: `justfile` bietet äquivalente Shortcuts:

```bash
just run_all
just run_one us_cpi 180
just report
just lint
just format
just smoke
```

## Konfiguration

Konfiguration ist bewusst lokal gehalten (keine Secrets in Git). Vorlagen im Repo:

- Env-Variablen: [`.env.example`](.env.example:1)
- YAML-Konfiguration: [`config/config.example.yaml`](config/config.example.yaml:1)

### Priorität (Precedence)

Die Konfiguration wird in folgender Reihenfolge geladen (höhere Priorität gewinnt):

1.  **CLI Flags** (z. B. `--lookback-days`, `--id`)
2.  **YAML Config** (via `--config`, überschreibt Env/Defaults)
3.  **Environment Variables** (`.env`, z. B. `DATA_TZ`, `FRED_API_KEY`)
4.  **Defaults** (im Code definiert)

### Secrets / `.env` (lokal)

- Lege lokal eine Datei `.env` an (z. B. via `cp .env.example .env`) und setze Werte nur dort.
- `.env` und `.env.*` dürfen **niemals** committet werden; Git ignoriert diese Dateien (siehe [`.gitignore`](.gitignore:21)).
- Provider-Key-Beispiel: FRED liest `FRED_API_KEY` aus der Umgebung (siehe [`.env.example`](.env.example:10)).

Zeitzonen-Regeln (konsequent in Code/Outputs beibehalten):

- `DATA_TZ=UTC` (kanonische Zeitzone für gespeicherte Timestamps; siehe [`.env.example`](.env.example:4))
- `REPORT_TZ=Europe/Vienna` (Darstellung/Reports; siehe [`.env.example`](.env.example:7))

Die gleichen Konventionen existieren auch in der YAML-Konfiguration (`data_tz`, `report_tz`; siehe [`config/config.example.yaml`](config/config.example.yaml:2)).

### Datenquellen (`sources_matrix.yaml`)

Die Definition der Zeitreihen erfolgt zentral in [`config/sources_matrix.yaml`](config/sources_matrix.yaml:1).
Hier werden Provider, Ticker und Metadaten gepflegt.

Beispiel-Eintrag (YAML):

```yaml
- id: us_cpi
  provider: fred
  provider_symbol: CPIAUCSL
  category: macro_us
  frequency_target: daily
  enabled: true
```

## Output-Pfade

Repo-Verzeichnisse sind angelegt (Platzhalter via `.gitkeep`):

- Datenablage: [`data/.gitkeep`](data/.gitkeep:1) (Time-Series Output: `data/series/{id}.parquet`)
- Metadaten-Index: `data/metadata.sqlite` (Serien-Metadaten + Status/letzte Aktualisierung)
- Matrix-Status-Snapshot: `data/matrix_status.json` (per-series `status/last_ok/last_run_at`)
- Logs: [`logs/.gitkeep`](logs/.gitkeep:1) (JSONL: `logs/run-YYYYMMDD.jsonl`)
- Reports: [`reports/.gitkeep`](reports/.gitkeep:1)

Beispiel-Struktur nach einem Run:

```text
data/
├── series/
│   └── us_cpi.parquet    # Time Series (date, value)
├── metadata.sqlite       # Metadaten & Status
└── matrix_status.json    # Snapshot
reports/
├── report_20251215.md     # Generierter Markdown-Report
└── report_20251215.json   # Generierter JSON-Report
```

### Data Contract (Parquet)

Gespeicherte Zeitreihen (`*.parquet`) folgen einem strikten Schema:

-   **Schema**:
    -   `date`: `datetime64[ns, UTC]` (Index, eindeutig)
    -   `value`: `float64` (kann `NaN` für missing values enthalten)
-   **Normalisierung**:
    -   Sortiert nach `date` (aufsteigend).
    -   Dedupliziert auf `date` (Strategie: **keep last** – neuere Werte überschreiben existierende für denselben Zeitstempel).
    -   Revisionen werden erkannt und geloggt, aber im Storage wird der neueste Wert persistiert.

## CLI Usage

```bash
# optional: YAML config (sonst Defaults + .env)
# --config ist globaler Parameter (Typer callback) und gilt für alle Subcommands.

# einzelne Serie (id aus [`config/sources_matrix.yaml`](config/sources_matrix.yaml:1))
macrolens-poc --config config/config.example.yaml run-one --id us_cpi --lookback-days 3650

# ausgewählte Serien (kommagetrennt)
macrolens-poc --config config/config.example.yaml run-selected --ids "us_cpi,btc_usd" --lookback-days 3650

# alle enabled Serien
macrolens-poc --config config/config.example.yaml run-all --lookback-days 3650

# Report aus gespeicherten Serien (Markdown + JSON unter `reports/`)
macrolens-poc --config config/config.example.yaml report

# KI-Analyse (benötigt OPENAI_API_KEY in .env)
macrolens-poc --config config/config.example.yaml analyze --report-file reports/report_latest.json --output reports/analysis.md
```

## Incremental Updates & Backfill

Die Steuerung der Daten-Historie erfolgt primär über den Parameter `--lookback-days`.

### Funktionsweise

- **Fetch**: Es werden Daten für den Zeitraum `[Heute - lookback_days, Heute]` vom Provider abgerufen.
- **Merge**: Die neuen Daten werden mit den bestehenden lokalen Daten (`data/series/*.parquet`) zusammengeführt.
    - **Overwrite**: Existiert ein Datenpunkt für ein Datum bereits, wird er durch den neuen Wert überschrieben. Dies stellt sicher, dass Revisionen (nachträgliche Korrekturen der Provider) übernommen werden.
    - **Append**: Neue Datenpunkte werden hinzugefügt.

### Backfill vs. Update

- **Initialer Backfill**: Um eine Serie initial zu laden, wähle einen großen Zeitraum (z. B. `--lookback-days 3650` für 10 Jahre).
- **Tägliches Update**: Für regelmäßige Updates genügt ein kurzer Zeitraum (z. B. `--lookback-days 5` oder `30`), um fehlende Tage zu ergänzen und jüngste Revisionen zu erfassen.

## Report ausführen

Report-Erzeugung (separater Schritt):

```bash
macrolens-poc --config config/config.example.yaml report
```

Output:

- Reports unter [`reports/`](reports/.gitkeep:1)
- Logs weiterhin unter [`logs/`](logs/.gitkeep:1)

## KI-Analyse (Multi-Model / OpenRouter)

Der `analyze` Befehl nutzt ein oder mehrere LLMs, um die generierten Reports zusammenzufassen.

### Funktionsweise

- **Input**: JSON-Report (aus `macrolens-poc report`).
- **Output**: Markdown-Datei mit der Analyse.
- **Ablauf**: Sequenzielle Abfrage der konfigurierten Modelle (robust gegen Einzelfehler).
- **Provider**: OpenAI-kompatibel (z. B. OpenAI, OpenRouter, LocalAI).

### Konfiguration

Voraussetzung:
- `OPENAI_API_KEY` in `.env` gesetzt.
- `LLM_MODELS`: Liste der Modelle (z. B. `gpt-4o,claude-3-5-sonnet`).
- `LLM_BASE_URL`: Optional für OpenRouter/LocalAI.

### Usage

Der Befehl erfordert explizite Pfade für Input und Output:

```bash
# Analyse mit Default-Modellen
macrolens-poc analyze \
  --report-file reports/report_YYYYMMDD.json \
  --output reports/analysis_YYYYMMDD.md

# Spezifische Modelle (überschreibt Config)
macrolens-poc analyze \
  --report-file reports/report_YYYYMMDD.json \
  --output reports/analysis_YYYYMMDD.md \
  --models "gpt-4o-mini,claude-3-haiku"
```

## Troubleshooting & Common Errors

Häufige Fehler und deren Lösungen:

| Fehler / Symptom | Mögliche Ursache | Lösung |
|---|---|---|
| `ValueError: ... API Key missing` | API-Key nicht gefunden. | Prüfen, ob `.env` existiert und Key enthält (z. B. `FRED_API_KEY`). Variable exportieren oder `.env` laden. |
| `429 Too Many Requests` | Rate Limit des Providers überschritten. | Warten oder Plan prüfen. Bei FRED/Yahoo ggf. `retry_delay` erhöhen. |
| `Yahoo: possibly delisted` | Ticker existiert nicht mehr oder Symbol falsch. | Ticker auf Yahoo Finance Website prüfen. Ggf. in `config/sources_matrix.yaml` korrigieren. |
| `Timezone mismatch` | Systemzeit weicht stark ab. | Sicherstellen, dass die Systemzeit korrekt ist. Intern wird UTC verwendet. |
| `Permission denied` | Fehlende Schreibrechte. | Berechtigungen in `data/` oder `reports/` prüfen (`chmod +w ...`). |
| `Empty Report` / Keine Daten | Fetch war nicht erfolgreich oder Lookback zu kurz. | Logs in `logs/` prüfen. Ggf. `--lookback-days` erhöhen. |

Details zum aktuellen Projektstatus siehe [`docs/PROJECT_STATUS.md`](docs/PROJECT_STATUS.md:1).
Nächste Arbeitspakete siehe [`TODO.md`](TODO.md:1).
