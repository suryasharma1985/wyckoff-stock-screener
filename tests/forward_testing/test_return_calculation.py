"""Tests for forward return calculations and excursion metrics."""

import pandas as pd
import pytest

from wyckoff_screener.forward_testing.models import ForwardSignal
from wyckoff_screener.forward_testing.evaluator import evaluate_forward_performance


def test_forward_return_horizons_and_excursions() -> None:
    """Verify returns at +5D, +10D, +20D, and max excursions (MFE/MAE)."""
    sig = ForwardSignal(
        signal_id="TEST_RUN_INFY",
        run_id="TEST_RUN",
        signal_date="2026-08-21",
        symbol="INFY",
        company_name="Infosys Limited",
        exchange="NSE",
        priority="HIGH_PRIORITY_CANDIDATE",
        score=75.0,
        signal_type="Spring",
        wyckoff_event="Spring",
        wyckoff_phase="Phase C Candidate",
        vsa_status="Vol: 2.1x",
        p_and_f_score="Tgt: 2000",
        entry_price=1500.0,
        close_price=1500.0,
        broad_setup_status=True,
        mechanically_qualified=True,
        tradingview_url="",
        screening_date="2026-08-21",
        source_run_date="2026-08-21",
        notes="Spring test",
    )

    # 20 trading days of price action
    # Day 5 close = 1575 (+5.0%)
    # Day 10 close = 1620 (+8.0%)
    # Day 20 close = 1650 (+10.0%)
    # Peak High = 1680 (+12.0%)
    # Lowest Low = 1440 (-4.0%)
    dates = pd.date_range("2026-08-24", periods=20, freq="B")
    future_df = pd.DataFrame({
        "Date": dates,
        "Open": [1500.0] * 20,
        "High": [1520.0, 1530.0, 1550.0, 1560.0, 1580.0, 1590.0, 1600.0, 1610.0, 1630.0, 1640.0,
                 1650.0, 1660.0, 1670.0, 1680.0, 1660.0, 1650.0, 1640.0, 1630.0, 1640.0, 1660.0],
        "Low":  [1480.0, 1470.0, 1440.0, 1490.0, 1510.0, 1530.0, 1540.0, 1550.0, 1560.0, 1580.0,
                 1590.0, 1600.0, 1610.0, 1620.0, 1610.0, 1600.0, 1590.0, 1580.0, 1590.0, 1600.0],
        "Close": [1510.0, 1525.0, 1460.0, 1550.0, 1575.0, 1585.0, 1595.0, 1605.0, 1615.0, 1620.0,
                  1630.0, 1640.0, 1650.0, 1660.0, 1645.0, 1635.0, 1625.0, 1615.0, 1630.0, 1650.0],
        "Volume": [100000] * 20,
    })

    res = evaluate_forward_performance(sig, future_ohlc_df=future_df)

    assert res.ret_5d == pytest.approx(5.0, abs=0.01)
    assert res.ret_10d == pytest.approx(8.0, abs=0.01)
    assert res.ret_20d == pytest.approx(10.0, abs=0.01)
    assert res.max_gain_pct == pytest.approx(12.0, abs=0.01)  # (1680 - 1500) / 1500 = +12.0%
    assert res.max_drawdown_pct == pytest.approx(-4.0, abs=0.01)  # (1440 - 1500) / 1500 = -4.0%
    assert res.current_price == 1650.0
    assert res.current_return_pct == pytest.approx(10.0, abs=0.01)
