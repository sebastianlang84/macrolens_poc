# Schwachstellenanalyse (Vulnerabilities) - macrolens_poc

Dieses Dokument beschreibt die identifizierten Schwachstellen im Projekt `macrolens_poc`, kategorisiert nach ihrer Art, sowie Empfehlungen zu deren Behebung.

## 1. Robustheit (Robustness)

### 1.1 Fehlende Fehlerbehandlung beim Lesen von Parquet-Dateien (Behoben)
*   **Datei**: [`src/macrolens_poc/storage/parquet_store.py`](src/macrolens_poc/storage/parquet_store.py:34)
*   **Status**: Behoben (Fix 1.1)
*   **Beschreibung**: Der Aufruf von `pd.read_parquet(path)` erfolgt ohne Absicherung durch einen `try-except`-Block. Wenn die Datei beschädigt ist, kein gültiges Parquet-Format aufweist oder durch einen abgebrochenen Schreibvorgang korrupt ist, stürzt die Anwendung ab.
*   **Lösung**: Einbetten des Ladevorgangs in einen `try-except`-Block. Bei Fehlern wird nun ein leeres DataFrame zurückgegeben und der Fehler geloggt, statt den Run abzubrechen.

### 1.2 Fragile MultiIndex-Logik im Yahoo-Provider
*   **Datei**: [`src/macrolens_poc/sources/yahoo.py`](src/macrolens_poc/sources/yahoo.py:145)
*   **Beschreibung**: Die Handhabung von MultiIndex-Spalten, die bei neueren `yfinance`-Versionen auftreten, ist komplex und fehleranfällig. Sie verlässt sich darauf, dass das Symbol exakt in den Spalten-Levels gefunden wird. Änderungen in der `yfinance`-API können diese Logik leicht brechen.
*   **Empfehlung**: Implementierung einer robusteren Normalisierungsschicht für Provider-Outputs. Nutzung von expliziten Schemaprüfungen nach dem Download.

### 1.3 `matrix-status` kann bei korruptem Datum crashen (Behoben)
*   **Datei**: [`src/macrolens_poc/cli.py`](src/macrolens_poc/cli.py:591)
*   **Status**: Behoben (Fix 1.3)
*   **Beschreibung**: Beim Rendern der Status-Tabelle wird `date.fromisoformat(entry.last_observation_date)` ohne Fehlerbehandlung aufgerufen. Ein korruptes/unerwartetes Datumsformat (z. B. aus einer manuell editierten Status-Datei oder einem partiell geschriebenen Artefakt) führt zu einem `ValueError` und lässt das CLI-Kommando abstürzen.
*   **Lösung**: Parsing in `try/except` gekapselt. Bei ungültigen Werten wird nun `N/A` angezeigt.

### 1.4 Ungültige Zeitzone kann Report-Generierung crashen (Behoben)
*   **Betroffen**: [`src/macrolens_poc/report/v1.py`](src/macrolens_poc/report/v1.py:231) und Hinweis in [`src/macrolens_poc/config.py`](src/macrolens_poc/config.py:81)
*   **Status**: Behoben (Fix 1.4)
*   **Beschreibung**: `ZoneInfo(settings.report_tz)` wird ohne Validierung/Fehlerbehandlung instanziert. Eine ungültige oder nicht installierte Zeitzone führt zu `ZoneInfoNotFoundError` und bricht die Report-Generierung ab.
*   **Lösung**: Zeitzonen-Validierung in `Settings` (Pydantic validator) und Fallback auf `UTC` in der Report-Generierung implementiert.

### 1.5 Lokales DoS-Risiko: SQLite „database is locked“ ohne Timeout/Busy-Handling (Behoben)
*   **Betroffen**: [`src/macrolens_poc/storage/metadata_db.py`](src/macrolens_poc/storage/metadata_db.py:68) und CLI-Aufruf ohne Fehlerkapselung in [`src/macrolens_poc/cli.py`](src/macrolens_poc/cli.py:69)
*   **Status**: Behoben (Fix 1.5)
*   **Beschreibung**: Der SQLite-Zugriff nutzt `sqlite3.connect(...)` ohne explizites Busy-/Timeout-Handling. Bei parallelen Runs oder externen Zugriffen kann `sqlite3.OperationalError: database is locked` auftreten. Da der Metadaten-Upsert im CLI nicht abgefangen wird, kann ein einzelner DB-Lock den gesamten Run abbrechen.
*   **Lösung**: Verbindung wird mit `timeout=10.0` geöffnet. Zusätzlich werden DB-Write-Fehler in der CLI abgefangen und als Warnung geloggt, statt den Run abzubrechen.

## 2. Sicherheit (Security)

### 2.1 Risiko der Secret-Exposition in der Konfiguration (Behoben)
*   **Datei**: [`src/macrolens_poc/config.py`](src/macrolens_poc/config.py:21)
*   **Status**: Behoben (Fix 2.1)
*   **Beschreibung**: Das Feld `api_key` in `LLMConfig` ermöglicht das Setzen von Secrets direkt im Konfigurationsobjekt. Dies erhöht das Risiko, dass API-Keys versehentlich in Logs (z. B. durch `model_dump()`) oder Fehlermeldungen auftauchen.
*   **Lösung**: Sensitive Felder in der Konfiguration wurden als `SecretStr` markiert, um versehentliche Exposition in Logs/Serialisierung zu verhindern.

### 2.2 Fehlende Pfadvalidierung in der CLI (Behoben)
*   **Datei**: [`src/macrolens_poc/cli.py`](src/macrolens_poc/cli.py:39)
*   **Status**: Behoben (Fix 2.2)
*   **Beschreibung**: Die Funktion `_ensure_dirs` erstellt Verzeichnisse basierend auf den Pfaden in den `Settings`. Es findet keine Prüfung statt, ob diese Pfade innerhalb des erlaubten Arbeitsverzeichnisses liegen (Gefahr von Path Traversal, falls Konfigurationsdateien aus unsicheren Quellen geladen werden).
*   **Lösung**: Validierung via `path.resolve()` und `is_relative_to(Path.cwd())` implementiert.

### 2.3 Path Traversal über `SeriesSpec.id` beim Lesen/Schreiben von Parquet (Behoben)
*   **Betroffen**: Schreibpfad in [`src/macrolens_poc/pipeline/run_series.py`](src/macrolens_poc/pipeline/run_series.py:176), `SeriesSpec.id` Definition in [`src/macrolens_poc/sources/matrix.py`](src/macrolens_poc/sources/matrix.py:13), Lesepfad im Report in [`src/macrolens_poc/report/v1.py`](src/macrolens_poc/report/v1.py:246)
*   **Status**: Behoben (Fix 2.3)
*   **Beschreibung**: Der Dateiname für Parquet wird aus `spec.id` konstruiert (`data/series/{id}.parquet`) ohne Sanitization. Enthält `id` Pfadseparatoren oder Sequenzen wie `../`, kann der resultierende Pfad aus dem vorgesehenen `data/series/`-Verzeichnis ausbrechen.
*   **Lösung**: `SeriesSpec.id` wird nun via Pydantic-Validator gegen Path-Traversal-Sequenzen geprüft. Zusätzlich erfolgt eine Pfad-Normalisierung und Validierung gegen das Basisverzeichnis in der Pipeline und im Report.

### 2.4 `analyze` kann beliebige Dateien truncaten/überschreiben (ungeprüfter Output-Pfad) (Behoben)
*   **Betroffen**: Truncate in [`src/macrolens_poc/llm/service.py`](src/macrolens_poc/llm/service.py:67) und CLI-Option in [`src/macrolens_poc/cli.py`](src/macrolens_poc/cli.py:490)
*   **Status**: Behoben (Fix 2.4)
*   **Beschreibung**: Der `--output`-Pfad wird direkt verwendet und beim Start der Analyse per `output_path.write_text("", ...)` geleert. Damit kann ein Nutzer (oder ein Skript mit falschem Pfad) beliebige Dateien im Dateisystem überschreiben/truncaten.
*   **Lösung**: Pfadvalidierung im CLI-Kommando `analyze` implementiert. Schreibzugriffe sind nur innerhalb von `settings.paths.reports_dir` erlaubt.

## 3. Datenintegrität (Data Integrity)

### 3.1 Nicht-atomare Schreibvorgänge bei Parquet-Dateien (Behoben)
*   **Datei**: [`src/macrolens_poc/storage/parquet_store.py`](src/macrolens_poc/storage/parquet_store.py:152)
*   **Status**: Behoben (Fix 3.1)
*   **Beschreibung**: `merged.to_parquet(path, index=False)` überschreibt die Zieldatei direkt. Wenn der Prozess während des Schreibens unterbrochen wird (z. B. Systemabsturz, Stromausfall), ist die Datei korrupt und die historischen Daten sind verloren.
*   **Lösung**: Implementierung von atomaren Schreibvorgängen mittels temporärer Datei und `os.replace`.

### 3.2 Report-Artefakte werden nicht-atomar geschrieben (MD/JSON Inkonsistenz möglich)
*   **Betroffen**: Markdown-Write in [`src/macrolens_poc/report/v1.py`](src/macrolens_poc/report/v1.py:209) und JSON-Write in [`src/macrolens_poc/report/v1.py`](src/macrolens_poc/report/v1.py:217)
*   **Beschreibung**: Report-Dateien werden direkt in die Zielpfade geschrieben. Bei Abbruch während des Schreibens oder zwischen MD- und JSON-Write können (a) partielle/korrupten Dateien entstehen und (b) MD/JSON-Versionen nicht zusammenpassen.
*   **Empfehlung**: Atomare Writes (Tempfile + `os.replace`) für beide Artefakte, idealerweise als „commit“ in definierter Reihenfolge. Optional: zusätzliches Manifest/Checksum, um konsistente Paare zu erkennen.

### 3.3 Observability/Datenintegrität: JSONL-Logfile kollidiert pro Tag (parallele Runs interleaven)
*   **Betroffen**: Tagesbasierter Logpfad in [`src/macrolens_poc/logging_utils.py`](src/macrolens_poc/logging_utils.py:23) und Append-Write in [`src/macrolens_poc/logging_utils.py`](src/macrolens_poc/logging_utils.py:38)
*   **Beschreibung**: `default_log_path()` schreibt alle Runs eines Tages in dieselbe Datei (`run-YYYYMMDD.jsonl`). Bei parallelen Runs (oder mehreren Prozessen) können Logzeilen interleaven; zudem werden Events verschiedener Runs in einem File vermischt, was Debugging/Archivierung erschwert.
*   **Empfehlung**: Logfile pro Run eindeutig machen (z. B. `run-{YYYYMMDD}-{HHMMSS}-{run_id}.jsonl`) oder pro Prozess einen exklusiven Writer nutzen (File-Lock). Zusätzlich: optionaler „index“/Symlink pro Tag für bequemes Browsing.

## 4. LLM-Konfiguration

### 4.1 Inkonsistente Modell-Identifier
*   **Betroffen**: [`tests/test_llm_reasoning.py`](tests/test_llm_reasoning.py:1) und [`src/macrolens_poc/config.py`](src/macrolens_poc/config.py:18)
*   **Beschreibung**: Es werden fiktive oder veraltete Modell-Identifier verwendet (z. B. `gpt-5.2`). Dies führt zu Fehlschlägen in Tests, wenn die Logik spezifische Strings erwartet, die nicht mit den Defaults übereinstimmen.
*   **Empfehlung**: Verwendung von existierenden Modell-Identifiern als Defaults (z. B. `gpt-4o`, `o1-preview`). Synchronisation der Test-Erwartungen mit der Konfiguration. WAAAASS WSOLL DER SHIT????!!!

### 4.2 Fiktive Default-Modelle
*   **Datei**: [`src/macrolens_poc/config.py`](src/macrolens_poc/config.py:24)
*   **Beschreibung**: Die Standardwerte für Modelle sind Platzhalter (`gpt-5.2`), die in einer realen Umgebung sofort zu Fehlern führen würden.
*   **Empfehlung**: Umstellung auf produktiv verfügbare Modelle oder explizite Kennzeichnung als Platzhalter, die eine Konfiguration erfordern.

### 4.3 Prompt-Injection Risiko: Report-JSON wird 1:1 in den User-Prompt injiziert (Behoben)
*   **Betroffen**: Prompt-Injection in [`src/macrolens_poc/llm/service.py`](src/macrolens_poc/llm/service.py:58) und Prompt-Template in [`src/macrolens_poc/llm/prompts/user.md`](src/macrolens_poc/llm/prompts/user.md:1)
*   **Status**: Behoben (Fix 4.3)
*   **Beschreibung**: Der JSON-Report wird per String-Replacement in den User-Prompt eingebettet. Enthält der Report (direkt oder indirekt) prompt-artige Inhalte („ignore previous instructions“, Tool-Aufrufe, Datenexfiltration), können Modelle diese Anweisungen trotz Codeblock interpretieren. Das Risiko steigt, wenn Report-Inhalte aus nicht-vertrauenswürdigen Quellen stammen oder später Textfelder hinzukommen.
*   **Lösung**: Prompt-Härtung durch klare Delimiter (`<report_data>`) und explizite Sicherheitsanweisungen im System-Prompt, die das Modell anweisen, Daten strikt als solche zu behandeln.

### 4.4 DoS/Kosten-Risiko: keine Größen-/Token-Limits + hohe `max_tokens` Defaults (Behoben)
*   **Betroffen**: Unbegrenzte Report-Injection in [`src/macrolens_poc/llm/service.py`](src/macrolens_poc/llm/service.py:41) und modellstring-basierte Token-Defaults in [`src/macrolens_poc/llm/openai_provider.py`](src/macrolens_poc/llm/openai_provider.py:82)
*   **Status**: Behoben (Fix 4.4)
*   **Beschreibung**: Der Report wird ohne Größenlimit geladen/pretty-printed und vollständig in den Prompt injiziert. Gleichzeitig setzt der Provider für bestimmte Modellstrings sehr hohe `max_tokens` Defaults. Große Reports können zu (a) Fehlern/Timeouts, (b) stark erhöhten Kosten oder (c) lokalen Ressourcenproblemen führen.
*   **Lösung**: Einführung eines Größenlimits für injizierte Reports (max. 50.000 Zeichen) und Umstellung auf konservativere `max_tokens` Defaults für Reasoning-Modelle.

### 4.5 Endpoint-Trust/Privacy: `base_url` beliebig konfigurierbar + Logging des Endpoints
*   **Betroffen**: `base_url` aus Env/YAML in [`src/macrolens_poc/config.py`](src/macrolens_poc/config.py:108) / [`src/macrolens_poc/config.py`](src/macrolens_poc/config.py:139) und Provider-Init-Logging in [`src/macrolens_poc/llm/openai_provider.py`](src/macrolens_poc/llm/openai_provider.py:19)
*   **Beschreibung**: Durch die freie Konfiguration von `base_url` kann Traffic (inkl. API-Key und Report-Inhalte) an beliebige OpenAI-kompatible Endpoints gesendet werden (Supply-Chain/Privacy-Risiko). Zusätzlich wird der Endpoint im Log ausgegeben, was in manchen Umgebungen sensitive Infrastrukturdetails leaken kann.
*   **Empfehlung**: Allowlist/Policy für `base_url` (z. B. nur `https://api.openai.com` oder explizite, dokumentierte Provider). Endpoint-Logging reduzieren oder auf Hostname ohne Query/Secrets redakten. Optional: separate Config-Option „trusted_endpoints“ + Warnung/Fail-closed bei unbekannten Hosts.

## 5. Performance

### 5.1 Ineffizientes Logging-I/O (Behoben)
*   **Datei**: [`src/macrolens_poc/logging_utils.py`](src/macrolens_poc/logging_utils.py:38)
*   **Status**: Behoben (Fix 5.1)
*   **Beschreibung**: Jeder `log()`-Aufruf öffnet und schließt die Datei (`with self.path.open("a", ...)`). Bei einer hohen Anzahl an Events (z. B. viele Zeitreihen) führt dies zu unnötigem Overhead durch Dateisystem-Handles.
*   **Lösung**: Der `JsonlLogger` hält nun den File-Handle während eines Runs offen (via Context Manager), um den I/O-Overhead zu minimieren.

## 6. Supply Chain & Reproduzierbarkeit

### 6.1 Dependencies nur lower-bounded (`>=`), kein Lockfile/Constraints (Behoben)
*   **Betroffen**: Dependency-Spezifikation in [`pyproject.toml`](pyproject.toml:7) und Repro-NFR in [`docs/PRD.md`](docs/PRD.md:132)
*   **Status**: Behoben (Fix 6.1)
*   **Beschreibung**: Abhängigkeiten sind ausschließlich mit unteren Schranken (`>=`) angegeben. Ohne Lockfile/Constraints kann derselbe Install-Command zu unterschiedlichen Dependency-Graphen führen (und damit zu nicht reproduzierbaren Runs/Tests). Das erhöht zudem Supply-Chain-Risiken (ungeprüfte Updates) und erschwert Debugging.
*   **Lösung**: Einführung einer `requirements.lock` (generiert via `pip freeze`) und Dokumentation des reproduzierbaren Install-Flows in der `README.md`.
