"""Tests for handling missing or awaiting forward price data."""

import pandas as pd
import pytest

from wyckoff_screener.forward_testing.models import ForwardSignal
from wyckoff_screener.forward_testing.evaluator import evaluate_forward_performance


def test_missing_future_price_data_maintains_open_status() -> None:
    """Verify that absent future price data produces an OPEN status rather than a loss."""
    sig = ForwardSignal(
        signal_id="TEST_OPEN_SYM",
        run_id="TEST_RUN",
        signal_date="2026-08-21",
        symbol="NEWSTOCK",
        company_name="New Stock Limited",
        exchange="NSE",
        priority="QUALIFIED_CANDIDATE",
        score=65.0,
        signal_type="LPS",
        wyckoff_event="LPS",
        wyckoff_phase="Phase C Candidate",
        vsa_status="",
        p_and_f_score="",
        entry_price=50.0,
        close_price=50.0,
        broad_setup_status=True,
        mechanically_qualified=True,
        tradingview_url="",
        screening_date="2026-08-21",
        source_run_date="2026-08-21",
        notes="",
    )

    # Empty DataFrame (no future observations yet)
    res_empty = evaluate_forward_performance(sig, future_ohlc_df=pd.DataFrame())
    assert res_empty.status == "OPEN"
    assert res_empty.result == "OPEN"
    assert res_empty.target_10_reached == "NO"
    assert res_empty.stop_5_reached == "NO"
    assert res_empty.days_since_signal == 0

    # None DataFrame
    res_none = evaluate_forward_performance(sig, future_ohlc_df=None)
    assert res_none.status == "OPEN"
    assert res_none.result == "OPEN"
