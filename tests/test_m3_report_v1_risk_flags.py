from __future__ import annotations

from macrolens_poc.report.v1 import SeriesRow, compute_risk_flags


def test_risk_flags_unknown_if_required_series_missing() -> None:
    flags = compute_risk_flags(rows_by_id={})
    assert flags["risk_regime"] == "unknown"


def test_risk_flags_risk_off_and_on() -> None:
    # risk_off: VIX up, SPX down
    rows = {
        "vix": SeriesRow(
            id="vix", category="risk_assets", last=20.0, deltas={"d1": None, "d5": 1.0, "d21": None}
        ),
        "sp500": SeriesRow(
            id="sp500", category="risk_assets", last=5000.0, deltas={"d1": None, "d5": -10.0, "d21": None}
        ),
    }
    flags = compute_risk_flags(rows_by_id=rows)
    assert flags["risk_regime"] == "risk_off"

    # risk_on: VIX down, SPX up
    rows = {
        "vix": SeriesRow(
            id="vix", category="risk_assets", last=20.0, deltas={"d1": None, "d5": -1.0, "d21": None}
        ),
        "sp500": SeriesRow(
            id="sp500", category="risk_assets", last=5000.0, deltas={"d1": None, "d5": 10.0, "d21": None}
        ),
    }
    flags = compute_risk_flags(rows_by_id=rows)
    assert flags["risk_regime"] == "risk_on"
