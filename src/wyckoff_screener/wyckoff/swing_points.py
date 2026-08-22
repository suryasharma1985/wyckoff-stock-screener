"""Swing point detection, prior decline, and trading range context helpers.

Provides deterministic, numeric helpers for:
1. Detecting local swing highs and swing lows using a symmetric rolling window.
2. Detecting prior declines (required for Selling Climax candidate qualification).
3. Detecting trading range support and resistance levels (required for Spring, LPS, SOS, UTAD).
"""

from typing import Final, NamedTuple
import numpy as np
import pandas as pd

DEFAULT_SWING_WINDOW: Final[int] = 3
DEFAULT_DECLINE_LOOKBACK: Final[int] = 10
DEFAULT_MIN_DECLINE_PCT: Final[float] = 0.03
DEFAULT_RANGE_LOOKBACK: Final[int] = 50

DEFAULT_HIGH_COL: Final[str] = "High"
DEFAULT_LOW_COL: Final[str] = "Low"
DEFAULT_CLOSE_COL: Final[str] = "Close"


class TradingRangeContext(NamedTuple):
    """Trading range support and resistance boundaries."""

    support: float
    resistance: float
    support_idx: int
    resistance_idx: int


# Reserved for Phase 5 peer-strength slope-of-lows comparison (Bogomazov method) — not yet wired into schematic event detection.
def is_swing_low(
    df: pd.DataFrame,
    idx: int,
    window: int = DEFAULT_SWING_WINDOW,
    low_col: str = DEFAULT_LOW_COL,
) -> bool:
    """Check if bar at `idx` is a local swing low.

    A bar is a swing low if its Low is strictly less than or equal to the Low of
    `window` bars before and `window` bars after (with strictly less than at least one side).

    Args:
        df: OHLCV DataFrame.
        idx: Index of bar to test.
        window: Number of neighboring bars on each side (default 3).
        low_col: Name of Low column.

    Returns:
        bool: True if bar is a swing low.
    """
    if idx < window or idx >= len(df) - window:
        return False

    val = df[low_col].iloc[idx]
    prev_vals = df[low_col].iloc[idx - window : idx]
    next_vals = df[low_col].iloc[idx + 1 : idx + window + 1]

    return bool(val <= prev_vals.min() and val <= next_vals.min())


# Reserved for Phase 5 peer-strength slope-of-lows comparison (Bogomazov method) — not yet wired into schematic event detection.
def is_swing_high(
    df: pd.DataFrame,
    idx: int,
    window: int = DEFAULT_SWING_WINDOW,
    high_col: str = DEFAULT_HIGH_COL,
) -> bool:
    """Check if bar at `idx` is a local swing high.

    A bar is a swing high if its High is greater than or equal to the High of
    `window` bars before and after.

    Args:
        df: OHLCV DataFrame.
        idx: Index of bar to test.
        window: Number of neighboring bars on each side (default 3).
        high_col: Name of High column.

    Returns:
        bool: True if bar is a swing high.
    """
    if idx < window or idx >= len(df) - window:
        return False

    val = df[high_col].iloc[idx]
    prev_vals = df[high_col].iloc[idx - window : idx]
    next_vals = df[high_col].iloc[idx + 1 : idx + window + 1]

    return bool(val >= prev_vals.max() and val >= next_vals.max())


def detect_prior_decline(
    df: pd.DataFrame,
    end_idx: int,
    lookback: int = DEFAULT_DECLINE_LOOKBACK,
    min_drop_pct: float = DEFAULT_MIN_DECLINE_PCT,
    close_col: str = DEFAULT_CLOSE_COL,
    high_col: str = DEFAULT_HIGH_COL,
    low_col: str = DEFAULT_LOW_COL,
) -> tuple[bool, float, str]:
    """Check whether a clear prior price decline preceded the bar at `end_idx`.

    Evaluates:
    1. Net percentage drop from the peak within `lookback` bars to the bar before `end_idx` (or bar low).
    2. Overall negative trend leading into the candidate bar.

    Args:
        df: OHLCV DataFrame.
        end_idx: Bar index where the candidate event occurs.
        lookback: Number of bars prior to examine (default 10).
        min_drop_pct: Minimum fractional decline threshold (e.g. 0.03 for 3%).
        close_col: Close column name.
        high_col: High column name.
        low_col: Low column name.

    Returns:
        tuple[bool, float, str]: (is_decline, drop_pct, evidence_note)
    """
    start_idx = max(0, end_idx - lookback)
    if end_idx <= start_idx:
        return False, 0.0, "Insufficient prior bars to establish decline."

    prior_window = df.iloc[start_idx:end_idx]
    prior_peak = prior_window[high_col].max()
    curr_low = df[low_col].iloc[end_idx]

    if prior_peak <= 0:
        return False, 0.0, "Invalid prior peak price <= 0."

    drop_pct = (prior_peak - curr_low) / prior_peak
    is_decline = bool(drop_pct >= min_drop_pct)

    note = (
        f"Prior peak={prior_peak:.2f}, bar low={curr_low:.2f}, "
        f"decline={drop_pct * 100:.1f}% over prior {end_idx - start_idx} bars "
        f"(threshold >= {min_drop_pct * 100:.1f}%)"
    )
    return is_decline, drop_pct, note


def get_prior_trading_range(
    df: pd.DataFrame,
    end_idx: int,
    lookback: int = DEFAULT_RANGE_LOOKBACK,
    high_col: str = DEFAULT_HIGH_COL,
    low_col: str = DEFAULT_LOW_COL,
) -> TradingRangeContext:
    """Identify the prior trading range support (lowest low) and resistance (highest high).

    Used as the reference support/resistance bounds for Spring, LPS, SOS, and UTAD detection.

    Args:
        df: OHLCV DataFrame.
        end_idx: Current bar index (lookback window strictly precedes this bar).
        lookback: Lookback period (default 50).
        high_col: High price column name.
        low_col: Low price column name.

    Returns:
        TradingRangeContext containing support and resistance price levels and their bar indices.
    """
    start_idx = max(0, end_idx - lookback)
    if end_idx <= start_idx:
        # Edge case with no prior bars: use current bar
        return TradingRangeContext(
            support=df[low_col].iloc[end_idx],
            resistance=df[high_col].iloc[end_idx],
            support_idx=end_idx,
            resistance_idx=end_idx,
        )

    prior_sub = df.iloc[start_idx:end_idx]
    support_val = float(prior_sub[low_col].min())
    resistance_val = float(prior_sub[high_col].max())
    support_idx = int(prior_sub[low_col].idxmin())
    resistance_idx = int(prior_sub[high_col].idxmax())

    return TradingRangeContext(
        support=support_val,
        resistance=resistance_val,
        support_idx=support_idx,
        resistance_idx=resistance_idx,
    )
