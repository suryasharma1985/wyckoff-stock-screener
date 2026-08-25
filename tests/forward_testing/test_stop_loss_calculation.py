"""Tests for Stop Loss (-5%) calculation and LOSS outcome classification."""

import pandas as pd
import pytest

from wyckoff_screener.forward_testing.models import ForwardSignal
from wyckoff_screener.forward_testing.evaluator import evaluate_forward_performance


def test_stop_loss_hit_and_loss_classification() -> None:
    """Verify stop loss detection when Low drops below entry - 5%."""
    sig = ForwardSignal(
        signal_id="TEST_STOP_SYM",
        run_id="TEST_RUN",
        signal_date="2026-08-21",
        symbol="SYM",
        company_name="Stop Test Corp",
        exchange="NSE",
        priority="HIGH_PRIORITY_CANDIDATE",
        score=70.0,
        signal_type="LPS",
        wyckoff_event="LPS",
        wyckoff_phase="Phase C Candidate",
        vsa_status="",
        p_and_f_score="",
        entry_price=200.0,  # 5% stop = 190.0
        close_price=200.0,
        broad_setup_status=True,
        mechanically_qualified=True,
        tradingview_url="",
        screening_date="2026-08-21",
        source_run_date="2026-08-21",
        notes="",
    )

    # Day 1 drops to Low 188.0 (below 190.0) without reaching 220.0 (+10%)
    df_stop = pd.DataFrame([
        {"Date": "2026-08-24", "Open": 198.0, "High": 202.0, "Low": 188.0, "Close": 189.0, "Volume": 1000},
    ])

    res = evaluate_forward_performance(sig, future_ohlc_df=df_stop)

    assert res.stop_5_reached == "YES"
    assert res.target_10_reached == "NO"
    assert res.result == "LOSS"
    assert res.status == "COMPLETED"
    assert res.exit_price == 190.0  # Stop level
