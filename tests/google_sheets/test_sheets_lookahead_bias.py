"""Adversarial lookahead-bias test for Google Sheets validation architecture."""

import pandas as pd
import pytest

from wyckoff_screener.backtest.signal_generator import evaluate_point_in_time_signal
from wyckoff_screener.google_sheets.exporter import format_screener_candidates_for_signals_sheet
from wyckoff_screener.google_sheets.evaluator import evaluate_trade_outcome


def test_adversarial_future_corruption_leaves_signal_intact() -> None:
    """Mathematical proof that mutating future bars leaves Google Sheets signal attributes unchanged."""
    dates = pd.date_range("2024-01-01", periods=100, freq="B")
    clean_df = pd.DataFrame({
        "Date": dates,
        "Open": [100.0 + i * 0.5 for i in range(100)],
        "High": [102.0 + i * 0.5 for i in range(100)],
        "Low": [98.0 + i * 0.5 for i in range(100)],
        "Close": [101.0 + i * 0.5 for i in range(100)],
        "Volume": [100000 + (i % 10) * 5000 for i in range(100)],
    })

    cutoff_date = "2024-03-15"
    
    # Generate point-in-time signal on clean DataFrame
    sig_clean = evaluate_point_in_time_signal(clean_df, symbol="TEST_SYM", as_of_date=cutoff_date, min_bars=40)
    assert sig_clean is not None
    
    df_signals_clean = format_screener_candidates_for_signals_sheet(pd.DataFrame([sig_clean]))

    # Now create heavily corrupted DataFrame where bars AFTER cutoff_date have 100x price spikes
    corrupted_df = clean_df.copy()
    future_mask = corrupted_df["Date"] > pd.to_datetime(cutoff_date)
    corrupted_df.loc[future_mask, "Open"] *= 100.0
    corrupted_df.loc[future_mask, "High"] *= 100.0
    corrupted_df.loc[future_mask, "Low"] *= 100.0
    corrupted_df.loc[future_mask, "Close"] *= 100.0
    corrupted_df.loc[future_mask, "Volume"] *= 1000.0

    # Re-evaluate signal on corrupted DataFrame
    sig_corrupted = evaluate_point_in_time_signal(corrupted_df, symbol="TEST_SYM", as_of_date=cutoff_date, min_bars=40)
    assert sig_corrupted is not None
    
    df_signals_corrupted = format_screener_candidates_for_signals_sheet(pd.DataFrame([sig_corrupted]))

    # Verify that SIGNALS table fields on Date T are bit-for-bit identical
    for col in ["Symbol", "Signal_Date", "Screener_Score", "Priority", "Wyckoff_Event", "Entry_Price", "Stop_Price", "Target_1"]:
        assert df_signals_clean[col].iloc[0] == df_signals_corrupted[col].iloc[0], f"Lookahead corruption detected in {col}!"

    # Verify that future evaluation does react to the altered future data as expected
    post_clean = clean_df[clean_df["Date"] > pd.to_datetime(cutoff_date)]
    post_corrupt = corrupted_df[corrupted_df["Date"] > pd.to_datetime(cutoff_date)]

    outcome_clean = evaluate_trade_outcome("TEST_SYM", cutoff_date, post_clean, entry_price=100.0)
    outcome_corrupt = evaluate_trade_outcome("TEST_SYM", cutoff_date, post_corrupt, entry_price=100.0)

    # In clean data, MFE is normal; in corrupted data, MFE exceeds 10,000%
    assert outcome_clean.mfe_pct < 100.0
    assert outcome_corrupt.mfe_pct > 5000.0
