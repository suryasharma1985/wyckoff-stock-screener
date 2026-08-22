"""Unit tests for historical rolling scorer and backtest forward return analysis."""

import numpy as np
import pandas as pd
import pytest

from wyckoff_screener.backtest.forward_return_analysis import (
    compute_forward_returns,
    summarize_forward_returns,
)
from wyckoff_screener.backtest.historical_scorer import run_rolling_score


def _create_synthetic_history(num_bars: int = 150) -> pd.DataFrame:
    """Generate synthetic OHLCV history with trading range base and breakout."""
    dates = pd.date_range("2024-01-01", periods=num_bars)
    prices = [100.0] * num_bars

    # Markup after bar 80
    for idx in range(80, num_bars):
        prices[idx] = 100.0 + (idx - 80) * 1.5

    highs = [p + 2.0 for p in prices]
    lows = [p - 2.0 for p in prices]
    opens = [p - 0.5 for p in prices]
    closes = [p + 0.5 for p in prices]
    volumes = [1000.0] * num_bars

    # Spring at bar 51
    lows[51] = 94.0
    closes[51] = 102.0
    volumes[51] = 1500.0

    return pd.DataFrame({
        "Date": dates,
        "Open": opens,
        "High": highs,
        "Low": lows,
        "Close": closes,
        "Volume": volumes,
    })


def test_no_lookahead_leak_at_checkpoint():
    """Verify that future bars do NOT leak backwards into historical checkpoint scores."""
    df_full = _create_synthetic_history(num_bars=150)
    df_truncated = df_full.iloc[:100].copy()

    scores_truncated = run_rolling_score(
        df_truncated,
        symbol="TEST_ASSET",
        lookback_window=80,
        step=5,
        min_bars=60,
    )

    scores_full = run_rolling_score(
        df_full,
        symbol="TEST_ASSET",
        lookback_window=80,
        step=5,
        min_bars=60,
    )

    # Number of checkpoints in truncated must match the first N in full
    num_common_checkpoints = len(scores_truncated)
    assert num_common_checkpoints > 0

    subset_full = scores_full.iloc[:num_common_checkpoints].reset_index(drop=True)

    # Every score, event, and flag must be byte-for-byte identical
    for col in ["date", "composite_score", "is_disqualified", "most_recent_event_type", "mechanical_score", "recency_score"]:
        assert (scores_truncated[col] == subset_full[col]).all(), f"Lookahead leak detected in column: {col}"


def test_forward_return_calculation_hand_calculated():
    """Verify forward percentage returns match exact price ratio formulas."""
    dates = pd.date_range("2024-01-01", periods=50)
    # Monotonic price series: 100, 101, 102, ..., 149
    prices = [100.0 + i for i in range(50)]
    pdf = pd.DataFrame({"Date": dates, "Close": prices})

    # Fake rolling scores df with checkpoints at bar 0 and bar 10
    scores_df = pd.DataFrame([
        {"bar_index": 0, "date": dates[0], "composite_score": 75.0, "is_disqualified": False},
        {"bar_index": 10, "date": dates[10], "composite_score": 30.0, "is_disqualified": True},
    ])

    fwd_df = compute_forward_returns(scores_df, pdf, horizons=[10, 20])

    # Checkpoint at bar 0 (price=100.0):
    # 10d return = (price[10] - 100) / 100 = (110 - 100) / 100 = +10.0%
    # 20d return = (price[20] - 100) / 100 = (120 - 100) / 100 = +20.0%
    assert fwd_df.loc[0, "fwd_return_10d"] == 10.0
    assert fwd_df.loc[0, "fwd_return_20d"] == 20.0

    # Checkpoint at bar 10 (price=110.0):
    # 10d return = (price[20] - 110) / 110 = (120 - 110) / 110 = +9.09%
    # 20d return = (price[30] - 110) / 110 = (130 - 110) / 110 = +18.18%
    assert fwd_df.loc[1, "fwd_return_10d"] == 9.09
    assert fwd_df.loc[1, "fwd_return_20d"] == 18.18


def test_summarize_forward_returns_cohort_breakdown():
    """Verify performance summary calculates statistics across qualified and score tiers."""
    df_eval = pd.DataFrame({
        "composite_score": [70.0, 65.0, 35.0, 20.0],
        "is_disqualified": [False, False, True, True],
        "fwd_return_10d": [5.0, 7.0, -2.0, -4.0],
        "fwd_return_20d": [10.0, 12.0, -5.0, -1.0],
    })

    summary = summarize_forward_returns(df_eval, horizons=[10, 20], score_high_thresh=60.0, score_low_thresh=40.0)

    assert summary["total_checkpoints"] == 4
    assert summary["qualified_count"] == 2
    assert summary["disqualified_count"] == 2
    assert summary["high_score_count"] == 2
    assert summary["low_score_count"] == 2

    # 10d qualified: mean of [5.0, 7.0] = 6.0%, win rate = 100%
    assert summary["horizons"]["10d"]["qualified"]["mean_return_pct"] == 6.0
    assert summary["horizons"]["10d"]["qualified"]["win_rate_pct"] == 100.0

    # 10d disqualified: mean of [-2.0, -4.0] = -3.0%, win rate = 0%
    assert summary["horizons"]["10d"]["disqualified"]["mean_return_pct"] == -3.0
    assert summary["horizons"]["10d"]["disqualified"]["win_rate_pct"] == 0.0
