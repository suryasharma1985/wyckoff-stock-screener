"""Tests for same-day target & stop ambiguity handling."""

import pandas as pd
import pytest

from wyckoff_screener.forward_testing.models import ForwardSignal
from wyckoff_screener.forward_testing.evaluator import evaluate_forward_performance


def test_same_day_target_and_stop_touch_classifies_ambiguous() -> None:
    """Verify that touching both target and stop on the same candle is classified as AMBIGUOUS."""
    sig = ForwardSignal(
        signal_id="TEST_AMBIGUOUS_SYM",
        run_id="TEST_RUN",
        signal_date="2026-08-21",
        symbol="SYM",
        company_name="Ambiguity Test Corp",
        exchange="NSE",
        priority="HIGH_PRIORITY_CANDIDATE",
        score=75.0,
        signal_type="Spring",
        wyckoff_event="Spring",
        wyckoff_phase="Phase C Candidate",
        vsa_status="",
        p_and_f_score="",
        entry_price=100.0,  # Target 1 = 110.0, Stop = 95.0
        close_price=100.0,
        broad_setup_status=True,
        mechanically_qualified=True,
        tradingview_url="",
        screening_date="2026-08-21",
        source_run_date="2026-08-21",
        notes="",
    )

    # Wide-range volatility bar: High 115 (>= 110) and Low 92 (<= 95) on the same day
    df_ambig = pd.DataFrame([
        {"Date": "2026-08-24", "Open": 100.0, "High": 115.0, "Low": 92.0, "Close": 105.0, "Volume": 5000},
    ])

    res = evaluate_forward_performance(sig, future_ohlc_df=df_ambig)

    assert res.target_10_reached == "YES"
    assert res.stop_5_reached == "YES"
    assert res.result == "AMBIGUOUS"
    assert res.status == "COMPLETED"
    assert "touched on Day 1" in res.result_reason
