"""Forward Performance Evaluation Engine for Phase 18 Google Sheets System.

Implements pure, auditable forward return calculations, excursion metrics (MFE/MAE),
target testing (+10%, +20%, +30%), stop loss testing (-5%), and same-day ambiguity classification.
"""

from typing import Final, Optional
import numpy as np
import pandas as pd

from wyckoff_screener.forward_testing.models import (
    ForwardSignal,
    ForwardTradeResult,
    DEFAULT_TARGET_1_PCT,
    DEFAULT_TARGET_2_PCT,
    DEFAULT_TARGET_3_PCT,
    DEFAULT_STOP_LOSS_PCT,
)


def evaluate_forward_performance(
    signal: ForwardSignal,
    future_ohlc_df: Optional[pd.DataFrame] = None,
    target_1_pct: float = DEFAULT_TARGET_1_PCT,
    target_2_pct: float = DEFAULT_TARGET_2_PCT,
    target_3_pct: float = DEFAULT_TARGET_3_PCT,
    stop_loss_pct: float = DEFAULT_STOP_LOSS_PCT,
    max_observation_days: int = 60,
    date_col: str = "Date",
    open_col: str = "Open",
    high_col: str = "High",
    low_col: str = "Low",
    close_col: str = "Close",
) -> ForwardTradeResult:
    """Evaluate post-signal forward performance against target and stop rules.

    Args:
        signal: Immutable ForwardSignal instance.
        future_ohlc_df: DataFrame containing daily candles occurring STRICTLY AFTER signal.signal_date.
        target_1_pct: First profit target percentage (default +10.0%).
        target_2_pct: Second profit target percentage (default +20.0%).
        target_3_pct: Third profit target percentage (default +30.0%).
        stop_loss_pct: Stop loss risk percentage (default -5.0%).
        max_observation_days: Maximum trading days to evaluate (default 60).
        date_col: Column name for date.
        open_col: Column name for Open price.
        high_col: Column name for High price.
        low_col: Column name for Low price.
        close_col: Column name for Close price.

    Returns:
        ForwardTradeResult populated with deterministic forward performance metrics.
    """
    entry_p = float(signal.entry_price)
    
    if future_ohlc_df is None or future_ohlc_df.empty or entry_p <= 0:
        return ForwardTradeResult(
            signal_id=signal.signal_id,
            symbol=signal.symbol,
            signal_date=signal.signal_date,
            entry_price=entry_p,
            current_price=entry_p if entry_p > 0 else None,
            current_return_pct=0.0 if entry_p > 0 else None,
            days_since_signal=0,
            status="OPEN",
            result="OPEN",
            result_reason="AWAITING_FORWARD_OBSERVATIONS",
            target_10_reached="NO",
            target_20_reached="NO",
            target_30_reached="NO",
            stop_5_reached="NO",
        )

    bars = future_ohlc_df.copy().reset_index(drop=True)
    
    # Calculate price trigger levels
    t1_level = entry_p * (1.0 + (target_1_pct / 100.0))
    t2_level = entry_p * (1.0 + (target_2_pct / 100.0))
    t3_level = entry_p * (1.0 + (target_3_pct / 100.0))
    stop_level = entry_p * (1.0 - (stop_loss_pct / 100.0))

    eval_len = min(len(bars), max_observation_days)
    
    max_gain = 0.0
    max_drawdown = 0.0
    
    t1_hit_day: Optional[int] = None
    t2_hit_day: Optional[int] = None
    t3_hit_day: Optional[int] = None
    stop_hit_day: Optional[int] = None
    
    horizon_returns: dict[int, Optional[float]] = {5: None, 10: None, 20: None, 30: None, 60: None}
    
    for i in range(eval_len):
        day_num = i + 1
        bar = bars.iloc[i]
        b_high = float(bar[high_col])
        b_low = float(bar[low_col])
        b_close = float(bar[close_col])

        # Excursions from entry
        gain = ((b_high - entry_p) / entry_p) * 100.0
        dd = ((b_low - entry_p) / entry_p) * 100.0
        
        if gain > max_gain:
            max_gain = gain
        if dd < max_drawdown:
            max_drawdown = dd

        # Record fixed horizon returns
        if day_num in horizon_returns:
            horizon_returns[day_num] = ((b_close - entry_p) / entry_p) * 100.0

        # Check triggers
        if b_high >= t1_level and t1_hit_day is None:
            t1_hit_day = day_num
        if b_high >= t2_level and t2_hit_day is None:
            t2_hit_day = day_num
        if b_high >= t3_level and t3_hit_day is None:
            t3_hit_day = day_num
        if b_low <= stop_level and stop_hit_day is None:
            stop_hit_day = day_num

    # Latest available bar
    latest_bar = bars.iloc[-1]
    curr_price = float(latest_bar[close_col])
    curr_ret = ((curr_price - entry_p) / entry_p) * 100.0
    days_elapsed = len(bars)

    # Determine Result Classification
    # 1. Check if both Target 1 and Stop hit on the exact same earliest day
    if t1_hit_day is not None and stop_hit_day is not None:
        if t1_hit_day == stop_hit_day:
            result = "AMBIGUOUS"
            reason = f"Target 1 (+{target_1_pct}%) and Stop Loss (-{stop_loss_pct}%) touched on Day {t1_hit_day}"
            status = "COMPLETED"
            exit_date = str(bars.iloc[t1_hit_day - 1][date_col])[:10]
            exit_price = stop_level
            days_held = t1_hit_day
        elif t1_hit_day < stop_hit_day:
            result = "WIN"
            reason = f"Target 1 (+{target_1_pct}%) reached on Day {t1_hit_day} before Stop on Day {stop_hit_day}"
            status = "COMPLETED"
            exit_date = str(bars.iloc[t1_hit_day - 1][date_col])[:10]
            exit_price = t1_level
            days_held = t1_hit_day
        else:
            result = "LOSS"
            reason = f"Stop Loss (-{stop_loss_pct}%) hit on Day {stop_hit_day} before Target on Day {t1_hit_day}"
            status = "COMPLETED"
            exit_date = str(bars.iloc[stop_hit_day - 1][date_col])[:10]
            exit_price = stop_level
            days_held = stop_hit_day
    elif t1_hit_day is not None:
        result = "WIN"
        reason = f"Target 1 (+{target_1_pct}%) reached on Day {t1_hit_day}"
        status = "COMPLETED"
        exit_date = str(bars.iloc[t1_hit_day - 1][date_col])[:10]
        exit_price = t1_level
        days_held = t1_hit_day
    elif stop_hit_day is not None:
        result = "LOSS"
        reason = f"Stop Loss (-{stop_loss_pct}%) hit on Day {stop_hit_day}"
        status = "COMPLETED"
        exit_date = str(bars.iloc[stop_hit_day - 1][date_col])[:10]
        exit_price = stop_level
        days_held = stop_hit_day
    else:
        result = "OPEN"
        reason = "Neither Target 1 nor Stop Loss reached yet"
        status = "OPEN"
        exit_date = None
        exit_price = None
        days_held = days_elapsed

    return ForwardTradeResult(
        signal_id=signal.signal_id,
        symbol=signal.symbol,
        signal_date=signal.signal_date,
        entry_price=entry_p,
        current_price=curr_price,
        current_return_pct=curr_ret,
        days_since_signal=days_elapsed,
        status=status,
        ret_5d=horizon_returns.get(5),
        ret_10d=horizon_returns.get(10),
        ret_20d=horizon_returns.get(20),
        ret_30d=horizon_returns.get(30),
        ret_60d=horizon_returns.get(60),
        max_gain_pct=max_gain,
        max_drawdown_pct=max_drawdown,
        target_10_reached="YES" if t1_hit_day is not None else "NO",
        target_20_reached="YES" if t2_hit_day is not None else "NO",
        target_30_reached="YES" if t3_hit_day is not None else "NO",
        stop_5_reached="YES" if stop_hit_day is not None else "NO",
        result=result,
        result_reason=reason,
        exit_date=exit_date,
        exit_price=exit_price,
        days_held=days_held,
        notes=signal.notes,
    )
