"""Automated tests proving zero lookahead bias in historical signal generation."""

from datetime import datetime
import numpy as np
import pandas as pd
import pytest

from wyckoff_screener.backtest.engine import compute_forward_returns_and_risk
from wyckoff_screener.backtest.signal_generator import evaluate_point_in_time_signal


@pytest.fixture
def base_ohlcv_series() -> pd.DataFrame:
    """Generate 120 synthetic daily OHLCV bars."""
    dates = pd.date_range(start="2023-01-01", periods=120, freq="B").strftime("%Y-%m-%d").tolist()
    np.random.seed(42)
    base_price = 100.0
    records = []
    for i, d in enumerate(dates):
        daily_ret = np.random.normal(0.001, 0.015)
        base_price *= (1.0 + daily_ret)
        high = base_price * 1.015
        low = base_price * 0.985
        close = base_price
        opn = low + (high - low) * 0.5
        vol = int(np.random.uniform(500000, 1500000))
        records.append({
            "Date": d,
            "Open": round(opn, 2),
            "High": round(high, 2),
            "Low": round(low, 2),
            "Close": round(close, 2),
            "Volume": vol,
        })
    return pd.DataFrame(records)


def test_signal_at_t_does_not_access_future_data(base_ohlcv_series: pd.DataFrame) -> None:
    """Mathematical proof: Corrupting future bars does not alter the historical signal on date T."""
    df_original = base_ohlcv_series.copy()
    signal_idx = 75
    signal_date = df_original["Date"].iloc[signal_idx]

    # Baseline signal on date T
    sig_baseline = evaluate_point_in_time_signal(
        df_original, symbol="TEST_SYM", as_of_date=signal_date, min_bars=60
    )
    assert sig_baseline is not None

    # Corrupt all future data (index 76 through 119) with extreme 100x price spikes and volume spikes
    df_corrupted = df_original.copy()
    for idx in range(signal_idx + 1, len(df_corrupted)):
        df_corrupted.loc[idx, "Open"] = df_corrupted.loc[idx, "Open"] * 100.0
        df_corrupted.loc[idx, "High"] = df_corrupted.loc[idx, "High"] * 100.0
        df_corrupted.loc[idx, "Low"] = df_corrupted.loc[idx, "Low"] * 100.0
        df_corrupted.loc[idx, "Close"] = df_corrupted.loc[idx, "Close"] * 100.0
        df_corrupted.loc[idx, "Volume"] = int(df_corrupted.loc[idx, "Volume"] * 50)

    # Re-evaluate signal on date T with corrupted future data
    sig_after_corruption = evaluate_point_in_time_signal(
        df_corrupted, symbol="TEST_SYM", as_of_date=signal_date, min_bars=60
    )
    assert sig_after_corruption is not None

    # Verify bit-for-bit mathematical identity of every signal field
    for key in [
        "composite_score",
        "candidate_category",
        "is_high_priority",
        "is_qualified",
        "is_disqualified",
        "is_mechanically_qualified",
        "most_recent_event_type",
        "vsa_volume_ratio",
        "vsa_spread_ratio",
        "vsa_close_position",
        "pf_target_price",
        "pf_upside_pct",
        "signal_close",
    ]:
        assert sig_baseline[key] == sig_after_corruption[key], f"Mismatch on {key} after future corruption!"


def test_forward_returns_calculated_strictly_after_signal(base_ohlcv_series: pd.DataFrame) -> None:
    """Verify that forward returns are computed from future prices while the signal is frozen."""
    df = base_ohlcv_series.copy()
    sig_date = df["Date"].iloc[75]
    sig = evaluate_point_in_time_signal(df, symbol="TEST_SYM", as_of_date=sig_date, min_bars=60)
    assert sig is not None

    # Compute forward returns
    augmented = compute_forward_returns_and_risk(sig, df, horizons=[5, 10, 20])
    assert augmented["entry_date"] == df["Date"].iloc[76]
    assert augmented["entry_price"] == df["Open"].iloc[76]
    assert augmented["exit_price_5d"] == df["Close"].iloc[76 + 5]
    assert augmented["fwd_ret_5d"] == round(((df["Close"].iloc[76 + 5] - df["Open"].iloc[76]) / df["Open"].iloc[76]) * 100.0, 2)
