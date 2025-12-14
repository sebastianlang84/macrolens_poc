# Design: Stale-Series Detection

## 1. Ziel
Erkennen von Zeitreihen, die technisch erfolgreich abgerufen werden ("ok"), aber seit einer definierten Zeitspanne keine neuen Datenpunkte mehr geliefert haben.

## 2. Definition "Staleness"
Eine Serie gilt als "stale", wenn:
`Run-Date (UTC) - Last-Observation-Date (UTC) > Threshold (Days)`

*   **Run-Date**: Das Datum, an dem der Job läuft (normalerweise `today`).
*   **Last-Observation-Date**: Das Datum des letzten verfügbaren Datenpunkts in der Serie (nach Merge/Store).

## 3. Konfiguration

### 3.1 Globaler Default
In `config.yaml` (bzw. `Settings`-Klasse) wird ein globaler Default definiert.
*   Key: `stale_days_default`
*   Default: `5` (Tage). Annahme: Bei Daily-Daten (Mo-Fr) sollten wir spätestens nach 5 Tagen (Wochenende + Feiertag + Puffer) neue Daten sehen.

### 3.2 Per-Series Override
In `sources_matrix.yaml` (`SeriesSpec`) kann der Default überschrieben werden.
*   Key: `stale_days` (Optional[int])
*   Beispiel: Für monatliche Daten (CPI) macht ein Threshold von `35` oder `40` Tagen Sinn.

## 4. Implementierung

### 4.1 Ort der Prüfung
Die Prüfung findet in `src/macrolens_poc/pipeline/run_series.py` am Ende der Funktion `run_series()` statt.
Dort ist `last_observation_date` bereits bekannt (aus dem geladenen/gespeicherten Parquet-File).

### 4.2 Logik
```python
# Pseudo-Code in run_series()

# ... fetch & store logic ...

# Determine effective threshold
threshold = spec.stale_days if spec.stale_days is not None else settings.stale_days_default

if status == "ok" and last_observation_date is not None:
    delta_days = (ref_date - last_observation_date).days
    if delta_days > threshold:
        status = "warn" # oder "warn_stale"
        message = f"stale: last data {delta_days} days ago (threshold: {threshold})"
```

### 4.3 Status-Handling
Wir erweitern die Semantik von `status`.
*   Bisher: `ok`, `warn`, `error`, `missing`.
*   Neu: Wir nutzen `warn` für Staleness, da es technisch kein Fehler (Exception) ist, aber Aufmerksamkeit erfordert.
*   Die Message im `SeriesRunResult` wird entsprechend gesetzt: `"stale: last data X days ago"`.

## 5. Reporting & Logging
*   **Logs**: Das Event `series_run` enthält den Status `warn` und die Message. Damit ist es im JSONL-Log sichtbar.
*   **Matrix Status**: `matrix_status.json` speichert den Status `warn` und die `last_error` Message (die wir hierfür nutzen oder ein neues Feld einführen). Da `last_error` im Code für "non-ok" Messages genutzt wird, passt das.
*   **Report V1**: Der Report zeigt den Status bereits an (indirekt über fehlende Deltas oder explizit, falls wir die Tabelle erweitern). Wir sollten sicherstellen, dass "stale" Serien auffallen.
    *   Option A: Im Report eine Sektion "Warnings" hinzufügen.
    *   Option B: In der Series-Tabelle eine Spalte "Status" oder "Info" ergänzen, wenn != ok.

## 6. Änderungen an Dateien

1.  `src/macrolens_poc/config.py`: `Settings` erweitern um `stale_days_default`.
2.  `src/macrolens_poc/sources/matrix.py`: `SeriesSpec` erweitern um `stale_days`.
3.  `src/macrolens_poc/pipeline/run_series.py`: Staleness-Check am Ende einfügen.
4.  `src/macrolens_poc/report/v1.py`: Ggf. Darstellung anpassen (optional für PoC, aber hilfreich).
