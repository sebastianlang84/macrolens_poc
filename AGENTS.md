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

## 2) Projekt-Kontext (Kurz)

- Ziel: lokaler Python-PoC für Makro-/Marktdaten-Ingestion, Normalisierung, Storage und Report-Generierung.
- Anforderungen/Scope: siehe [`PRD.md`](PRD.md:1).

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
