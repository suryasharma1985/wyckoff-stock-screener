"""Tests for Google Sheets trade outcome evaluation engine."""

import pandas as pd
import pytest

from wyckoff_screener.google_sheets.evaluator import evaluate_trade_outcome


def test_target_hit_before_stop() -> None:
    """Verify target hit triggers WIN exit at target price."""
    # Synthetic future bars: Day 1 flat, Day 2 rallies to hit target (115.0)
    future_df = pd.DataFrame([
        {"Date": "2024-02-01", "Open": 100.0, "High": 102.0, "Low": 98.0, "Close": 101.0, "Volume": 1000},
        {"Date": "2024-02-02", "Open": 101.0, "High": 116.0, "Low": 100.0, "Close": 115.0, "Volume": 2000},
        {"Date": "2024-02-05", "Open": 115.0, "High": 118.0, "Low": 114.0, "Close": 117.0, "Volume": 1500},
    ])

    outcome = evaluate_trade_outcome(
        symbol="TEST_STOCK",
        signal_date="2024-01-31",
        post_signal_df=future_df,
        entry_price=100.0,
        stop_price=95.0,
        target_price=115.0,
    )

    assert outcome.outcome == "WIN"
    assert outcome.target_hit is True
    assert outcome.stop_hit is False
    assert outcome.target_before_stop is True
    assert outcome.exit_date == "2024-02-02"
    assert outcome.exit_price == 115.0
    assert outcome.exit_reason == "TARGET_HIT"
    assert outcome.holding_days == 2
    # Gross: +15.0%, Net (-0.40% friction): +14.60%
    assert outcome.net_return_pct == pytest.approx(14.60, abs=0.01)
    # Risk per share = 100 - 95 = 5.0. R-multiple = (115 - 100) / 5 = +3.0 R
    assert outcome.r_multiple == pytest.approx(3.0, abs=0.01)


def test_stop_hit_before_target() -> None:
    """Verify stop hit triggers LOSS exit at stop price."""
    future_df = pd.DataFrame([
        {"Date": "2024-02-01", "Open": 100.0, "High": 101.0, "Low": 97.0, "Close": 98.0, "Volume": 1000},
        {"Date": "2024-02-02", "Open": 98.0, "High": 99.0, "Low": 94.0, "Close": 94.5, "Volume": 3000},
    ])

    outcome = evaluate_trade_outcome(
        symbol="TEST_STOCK",
        signal_date="2024-01-31",
        post_signal_df=future_df,
        entry_price=100.0,
        stop_price=95.0,
        target_price=115.0,
    )

    assert outcome.outcome == "LOSS"
    assert outcome.stop_hit is True
    assert outcome.target_hit is False
    assert outcome.stop_before_target is True
    assert outcome.exit_date == "2024-02-02"
    assert outcome.exit_price == 95.0
    assert outcome.exit_reason == "STOP_HIT"
    assert outcome.holding_days == 2
    # Gross: -5.0%, Net (-0.40% friction): -5.40%
    assert outcome.net_return_pct == pytest.approx(-5.40, abs=0.01)
    assert outcome.r_multiple == pytest.approx(-1.0, abs=0.01)


def test_same_day_ambiguity_conservative() -> None:
    """Verify same-day target & stop hit handles ambiguity conservatively by default."""
    # Day 1 candle has massive spread: High 120 (>= target 115) and Low 90 (<= stop 95)
    future_df = pd.DataFrame([
        {"Date": "2024-02-01", "Open": 100.0, "High": 120.0, "Low": 90.0, "Close": 110.0, "Volume": 5000},
    ])

    # Conservative mode (default): Stop takes precedence
    outcome_cons = evaluate_trade_outcome(
        symbol="TEST_STOCK",
        signal_date="2024-01-31",
        post_signal_df=future_df,
        entry_price=100.0,
        stop_price=95.0,
        target_price=115.0,
        ambiguity_handling="CONSERVATIVE",
    )
    assert outcome_cons.is_ambiguous_same_day is True
    assert outcome_cons.exit_price == 95.0
    assert outcome_cons.outcome == "LOSS"

    # Target First mode: Target takes precedence
    outcome_tgt = evaluate_trade_outcome(
        symbol="TEST_STOCK",
        signal_date="2024-01-31",
        post_signal_df=future_df,
        entry_price=100.0,
        stop_price=95.0,
        target_price=115.0,
        ambiguity_handling="TARGET_FIRST",
    )
    assert outcome_tgt.is_ambiguous_same_day is True
    assert outcome_tgt.exit_price == 115.0
    assert outcome_tgt.outcome == "WIN"


def test_excursion_and_forward_horizon_returns() -> None:
    """Verify MFE, MAE, and fixed horizon return calculations."""
    dates = pd.date_range("2024-02-01", periods=10, freq="B")
    future_df = pd.DataFrame({
        "Date": dates,
        "Open": [100.0] * 10,
        "High": [102.0, 105.0, 110.0, 108.0, 106.0, 107.0, 108.0, 109.0, 111.0, 112.0],
        "Low": [98.0, 96.0, 97.0, 98.0, 99.0, 98.0, 97.0, 96.0, 95.5, 96.0],
        "Close": [101.0, 104.0, 108.0, 107.0, 105.0, 106.0, 107.0, 108.0, 110.0, 111.0],
        "Volume": [1000] * 10,
    })

    outcome = evaluate_trade_outcome(
        symbol="TEST_STOCK",
        signal_date="2024-01-31",
        post_signal_df=future_df,
        entry_price=100.0,
        stop_price=90.0,    # Not hit
        target_price=120.0,  # Not hit
        max_holding_days=10,
    )

    # Highest high = 112.0 -> MFE = +12.0%
    assert outcome.mfe_pct == pytest.approx(12.0, abs=0.01)
    # Lowest low = 95.5 -> MAE = -4.5%
    assert outcome.mae_pct == pytest.approx(-4.5, abs=0.01)
    # 5D Return: Close on Day 5 is 105.0 -> Net (+5.0% - 0.40% friction) = +4.60%
    assert outcome.fwd_net_5d == pytest.approx(4.60, abs=0.01)
    # 10D Return: Close on Day 10 is 111.0 -> Net (+11.0% - 0.40% friction) = +10.60%
    assert outcome.fwd_net_10d == pytest.approx(10.60, abs=0.01)
    assert outcome.exit_reason == "TIME_HORIZON_REACHED"
    assert outcome.holding_days == 10
