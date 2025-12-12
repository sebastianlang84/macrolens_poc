# TODO

## Now (M1/M2) — Matrix + Provider + Pipeline/Storage

- [x] Data-Source-Matrix: Schema + Datei definieren (YAML/CSV/JSON) gem. [`PRD.md`](PRD.md:65)
- [x] Matrix-Loader + Schema-Validation (z. B. pydantic)
- [x] Matrix-Statusfelder automatisch pflegen (`last_ok`, `status`, „stale“ via Altersberechnung)
- [x] Provider-Adapter: FRED (Series by id, start/end)
- [x] Provider-Adapter: Yahoo Finance (EOD Close für Ticker)
- [ ] Provider-Robustheit: Timeout/Retry/Backoff (Provider-Fehler dürfen Run nicht crashen)
- [x] Normalize/Validate: einheitliches Datums-/Zeitzonen-Regime festlegen und konsequent umsetzen
- [x] Normalize: Dedupe + sort + gap handling (Daily Index, NaNs)
- [x] Validate: empty / stale / missing (Status `ok/warn/error/missing`)
- [x] Storage: Time series pro Serie (Parquet bevorzugt), Append/Merge ohne Duplikate
- [ ] Revisionsdaten (z. B. FRED): Overwrite-Policy + Logging für rückwirkende Änderungen
- [x] CLI: Daily Run (alle `enabled=true`) + On-Demand Run (Liste von `id`s)
- [x] Run Summary: ok/warn/error/missing + Laufzeit + „0 neue Punkte“ bei No-Op Run

## Next (M3) — Report v1

- [x] Aggregator: letzter Wert + Δ1d/Δ5d/Δ21d
- [ ] Simple Risk Flags (Heuristiken) gem. [`PRD.md`](PRD.md:93)
- [x] Export: Markdown + JSON (z. B. `reports/report-YYYYMMDD.md` + `.json`)

## Later — Monitoring, DX, Open Questions

- [x] Stale-series detection + „Matrix status“ Export
- [ ] Optional: SQLite Index für Metadaten
- [ ] DX: Makefile/justfile (z. B. `run_all`, `run_one`, `report`)
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