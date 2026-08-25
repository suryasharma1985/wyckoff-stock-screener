import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
import pandas as pd
import numpy as np
from wyckoff_screener.data_loader import validate_ohlcv_dataframe
from wyckoff_screener.indicators.moving_averages import simple_moving_average
from wyckoff_screener.indicators.momentum import rsi
from wyckoff_screener.indicators.volatility import atr_contraction_ratio

df = pd.read_csv("data/cache/ANANTRAJ.NS.csv")
v_df = validate_ohlcv_dataframe(df)

# Check 10 random cutoff dates
dates = v_df["Date"].sample(10, random_state=42).sort_values().tolist()

# 1. Full vectorized indicator calculation
full_sma50 = simple_moving_average(v_df, period=50)
full_sma100 = simple_moving_average(v_df, period=100)
full_rsi14 = rsi(v_df, period=14)
full_atr = atr_contraction_ratio(v_df)

for dt in dates:
    dt_str = str(dt)[:10]
    pit_df = v_df[v_df["Date"] <= dt].copy()
    
    pit_sma50 = simple_moving_average(pit_df, period=50).iloc[-1]
    pit_sma100 = simple_moving_average(pit_df, period=100).iloc[-1]
    pit_rsi14 = rsi(pit_df, period=14).iloc[-1]
    pit_atr = atr_contraction_ratio(pit_df).iloc[-1]
    
    vec_idx = v_df[v_df["Date"] <= dt].index[-1]
    vec_sma50 = full_sma50.iloc[vec_idx]
    vec_sma100 = full_sma100.iloc[vec_idx]
    vec_rsi14 = full_rsi14.iloc[vec_idx]
    vec_atr = full_atr.iloc[vec_idx]
    
    assert np.isclose(pit_sma50, vec_sma50, equal_nan=True), f"SMA50 mismatch on {dt_str}: {pit_sma50} vs {vec_sma50}"
    assert np.isclose(pit_sma100, vec_sma100, equal_nan=True), f"SMA100 mismatch on {dt_str}: {pit_sma100} vs {vec_sma100}"
    assert np.isclose(pit_rsi14, vec_rsi14, equal_nan=True), f"RSI14 mismatch on {dt_str}: {pit_rsi14} vs {vec_rsi14}"
    assert np.isclose(pit_atr, vec_atr, equal_nan=True), f"ATR mismatch on {dt_str}: {pit_atr} vs {vec_atr}"

print("ALL VECTORIZED PRECOMPUTATION EQUIVALENCE CHECKS PASSED PERFECTLY!")
