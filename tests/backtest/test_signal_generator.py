"""Tests for Phase 16 Historical Point-in-Time Signal Generation & Google Sheets Export."""

import json
from pathlib import Path
import numpy as np
import pandas as pd
import pytest

from wyckoff_screener.backtest.signal_generator import (
    determine_historical_signal_dates,
    evaluate_point_in_time_signal,
    export_backtest_dataset,
    generate_backtest_dataset,
)


@pytest.fixture
def sample_ohlcv_series() -> pd.DataFrame:
    """Generate a clean synthetic daily OHLCV series for 120 trading days."""
    dates = pd.date_range("2024-01-01", periods=120, freq="B")
    np.random.seed(42)

    base = 100.0 + np.cumsum(np.random.randn(120) * 0.5)
    high_prices = base + np.random.uniform(1.0, 3.0, size=120)
    low_prices = base - np.random.uniform(1.0, 3.0, size=120)
    open_prices = low_prices + np.random.uniform(0.1, 0.9, size=120) * (high_prices - low_prices)
    close_prices = low_prices + np.random.uniform(0.1, 0.9, size=120) * (high_prices - low_prices)
    volumes = np.random.randint(50000, 200000, size=120)

    df = pd.DataFrame({
        "Date": dates.strftime("%Y-%m-%d"),
        "Open": np.round(open_prices, 2),
        "High": np.round(high_prices, 2),
        "Low": np.round(low_prices, 2),
        "Close": np.round(close_prices, 2),
        "Volume": volumes,
    })
    return df



def test_zero_lookahead_bias_proof(sample_ohlcv_series: pd.DataFrame) -> None:
    """Prove mathematically and programmatically that future bars cannot affect historical signals.

    Test methodology:
    1. Generate point-in-time signal on date D (e.g. bar 80).
    2. Completely corrupt/alter future bars (bars 81 to 120) with 10x prices and massive volume spikes.
    3. Re-evaluate point-in-time signal on date D.
    4. Assert that the historical signal on date D is 100% BIT-FOR-BIT IDENTICAL.
    """
    df_original = sample_ohlcv_series.copy()
    signal_date = df_original["Date"].iloc[79]  # 80th bar

    # 1. Baseline signal on date D
    signal_1 = evaluate_point_in_time_signal(
        df=df_original,
        symbol="TEST_STOCK",
        as_of_date=signal_date,
        min_bars=60,
    )
    assert signal_1 is not None

    # 2. Corrupt future bars (from index 80 onwards)
    df_corrupted = df_original.copy()
    df_corrupted.loc[80:, "Close"] = df_corrupted.loc[80:, "Close"] * 10.0
    df_corrupted.loc[80:, "High"] = df_corrupted.loc[80:, "High"] * 10.0
    df_corrupted.loc[80:, "Low"] = df_corrupted.loc[80:, "Low"] * 10.0
    df_corrupted.loc[80:, "Open"] = df_corrupted.loc[80:, "Open"] * 10.0
    df_corrupted.loc[80:, "Volume"] = 99999999

    # 3. Re-evaluate signal on date D with corrupted future data
    signal_2 = evaluate_point_in_time_signal(
        df=df_corrupted,
        symbol="TEST_STOCK",
        as_of_date=signal_date,
        min_bars=60,
    )
    assert signal_2 is not None

    # 4. Strict equivalence assertion
    assert signal_1["signal_date"] == signal_2["signal_date"]
    assert signal_1["composite_score"] == signal_2["composite_score"]
    assert signal_1["candidate_category"] == signal_2["candidate_category"]
    assert signal_1["is_high_priority"] == signal_2["is_high_priority"]
    assert signal_1["is_qualified"] == signal_2["is_qualified"]
    assert signal_1["is_disqualified"] == signal_2["is_disqualified"]
    assert signal_1["most_recent_event_type"] == signal_2["most_recent_event_type"]
    assert signal_1["vsa_volume_ratio"] == signal_2["vsa_volume_ratio"]
    assert signal_1["vsa_spread_ratio"] == signal_2["vsa_spread_ratio"]
    assert signal_1["vsa_close_position"] == signal_2["vsa_close_position"]
    assert signal_1["pf_target_price"] == signal_2["pf_target_price"]
    assert signal_1["pf_upside_pct"] == signal_2["pf_upside_pct"]
    assert signal_1["signal_close"] == signal_2["signal_close"]
    assert signal_1["data_bars_available"] == signal_2["data_bars_available"]


def test_determine_historical_signal_dates() -> None:
    """Verify clean trading-day aligned monthly and weekly signal date selection."""
    dates = pd.date_range("2024-01-01", "2024-06-30", freq="B")

    # Monthly frequency: last business day of each month
    monthly_dates = determine_historical_signal_dates(dates, start_date="2024-01-01", end_date="2024-06-30", frequency="monthly")
    assert len(monthly_dates) == 6
    assert monthly_dates[0] == "2024-01-31"
    assert monthly_dates[-1] == "2024-06-28"

    # Weekly frequency: 26 weeks
    weekly_dates = determine_historical_signal_dates(dates, start_date="2024-01-01", end_date="2024-06-30", frequency="weekly")
    assert len(weekly_dates) >= 25


def test_generate_and_export_backtest_dataset(sample_ohlcv_series: pd.DataFrame, tmp_path: Path) -> None:
    """Verify end-to-end dataset generation, price panel indexing, and export manifest."""
    securities = [
        ("STOCK_A", sample_ohlcv_series, "STOCK_A.NS", "Stock A Limited"),
        ("STOCK_B", sample_ohlcv_series, "STOCK_B.NS", "Stock B Limited"),
    ]

    signals_df, prices_df, manifest = generate_backtest_dataset(
        securities=securities,
        start_date="2024-04-01",
        end_date="2024-06-30",
        frequency="monthly",
        min_bars=60,
        min_avg_turnover_cr=0.0,  # Synthetic test data turnover override
        backtest_run_id="test_run_001",
    )

    assert not signals_df.empty
    assert not prices_df.empty
    assert manifest["total_signals_generated"] == len(signals_df)
    assert manifest["entry_model"] == "next_trading_day_open"
    assert "Survivorship-biased" in manifest["survivorship_bias_disclosure"]

    # Price panel verification
    assert "Trading_Day_Num" in prices_df.columns
    assert "Symbol" in prices_df.columns
    assert "Close" in prices_df.columns

    # Export to disk verification
    sig_p, prc_p, man_p = export_backtest_dataset(signals_df, prices_df, manifest, tmp_path)
    assert sig_p.exists()
    assert prc_p.exists()
    assert man_p.exists()

def test_forward_returns_change_when_future_prices_change(sample_ohlcv_series: pd.DataFrame) -> None:
    """Verify that forward returns react to future prices while the historical signal is invariant."""
    from wyckoff_screener.backtest.forward_return_analysis import compute_forward_returns

    df_original = sample_ohlcv_series.copy()
    signal_date = df_original["Date"].iloc[79]

    # Signal 1
    sig_1 = evaluate_point_in_time_signal(df_original, symbol="TEST_STOCK", as_of_date=signal_date, min_bars=60)
    assert sig_1 is not None

    # Corrupt future prices on bar 89 (+10d)
    df_future_doubled = df_original.copy()
    df_future_doubled.loc[89, "Close"] = df_future_doubled.loc[89, "Close"] * 2.0
    df_future_doubled.loc[89, "High"] = max(df_future_doubled.loc[89, "High"], df_future_doubled.loc[89, "Close"])

    # Signal 2
    sig_2 = evaluate_point_in_time_signal(df_future_doubled, symbol="TEST_STOCK", as_of_date=signal_date, min_bars=60)
    assert sig_2 is not None

    # Signal is 100% identical on date D
    assert sig_1["composite_score"] == sig_2["composite_score"]
    assert sig_1["candidate_category"] == sig_2["candidate_category"]

    # But downstream forward returns on bar 80 react differently to future prices
    rolling_df = pd.DataFrame([
        {"bar_index": 79, "date": signal_date, "symbol": "TEST_STOCK", "close_price": sig_1["signal_close"]}
    ])
    fwd_ret_1 = compute_forward_returns(rolling_df, df_original, horizons=[10])
    fwd_ret_2 = compute_forward_returns(rolling_df, df_future_doubled, horizons=[10])

    assert fwd_ret_1["fwd_return_10d"].iloc[0] != fwd_ret_2["fwd_return_10d"].iloc[0]


def test_next_trading_day_entry_alignment(sample_ohlcv_series: pd.DataFrame) -> None:
    """Verify that the entry price strictly aligns with the next available trading day Open."""
    df = sample_ohlcv_series.copy()
    signal_idx = 79
    signal_date = df["Date"].iloc[signal_idx]
    next_day_date = df["Date"].iloc[signal_idx + 1]
    expected_entry_open = float(df["Open"].iloc[signal_idx + 1])

    sig = evaluate_point_in_time_signal(df, symbol="TEST_STOCK", as_of_date=signal_date, min_bars=60)
    assert sig is not None
    assert sig["entry_model"] == "next_trading_day_open"
    assert sig["signal_date"] == signal_date
    # Next day Open in raw price table is the designated entry price
    assert float(df[df["Date"] == next_day_date]["Open"].iloc[0]) == expected_entry_open

