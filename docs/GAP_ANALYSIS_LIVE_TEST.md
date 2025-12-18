# Gap-Analyse: Live-Test (2025-12-15)

**Datum:** 15.12.2025
**Kontext:** Live-Test der Pipeline (`run-selected` -> `report` -> `analyze`)
**Status:** Technisch erfolgreich (Exit Code 0), inhaltlich degradiert (Datenlücken).

---

## 1. Identifizierte Lücken (Gaps)

### Gap 1: Instabilität der Datenquellen (Yahoo Finance)
*   **Beobachtung:** `yfinance` lieferte für kritische Assets (`BTC-USD`, `^GSPC`) im Live-Lauf "0 rows", obwohl die Symbole korrekt sind und in vorherigen Tests funktionierten.
*   **Ursache:** `yfinance` ist keine offizielle API, sondern ein Scraper. Anfällig für Rate-Limiting, IP-Blocks oder Änderungen im HTML-Layout von Yahoo. "0 rows" deutet oft auf stilles Scheitern hin (keine Exception, aber leeres Ergebnis).
*   **Auswirkung:** **Hoch**. Ohne S&P 500 und BTC fehlen die Kern-Indikatoren für "Risk Assets". Der Report wird unvollständig, das Risiko-Regime kann nicht bestimmt werden.

### Gap 2: Datenverfügbarkeit FRED (US CPI)
*   **Beobachtung:** FRED lieferte für `us_cpi` "0 observations".
*   **Ursache:** Möglicherweise Timeout, temporäres API-Problem oder (wahrscheinlicher) ein Problem mit dem angefragten Zeitfenster (`lookback_days`) in Kombination mit dem Veröffentlichungszyklus von CPI (monatlich, mit Verzögerung). Wenn im angefragten 30-Tage-Fenster kein neuer CPI-Punkt liegt, liefert FRED ggf. nichts zurück, wenn die Logik nicht explizit "fill forward" oder "get last available" macht.
*   **Auswirkung:** **Mittel bis Hoch**. Inflation ist ein Kern-Treiber für das Makro-Regime. Fehlt dieser Datenpunkt, ist die fundamentale Einordnung (Goldilocks vs. Reflation vs. Stagflation) unmöglich.

### Gap 3: Fehlende Ausführung kritischer Indikatoren
*   **Beobachtung:** `us_hy_spread` und `us_indpro` waren im Report `unknown`.
*   **Ursache:** Der Live-Test führte `run-selected` nur für eine Teilmenge (`btc_usd`, `sp500`, `us_cpi`) aus. Da die Datenbank (`parquet`) für die anderen Werte noch leer oder veraltet war, flossen sie nicht in den Report ein.
*   **Auswirkung:** **Mittel**. Dies ist eher ein Prozess- als ein Softwarefehler. Für einen validen "Full Report" muss sichergestellt sein, dass *alle* Matrix-Komponenten zumindest einmal initial geladen wurden.

### Gap 4: "Unknown" Regime-Handling
*   **Beobachtung:** Das System setzt `risk_regime` auf `unknown`, wenn Daten fehlen.
*   **Ursache:** Deterministische Logik im Reporting: Wenn Inputs fehlen -> Output undefiniert.
*   **Auswirkung:** **Mittel**. Das LLM muss "raten" oder den Bericht stark einschränken. Es gibt keine "Graceful Degradation" (z.B. "Regime basierend auf verfügbaren Daten" oder "Last Known Good").

---

## 2. Bewertung der Kritikalität

| Gap | Beschreibung | Kritikalität | Begründung |
|---|---|---|---|
| **1** | Yahoo Instabilität | **Kritisch** | Ohne Preisdaten ist das Tool nutzlos. `yfinance` ist für Prod-Betrieb zu wackelig. |
| **2** | FRED Lücken (CPI) | **Hoch** | Makro-Modell bricht zusammen ohne Inflation/Wachstum. |
| **3** | Fehlende Indikatoren | **Mittel** | Prozess-Thema (Initial Load fehlt), leicht behebbar. |
| **4** | Regime "Unknown" | **Mittel** | UX-Thema. Der User verliert Vertrauen, wenn das System oft "weiß nicht" sagt. |

---

## 3. Maßnahmenplan (Action Items)

### Kurzfristig (Stabilisierung)
1.  **Robustes Retry & Fallback für `yfinance`:**
    *   Implementierung von aggressiveren Retries bei "0 rows" (nicht nur bei Exceptions).
    *   Ggf. Fallback auf alternative Ticker-Symbole oder Bibliotheken (z.B. `pandas_datareader` als Backup, falls `yfinance` zickt, oder direkte Requests).
2.  **FRED "Lookback-Extension":**
    *   Wenn im angefragten Fenster (z.B. 30 Tage) keine Daten für Low-Frequency-Series (CPI, GDP) gefunden werden: Automatisch das Fenster erweitern (z.B. auf 90 Tage), um den *letzten gültigen Wert* sicher zu finden.
3.  **"Stale Data" Toleranz im Report:**
    *   Erlaube die Verwendung von "alten" Daten (z.B. bis zu 5 Tage für Daily, 40 Tage für Monthly), bevor auf "Missing" geschaltet wird. Dies muss im Report transparent markiert sein ("Data as of...").

### Mittelfristig (Architektur)
4.  **Provider-Diversifizierung:**
    *   Evaluation von stabileren (ggf. kostenpflichtigen oder offiziellen) APIs für Marktdaten (z.B. Alpha Vantage Free Tier, Tiingo, IEX Cloud).
    *   Für Krypto: Coingecko API (Free Tier ist sehr stabil) statt Yahoo.
5.  **Full-Sync Job:**
    *   Einrichten eines "Nightly Full Sync", der *alle* Series aktualisiert, nicht nur selektive. `run-selected` sollte nur für Intraday-Updates genutzt werden.

### Langfristig (Vision)
6.  **Multi-Source Strategy:**
    *   Jede Series kann mehrere Provider haben (Primary/Secondary). Wenn Primary failt, versucht das System Secondary.

---

## 4. Fazit für den User

Der Live-Test war ein **erfolgreicher "Fail-Test"**. Er hat gezeigt, dass die Pipeline technisch durchläuft (Resilienz), aber die Datenqualität der Flaschenhals ist. Für den produktiven Einsatz ist die Abhängigkeit von `yfinance` in der aktuellen Form das größte Risiko. Wir müssen die Datenbeschaffung robuster machen, bevor wir die Analyse-Logik weiter verfeinern.