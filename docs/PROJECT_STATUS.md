# Project Status (Snapshot)

## Overview
- **Status:** Feature Complete (POC) / Hardening Phase / Documentation Refinement.
- **Milestone M4 (KI-Analyse) Completed:** `analyze` command integrates OpenAI for market summaries.
- **Documentation Refined:** `README.md` und `docs/PRD.md` wurden aktualisiert (Matrix Extensions, Data Contract).
- **Live-Test Analysis Completed:** Detaillierte Auswertung und Gap-Analyse unter [`docs/GAP_ANALYSIS_LIVE_TEST.md`](docs/GAP_ANALYSIS_LIVE_TEST.md:1).
- **Core Pipeline:** Ingestion, Normalization, Storage (Parquet) fully functional.
- **New Features:**
    - **Stale Detection:** Warns about outdated series based on configured frequency.
    - **Determinism:** Strict `as_of` logic (UTC) ensures reproducible runs.
- Current providers: FRED and Yahoo Finance (yfinance).
- CLI commands: `run-all`, `run-one`, `run-selected`, `report`, `analyze`.

## Latest Test Run (2025-12-15)

**Status:** Abgeschlossen & Analysiert.
**Ergebnisse:** Siehe [`docs/GAP_ANALYSIS_LIVE_TEST.md`](docs/GAP_ANALYSIS_LIVE_TEST.md:1).

Fakten aus dem durchgeführten Testlauf (Fixes & Stabilization):

- **Data Quality:** Yahoo Finance Timezone-Issues identifiziert und behoben (Upgrade `yfinance`).
- **LLM Analysis:** Bedarf für robustere Multi-Model Strategie erkannt (siehe [`docs/design/DESIGN_ROBUST_ANALYSIS.md`](docs/design/DESIGN_ROBUST_ANALYSIS.md:1)).
- **Config Loading:** Erfolgreich verifiziert, dass `.env` Variablen korrekt geladen und priorisiert werden (Fix für `Config` Klasse).
- **LLM Integration:** Erfolgreiche Tests mit OpenAI und OpenRouter (via `debug_llm_v2.py`). Modelle werden korrekt instanziiert und API-Keys sicher geladen.
- Smoke war grün: `macrolens-poc --help` ok, `python3 -m pytest` → 22 passed.
- Minimal-Run: `macrolens-poc --config config/config.example.yaml run-all --lookback-days 10`.
- Exit-Code 0, aber Status im Log: `ok=4`, `warn=5`, `error=6`, `missing=0` (JSONL unter [`logs/run-20251212.jsonl`](logs/run-20251212.jsonl:1)).
- Artefakte: unter [`data/`](data/.gitkeep:1); Reports wurden durch `run-all` nicht erzeugt (separat via [`report()`](src/macrolens_poc/cli.py:302)).

Bekannte Probleme (aus dem Lauf):

- Yahoo/yfinance: mehrere Serien mit `TypeError: arg must be a list, tuple, 1-d array, or Series` (sowie `FutureWarning` bzgl. `auto_adjust`; siehe [`src/macrolens_poc/sources/yahoo.py`](src/macrolens_poc/sources/yahoo.py:1)).
- FRED: mehrere Makroserien liefern bei `--lookback-days 10` `0 observations` (wahrscheinlich erwartbar je nach Frequenz) → Empfehlung: Lookback erhöhen.
- FRED: ein Error (Serie `gold_usd`) wurde als `error` gezählt, aber ohne `error_type/error_message` in der per-series Event-Zeile; Details stehen im JSONL (vgl. [`_log_series_run()`](src/macrolens_poc/cli.py:86)).

Umgebungshinweis:

- Systemweit war `python` nicht im PATH, `python3` ist verfügbar.

## Context & Decisions
- Data provider continuity needs a plan before further build-out.
- Additional coverage (regions/series) should align with reporting and storage constraints.

| Topic | Status | Next Step | Owner |
| --- | --- | --- | --- |
| Yahoo Finance dependency | Reliant on `yfinance`; no SLA and occasional blocking/changes. | Evaluate replacement provider (e.g., Polygon/Alphavantage) and prototype adapter with retry/backoff hooks. | @owner-product |
| Coverage expansion (regions/series) | Current matrix covers US macro + selected risk assets/crypto; no non-US macro yet. | Define target regions/series list and storage impact; add to config matrix and align with status/health tracking. | @owner-data |

## Open Questions
- Welche Yahoo-Alternative priorisieren wir für Equity/FX/Commodities (Kosten, Limits, SLA)?
- Welche zusätzlichen Regionen/Serien sind für den nächsten Increment verbindlich (EU/UK/JP; Rates vs. Equities)?

## Observations
- Reporting command generates Markdown/JSON artifacts with last values and Δ windows; risk flags are implemented as a minimal deterministic `risk_regime` (unknown/risk_on/risk_off/neutral), currently based on VIX + S&P500 Δ5d.
- Provider robustness: timeout + retry/backoff exists (deterministic exponential backoff in [`src/macrolens_poc/retry_utils.py`](src/macrolens_poc/retry_utils.py:10)); yfinance currently retries on any exception (broad).
- Revision-aware storage merge is implemented (incoming overwrites by date, revision overwrites are detected + sampled; siehe [`src/macrolens_poc/storage/parquet_store.py`](src/macrolens_poc/storage/parquet_store.py:70)).
- Per-series status is persisted to `data/matrix_status.json` (last_ok/last_run_at/last_error), and metadata is persisted to `data/metadata.sqlite` (siehe [`src/macrolens_poc/sources/matrix_status.py`](src/macrolens_poc/sources/matrix_status.py:45) und [`src/macrolens_poc/storage/metadata_db.py`](src/macrolens_poc/storage/metadata_db.py:1)).
- Storage layout is fixed to `data/series/{id}.parquet` (kein Partitioning); für PoC ok, aber Skalierung/Indexing ggf. später.
- **Coverage:** Added `us_hy_spread` and `us_indpro` to tracking.

## Suggested Next Steps
- [Done] Narrow retry conditions for yfinance and log retry attempts (attempt index + delay) for better diagnosability.
- [Done] Refine LLM prompts for more specific investment horizon analysis.
- **Implement Matrix Extensions:** Add new series defined in `docs/PRD.md` to `config/sources_matrix.yaml`.
- Extend risk flag rule set and include explicit dependencies/assumptions in report metadata.
- Consider a manifest/partitioning strategy if series count grows beyond the current PoC scope.

## Review Cadence
- Wöchentliches Update der offenen Fragen/Entscheidungen im Planning; Kurz-Check im Standup bis Klarheit zu Provider- und Coverage-Entscheidungen.
