# Design Spec: Robust Delta Calculation (Gappy Data Handling)

## Status
- **Author**: Roo (Architect Mode)
- **Date**: 2025-12-19
- **Status**: Finalized (Proposed for Implementation)

## 1. Problemstellung
Die aktuelle Delta-Berechnung in [`src/macrolens_poc/report/v1.py`](../../src/macrolens_poc/report/v1.py:69) verwendet einen exakten Match für das Ziel-Datum (`last_day - window`). 
Da Finanzmärkte an Wochenenden und Feiertagen geschlossen sind, führen Fenster wie 1 Tag (d1) oder 5 Tage (d5) oft zu `null` Ergebnissen, wenn der Zieltag auf einen schließungsfreien Tag fällt.

## 2. Zielsetzung
Einführung einer robusten Suchlogik innerhalb eines Toleranzfensters (Default: +/- 2 Tage), um die Verfügbarkeit von Deltas in Reports zu erhöhen, während gleichzeitig Look-ahead Bias minimiert wird.

## 3. Vorgeschlagene Lösung

### 3.1 Algorithmus: `find_nearest_value`
Es wird eine dedizierte Helper-Funktion implementiert, die zwischen zwei Modi unterscheiden kann:

- **Modus `lookback_first` (Default)**: Bevorzugt Datenpunkte in der Vergangenheit, um Look-ahead Bias zu vermeiden. Sucht erst rückwärts bis zur Toleranzgrenze, dann (optional/falls konfiguriert) vorwärts.
- **Modus `nearest`**: Wählt den absolut zeitlich nächsten Datenpunkt innerhalb der Toleranz.

#### Auswahlregeln (Default: `lookback_first` mit Tie-Break)
1. **Exact Match**: Hat immer Vorrang.
2. **Suche**: Falls kein exakter Match, prüfe alle Tage `d` im Fenster `[target_day - tolerance, target_day + tolerance]`.
3. **Ranking**:
    - Wähle `d` mit minimalem `abs(d - target_day)`.
    - **Tie-Break**: Falls zwei Tage den gleichen Abstand haben (z.B. Freitag und Montag bei Zieltag Sonntag), gewinnt der **frühere** Tag (Freitag).
    - **Look-ahead Policy**: Im Modus `lookback_first` werden zukünftige Tage (`d > target_day`) nur gewählt, wenn im Lookback-Zeitraum kein einziger Punkt gefunden wurde.

### 3.2 Effizienz
Für den aktuellen PoC-Umfang reicht ein Scan der Keys von `by_day`. Für zukünftige Skalierung wird die Verwendung von `bisect` auf sortierten Datumslisten empfohlen.

## 4. Technische Umsetzung

### Signatur der Helper-Funktion
```python
def find_nearest_value(
    by_day: dict[datetime.date, float], 
    target_day: datetime.date, 
    tolerance_days: int = 2, 
    mode: str = "lookback_first"
) -> Optional[float]:
    ...
```

### Änderungen in `src/macrolens_poc/report/v1.py`
- Integration von `find_nearest_value`.
- In `_series_last_and_deltas`: Ersetze `by_day.get(target_day)` durch den Aufruf der Helper-Funktion.
- Standard-Toleranz: 2 Tage.

## 5. Test-Szenarien (Edge Cases)
Folgende Fälle müssen in [`tests/test_m3_report_v1_deltas.py`](../../tests/test_m3_report_v1_deltas.py) abgedeckt werden:

1. **Exact Match**: Target existiert -> Wert wird genommen.
2. **Wochenende (Lookback)**: `last_day`=Mo, `window`=1 -> `target`=So (fehlt). Sa fehlt. Fr existiert -> Fr wird genommen.
3. **Tie-Break**: `target`=So, Sa und Mo vorhanden -> Sa gewinnt (früher).
4. **Look-ahead**: `target`=Sa, Fr fehlt, Mo existiert -> Mo wird genommen (da innerhalb Toleranz und einziger Kandidat).
5. **Außerhalb Toleranz**: Nächster Punkt ist 4 Tage weg -> `None`.
6. **Leere Serie**: Immer `None`.

## 6. Einschränkungen
- Die Logik ist primär für **tägliche Marktdaten** optimiert. 
- Bei wöchentlichen oder monatlichen Serien (z.B. manche FRED-Daten) ist eine Toleranz von 2 Tagen oft nicht ausreichend. Dies wird als "Known Limitation" für v1 dokumentiert.