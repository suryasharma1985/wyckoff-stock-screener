"""Tests for target testing (+10%, +20%, +30%)."""

import pandas as pd
import pytest

from wyckoff_screener.forward_testing.models import ForwardSignal
from wyckoff_screener.forward_testing.evaluator import evaluate_forward_performance


def test_target_testing_levels() -> None:
    """Verify progressive detection of Target 10%, 20%, and 30%."""
    sig = ForwardSignal(
        signal_id="TEST_TARGET_SYM",
        run_id="TEST_RUN",
        signal_date="2026-08-21",
        symbol="SYM",
        company_name="Target Test Corp",
        exchange="NSE",
        priority="HIGH_PRIORITY_CANDIDATE",
        score=80.0,
        signal_type="SOS",
        wyckoff_event="SOS",
        wyckoff_phase="Phase D Candidate",
        vsa_status="",
        p_and_f_score="",
        entry_price=100.0,
        close_price=100.0,
        broad_setup_status=True,
        mechanically_qualified=True,
        tradingview_url="",
        screening_date="2026-08-21",
        source_run_date="2026-08-21",
        notes="",
    )

    # Case 1: High reaches 112 (+12%) -> Target 10% YES, 20% NO, 30% NO
    df_10 = pd.DataFrame([
        {"Date": "2026-08-24", "Open": 100.0, "High": 112.0, "Low": 99.0, "Close": 111.0, "Volume": 1000},
    ])
    res_10 = evaluate_forward_performance(sig, future_ohlc_df=df_10)
    assert res_10.target_10_reached == "YES"
    assert res_10.target_20_reached == "NO"
    assert res_10.target_30_reached == "NO"
    assert res_10.result == "WIN"

    # Case 2: High reaches 125 (+25%) -> Target 10% YES, 20% YES, 30% NO
    df_20 = pd.DataFrame([
        {"Date": "2026-08-24", "Open": 100.0, "High": 125.0, "Low": 99.0, "Close": 122.0, "Volume": 1000},
    ])
    res_20 = evaluate_forward_performance(sig, future_ohlc_df=df_20)
    assert res_20.target_10_reached == "YES"
    assert res_20.target_20_reached == "YES"
    assert res_20.target_30_reached == "NO"
    assert res_20.result == "WIN"

    # Case 3: High reaches 135 (+35%) -> Target 10% YES, 20% YES, 30% YES
    df_30 = pd.DataFrame([
        {"Date": "2026-08-24", "Open": 100.0, "High": 135.0, "Low": 99.0, "Close": 133.0, "Volume": 1000},
    ])
    res_30 = evaluate_forward_performance(sig, future_ohlc_df=df_30)
    assert res_30.target_10_reached == "YES"
    assert res_30.target_20_reached == "YES"
    assert res_30.target_30_reached == "YES"
    assert res_30.result == "WIN"
