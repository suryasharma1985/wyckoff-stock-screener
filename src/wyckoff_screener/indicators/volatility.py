"""Volatility indicators module for Wyckoff screener.

Implements Average True Range (ATR), Bollinger Band Width (BBW), and ATR Contraction Ratio
used for volatility contraction (VCP-style tightening) and bar spread normalization per AGENTS.md.
"""

from typing import Final
import numpy as np
import pandas as pd

DEFAULT_HIGH_COL: Final[str] = "High"
DEFAULT_LOW_COL: Final[str] = "Low"
DEFAULT_CLOSE_COL: Final[str] = "Close"

DEFAULT_ATR_PERIOD: Final[int] = 14
DEFAULT_ATR_SHORT_PERIOD: Final[int] = 14
DEFAULT_ATR_LONG_PERIOD: Final[int] = 50
DEFAULT_BB_PERIOD: Final[int] = 20
DEFAULT_BB_STD: Final[float] = 2.0


def true_range(
    df: pd.DataFrame,
    high_col: str = DEFAULT_HIGH_COL,
    low_col: str = DEFAULT_LOW_COL,
    close_col: str = DEFAULT_CLOSE_COL,
) -> pd.Series:
    """Calculate True Range (TR) for each bar.

    TR = max(High - Low, abs(High - Close_prev), abs(Low - Close_prev))
    For the first bar, TR = High - Low.

    Args:
        df: DataFrame containing High, Low, Close columns.
        high_col: High price column name (default 'High').
        low_col: Low price column name (default 'Low').
        close_col: Close price column name (default 'Close').

    Returns:
        pd.Series containing True Range values.
    """
    for col in (high_col, low_col, close_col):
        if col not in df.columns:
            raise KeyError(f"Required column '{col}' not found in DataFrame.")

    high = df[high_col]
    low = df[low_col]
    prev_close = df[close_col].shift(1)

    hl = high - low
    hc = (high - prev_close).abs()
    lc = (low - prev_close).abs()

    tr = pd.concat([hl, hc, lc], axis=1).max(axis=1)
    # First bar where prev_close is NaN uses high - low
    tr.iloc[0] = hl.iloc[0]
    return tr


def average_true_range(
    df: pd.DataFrame,
    period: int = DEFAULT_ATR_PERIOD,
    high_col: str = DEFAULT_HIGH_COL,
    low_col: str = DEFAULT_LOW_COL,
    close_col: str = DEFAULT_CLOSE_COL,
    use_wilder: bool = False,
) -> pd.Series:
    """Calculate Average True Range (ATR) over a rolling window.

    Implements ATR calculation as used in AGENTS.md for volatility measurement and
    spread ratio normalization (rolling 20-period average true range).

    Args:
        df: DataFrame containing OHLC price columns.
        period: Rolling window length (default 14).
        high_col: High column name.
        low_col: Low column name.
        close_col: Close column name.
        use_wilder: If True, uses Wilder's RMA smoothing; if False, uses rolling simple mean. Defaults to False.

    Returns:
        pd.Series containing ATR values.
    """
    if period <= 0:
        raise ValueError(f"Period must be a positive integer, got {period}.")

    tr = true_range(df, high_col=high_col, low_col=low_col, close_col=close_col)

    if use_wilder:
        # Wilder's smoothing for ATR
        tr_vals = tr.to_numpy(dtype=np.float64)
        n = len(tr_vals)
        atr_vals = np.full(n, np.nan, dtype=np.float64)
        if n < period:
            return pd.Series(atr_vals, index=df.index, name=f"ATR_{period}")

        # Initial SMA of first `period` true ranges
        atr_vals[period - 1] = np.mean(tr_vals[:period])
        for i in range(period, n):
            atr_vals[i] = (atr_vals[i - 1] * (period - 1) + tr_vals[i]) / period

        return pd.Series(atr_vals, index=df.index, name=f"ATR_{period}")

    return tr.rolling(window=period, min_periods=period).mean()


def bollinger_band_width(
    df: pd.DataFrame,
    column: str = DEFAULT_CLOSE_COL,
    period: int = DEFAULT_BB_PERIOD,
    num_std: float = DEFAULT_BB_STD,
) -> pd.Series:
    """Calculate Bollinger Band Width (BBW) as a volatility contraction proxy.

    BBW = (Upper Band - Lower Band) / Middle Band = (2 * num_std * rolling_std) / rolling_mean

    Implements the volatility contraction proxy (VCP-style tightening) referenced in AGENTS.md.

    Args:
        df: DataFrame containing price series.
        column: Column name on which to compute Bollinger Bands (default 'Close').
        period: Moving average period (default 20).
        num_std: Number of standard deviations for bands (default 2.0).

    Returns:
        pd.Series containing Bollinger Band Width.
    """
    if column not in df.columns:
        raise KeyError(f"Column '{column}' not found in DataFrame.")
    if period <= 0:
        raise ValueError(f"Period must be a positive integer, got {period}.")
    if num_std <= 0:
        raise ValueError(f"num_std must be positive, got {num_std}.")

    sma = df[column].rolling(window=period, min_periods=period).mean()
    rolling_std = df[column].rolling(window=period, min_periods=period).std(ddof=0)

    # Upper = sma + num_std * std, Lower = sma - num_std * std
    # Width = (Upper - Lower) / SMA = (2 * num_std * std) / SMA
    return (2.0 * num_std * rolling_std) / sma


def atr_contraction_ratio(
    df: pd.DataFrame,
    short_period: int = DEFAULT_ATR_SHORT_PERIOD,
    long_period: int = DEFAULT_ATR_LONG_PERIOD,
    high_col: str = DEFAULT_HIGH_COL,
    low_col: str = DEFAULT_LOW_COL,
    close_col: str = DEFAULT_CLOSE_COL,
) -> pd.Series:
    """Calculate ATR Contraction Ratio comparing recent ATR to a longer baseline.

    Ratio = ATR(short_period) / ATR(long_period)

    Flags volatility contraction (VCP-style tightening) when ratio < 1.0 (e.g. < 0.7 indicates sharp tightening).

    Args:
        df: DataFrame with OHLC columns.
        short_period: Recent ATR period (default 14).
        long_period: Baseline ATR period (default 50).
        high_col: High column name.
        low_col: Low column name.
        close_col: Close column name.

    Returns:
        pd.Series containing the contraction ratio.
    """
    if short_period <= 0 or long_period <= 0:
        raise ValueError("Periods must be positive integers.")
    if short_period >= long_period:
        raise ValueError(f"short_period ({short_period}) must be strictly less than long_period ({long_period}).")

    short_atr = average_true_range(df, period=short_period, high_col=high_col, low_col=low_col, close_col=close_col)
    long_atr = average_true_range(df, period=long_period, high_col=high_col, low_col=low_col, close_col=close_col)

    # Avoid divide-by-zero if long_atr is 0
    safe_long_atr = long_atr.replace(0, np.nan)
    return short_atr / safe_long_atr
