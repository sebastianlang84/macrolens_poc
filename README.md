# macrolens_poc

Lokaler Python-PoC für Makro-/Marktdaten-Ingestion, Normalisierung, Storage und Report-Generierung (Zielbild aus [`PRD.md`](PRD.md:20)).

## Quickstart

Voraussetzungen:

- Python >= 3.11 (siehe [`pyproject.toml`](pyproject.toml:6))

Setup (virtuelle Umgebung + editable install) und CLI-Help:

```bash
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -e '.[dev]'
python -m macrolens_poc.cli --help
```

## Konfiguration

Konfiguration ist bewusst lokal gehalten (keine Secrets in Git). Vorlagen im Repo:

- Env-Variablen: [`.env.example`](.env.example:1)
- YAML-Konfiguration: [`config/config.example.yaml`](config/config.example.yaml:1)

Provider Keys:

- FRED: `FRED_API_KEY` (siehe [`.env.example`](.env.example:1))

Zeitzonen-Regeln (konsequent in Code/Outputs beibehalten):

- `DATA_TZ=UTC` (kanonische Zeitzone für gespeicherte Timestamps; siehe [`.env.example`](.env.example:4))
- `REPORT_TZ=Europe/Vienna` (Darstellung/Reports; siehe [`.env.example`](.env.example:7))

Die gleichen Konventionen existieren auch in der YAML-Konfiguration (`data_tz`, `report_tz`; siehe [`config/config.example.yaml`](config/config.example.yaml:2)).

## Output-Pfade

Repo-Verzeichnisse sind angelegt (Platzhalter via `.gitkeep`):

- Datenablage: [`data/.gitkeep`](data/.gitkeep:1) (Time-Series Output: `data/series/{id}.parquet`)
- Logs: [`logs/.gitkeep`](logs/.gitkeep:1) (JSONL: `logs/run-YYYYMMDD.jsonl`)
- Reports: [`reports/.gitkeep`](reports/.gitkeep:1)

## Status / Scope

- M0: Repo + Skeleton ✅
- M1/M2 (minimal): Provider (FRED + Yahoo via yfinance) + Pipeline + Parquet-Storage ✅

CLI Usage:

```bash
# einzelne Serie (id aus [`config/sources_matrix.yaml`](config/sources_matrix.yaml:1))
python -m macrolens_poc.cli run-one --id us_cpi --lookback-days 3650

# alle enabled Serien
python -m macrolens_poc.cli run-all --lookback-days 3650

# Report aus gespeicherten Serien (Markdown + JSON unter `reports/`)
python -m macrolens_poc.cli report
```

Nächste Arbeitspakete (M3+) siehe [`TODO.md`](TODO.md:1) und Roadmap / Anforderungen in [`PRD.md`](PRD.md:195).

## Merge-Konflikte in Docs vermeiden

Für häufig geänderte Textdateien ist `merge=union` vordefiniert (siehe [`.gitattributes`](.gitattributes:1)), damit unabhängige Änderungen an Changelog/TODO/Status/README automatisch zusammengeführt werden.
