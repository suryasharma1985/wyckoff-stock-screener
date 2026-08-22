"""Volume Spread Analysis (VSA) metrics module for Wyckoff screener.

Implements the exact quantified VSA bar classification metrics from AGENTS.md:
1. volume_ratio: bar volume / rolling 20-period average volume
2. spread_ratio: bar (high - low) / rolling 20-period average true range
3. close_position: (close - low) / (high - low), with safe zero-range handling

All thresholds are defined as module-level named constants.
"""

from typing import Final
import numpy as np
import pandas as pd

from wyckoff_screener.indicators.volatility import average_true_range

# Default column names
DEFAULT_HIGH_COL: Final[str] = "High"
DEFAULT_LOW_COL: Final[str] = "Low"
DEFAULT_CLOSE_COL: Final[str] = "Close"
DEFAULT_OPEN_COL: Final[str] = "Open"
DEFAULT_VOLUME_COL: Final[str] = "Volume"

# Default rolling window period
DEFAULT_VSA_PERIOD: Final[int] = 20
DEFAULT_VOLUME_RATIO_PERIOD: Final[int] = 20
DEFAULT_SPREAD_RATIO_PERIOD: Final[int] = 20

# Volume Ratio Thresholds (AGENTS.md)
# >= 2.0: Very High / Climactic
# 1.5 - 2.0: High
# 0.75 - 1.5: Average
# 0.4 - 0.75: Low
# < 0.4: Very Low
VOL_RATIO_VERY_HIGH: Final[float] = 2.0
VOL_RATIO_HIGH: Final[float] = 1.5
VOL_RATIO_AVG: Final[float] = 0.75
VOL_RATIO_LOW: Final[float] = 0.4

# Spread Ratio Thresholds (AGENTS.md)
# >= 1.5: Wide
# 0.6 - 1.5: Average
# < 0.6: Narrow
SPREAD_RATIO_WIDE: Final[float] = 1.5
SPREAD_RATIO_AVG: Final[float] = 0.6

# Close Position Thresholds (AGENTS.md)
# > 0.7: Near High (Strong close)
# < 0.3: Near Low (Weak close)
# 0.3 - 0.7: Mid-range close
CLOSE_POS_HIGH: Final[float] = 0.7
CLOSE_POS_LOW: Final[float] = 0.3

# Pattern Specific Thresholds (AGENTS.md)
NO_DEMAND_SPREAD_MAX: Final[float] = 0.6
NO_DEMAND_VOL_MAX: Final[float] = 1.0
NO_SUPPLY_SPREAD_MAX: Final[float] = 0.6
NO_SUPPLY_VOL_MAX: Final[float] = 1.0
STOPPING_VOL_RATIO_MIN: Final[float] = 1.5
STOPPING_SPREAD_RATIO_MAX: Final[float] = 1.0


def volume_ratio(
    df: pd.DataFrame,
    period: int = DEFAULT_VOLUME_RATIO_PERIOD,
    volume_col: str = DEFAULT_VOLUME_COL,
) -> pd.Series:
    """Calculate Volume Ratio for each bar.

    volume_ratio = bar volume / rolling 20-period average volume

    Quantified categories per AGENTS.md:
        >= 2.0: Very High / Climactic
        1.5 - 2.0: High
        0.75 - 1.5: Average
        0.4 - 0.75: Low
        < 0.4: Very Low

    Args:
        df: DataFrame containing the volume series.
        period: Rolling average period (default 20).
        volume_col: Column name for volume (default 'Volume').

    Returns:
        pd.Series containing volume ratio values.
    """
    if volume_col not in df.columns:
        raise KeyError(f"Volume column '{volume_col}' not found in DataFrame.")
    if period <= 0:
        raise ValueError(f"Period must be a positive integer, got {period}.")

    rolling_avg_vol = df[volume_col].rolling(window=period, min_periods=period).mean()
    # Avoid divide-by-zero if average volume is zero
    safe_avg_vol = rolling_avg_vol.replace(0, np.nan)
    return df[volume_col] / safe_avg_vol


def spread_ratio(
    df: pd.DataFrame,
    period: int = DEFAULT_SPREAD_RATIO_PERIOD,
    high_col: str = DEFAULT_HIGH_COL,
    low_col: str = DEFAULT_LOW_COL,
    close_col: str = DEFAULT_CLOSE_COL,
) -> pd.Series:
    """Calculate Spread Ratio for each bar.

    spread_ratio = bar (high - low) / rolling 20-period average true range

    Note on ATR Method:
        A simple rolling mean (use_wilder=False) is used here rather than Wilder's
        smoothing, because spread_ratio is designed to measure immediate local bar
        spread relative to the unweighted 20-period baseline, reacting directly
        to recent volatility per the VSA definition in AGENTS.md.

    Quantified categories per AGENTS.md:
        >= 1.5: Wide
        0.6 - 1.5: Average
        < 0.6: Narrow

    Args:
        df: DataFrame containing OHLC price series.
        period: Rolling ATR period (default 20).
        high_col: High price column name (default 'High').
        low_col: Low price column name (default 'Low').
        close_col: Close price column name (default 'Close').

    Returns:
        pd.Series containing spread ratio values.
    """
    if high_col not in df.columns:
        raise KeyError(f"High column '{high_col}' not found in DataFrame.")
    if low_col not in df.columns:
        raise KeyError(f"Low column '{low_col}' not found in DataFrame.")
    if close_col not in df.columns:
        raise KeyError(f"Close column '{close_col}' not found in DataFrame.")
    if period <= 0:
        raise ValueError(f"Period must be a positive integer, got {period}.")

    bar_spread = df[high_col] - df[low_col]
    atr_series = average_true_range(
        df,
        period=period,
        high_col=high_col,
        low_col=low_col,
        close_col=close_col,
        use_wilder=False,
    )
    safe_atr = atr_series.replace(0, np.nan)
    return bar_spread / safe_atr


def close_position(
    df: pd.DataFrame,
    high_col: str = DEFAULT_HIGH_COL,
    low_col: str = DEFAULT_LOW_COL,
    close_col: str = DEFAULT_CLOSE_COL,
) -> pd.Series:
    """Calculate Close Position within the bar's High-Low range.

    close_position = (close - low) / (high - low)

    Handles zero-range bars (high == low) safely by returning 0.5 (mid-range).

    Quantified categories per AGENTS.md:
        > 0.7: Near High (Strong close)
        < 0.3: Near Low (Weak close)
        0.3 - 0.7: Mid-range close

    Args:
        df: DataFrame containing High, Low, Close series.
        high_col: High price column name (default 'High').
        low_col: Low price column name (default 'Low').
        close_col: Close price column name (default 'Close').

    Returns:
        pd.Series containing close position values in [0.0, 1.0].
    """
    for col in (high_col, low_col, close_col):
        if col not in df.columns:
            raise KeyError(f"Required column '{col}' not found in DataFrame.")

    high = df[high_col]
    low = df[low_col]
    close = df[close_col]

    bar_range = high - low
    # Where bar_range is 0, default to 0.5 (neutral mid-range) to prevent division by zero
    zero_range_mask = bar_range == 0.0
    safe_range = bar_range.where(~zero_range_mask, 1.0)

    pos = (close - low) / safe_range
    return pos.where(~zero_range_mask, 0.5)


def classify_volume_ratio(vr: float) -> str:
    """Classify volume ratio value into quantified category string."""
    if np.isnan(vr):
        return "Unknown"
    if vr >= VOL_RATIO_VERY_HIGH:
        return "Very High"
    if vr >= VOL_RATIO_HIGH:
        return "High"
    if vr >= VOL_RATIO_AVG:
        return "Average"
    if vr >= VOL_RATIO_LOW:
        return "Low"
    return "Very Low"


def classify_spread_ratio(sr: float) -> str:
    """Classify spread ratio value into quantified category string."""
    if np.isnan(sr):
        return "Unknown"
    if sr >= SPREAD_RATIO_WIDE:
        return "Wide"
    if sr >= SPREAD_RATIO_AVG:
        return "Average"
    return "Narrow"


def classify_close_position(cp: float) -> str:
    """Classify close position value into quantified category string."""
    if np.isnan(cp):
        return "Unknown"
    if cp > CLOSE_POS_HIGH:
        return "Near High"
    if cp < CLOSE_POS_LOW:
        return "Near Low"
    return "Mid-Range"
