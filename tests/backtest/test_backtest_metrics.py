"""Automated tests for backtest return calculations, excursions (MFE/MAE), and drawdowns."""

import pandas as pd
import pytest

from wyckoff_screener.backtest.engine import compute_forward_returns_and_risk


def test_forward_return_mfe_mae_drawdown_calculation() -> None:
    """Verify exact formula behavior for next-day open entry, MFE, MAE, and max drawdown."""
    # Construct a controlled 10-bar price history
    dates = [f"2024-01-{i:02d}" for i in range(1, 11)]
    # Signal occurs on bar 0 (2024-01-01)
    # Entry occurs on bar 1 (2024-01-02) Open = 100.0
    prices = [
        {"Date": dates[0], "Open": 95.0, "High": 98.0, "Low": 94.0, "Close": 97.0, "Volume": 1000000},  # Signal bar
        {"Date": dates[1], "Open": 100.0, "High": 105.0, "Low": 98.0, "Close": 102.0, "Volume": 1000000}, # Entry bar (Open=100)
        {"Date": dates[2], "Open": 102.0, "High": 110.0, "Low": 99.0, "Close": 108.0, "Volume": 1000000},
        {"Date": dates[3], "Open": 108.0, "High": 120.0, "Low": 105.0, "Close": 115.0, "Volume": 1000000}, # Peak High = 120 (+20%)
        {"Date": dates[4], "Open": 115.0, "High": 116.0, "Low": 90.0, "Close": 92.0, "Volume": 1000000},   # Trough Low = 90 (-10% from entry, -25% from peak)
        {"Date": dates[5], "Open": 92.0, "High": 96.0, "Low": 88.0, "Close": 95.0, "Volume": 1000000},    # Bar 5 (+4d from entry): Close = 95 (-5%)
    ]
    df = pd.DataFrame(prices)

    mock_signal = {
        "signal_date": dates[0],
        "symbol": "MOCK",
        "composite_score": 75.0,
        "candidate_category": "HIGH_PRIORITY_CANDIDATE",
        "most_recent_event_type": "Spring",
    }

    res = compute_forward_returns_and_risk(
        mock_signal,
        df,
        horizons=[1, 2, 3, 4],
        friction_pct=0.40,
    )

    # 1. Entry validation
    assert res["entry_date"] == dates[1]
    assert res["entry_price"] == 100.0

    # 2. Return validation: Horizon 4 (bar 5 Close = 95.0)
    # Gross Return: (95 - 100) / 100 = -5.0%
    assert res["fwd_ret_4d"] == -5.0
    # Net Return: -5.0 - 0.40 = -5.40%
    assert res["fwd_net_ret_4d"] == -5.40

    # 3. Maximum Favorable Excursion: Max High = 120.0 -> (120 - 100) / 100 = +20.0%
    assert res["mfe_pct"] == 20.0

    # 4. Maximum Adverse Excursion: Min Low = 88.0 -> (88 - 100) / 100 = -12.0%
    assert res["mae_pct"] == -12.0

    # 5. Maximum Drawdown after entry: Peak high 120 to subsequent low 88 -> (88 - 120) / 120 = -26.67%
    assert res["max_drawdown_pct"] == -26.67
