"""Momentum indicators module for Wyckoff screener.

Implements Relative Strength Index (RSI) using Wilder's smoothing method (14-period standard).
Used for momentum filters (such as the 55-70 bullish momentum zone) per AGENTS.md.
"""

from typing import Final
import numpy as np
import pandas as pd

DEFAULT_RSI_PERIOD: Final[int] = 14
DEFAULT_RSI_COLUMN: Final[str] = "Close"
RSI_BULLISH_BAND_LOWER: Final[float] = 55.0
RSI_BULLISH_BAND_UPPER: Final[float] = 70.0


def rsi(
    df: pd.DataFrame,
    column: str = DEFAULT_RSI_COLUMN,
    period: int = DEFAULT_RSI_PERIOD,
) -> pd.Series:
    """Calculate Relative Strength Index (RSI) using classic Wilder's smoothing.

    Calculation matches the standard 14-period RSI by J. Welles Wilder (Wilder's RMA smoothing),
    as referenced in AGENTS.md momentum filters (e.g. 55-70 accumulation/markup band).

    Formula:
        delta = price[t] - price[t-1]
        gain = delta if delta > 0 else 0
        loss = -delta if delta < 0 else 0
        avg_gain[t] = (avg_gain[t-1] * (period - 1) + gain[t]) / period
        avg_loss[t] = (avg_loss[t-1] * (period - 1) + loss[t]) / period
        RS = avg_gain / avg_loss
        RSI = 100 - (100 / (1 + RS))

    Args:
        df: DataFrame containing price series.
        column: Column name on which to compute RSI. Defaults to 'Close'.
        period: Number of periods for RSI. Defaults to 14.

    Returns:
        pd.Series containing RSI values (0-100 scale, with NaN for initial periods < period).
    """
    if column not in df.columns:
        raise KeyError(f"Column '{column}' not found in DataFrame.")
    if period <= 0:
        raise ValueError(f"Period must be a positive integer, got {period}.")

    prices = df[column].to_numpy(dtype=np.float64)
    n = len(prices)

    rsi_values = np.full(n, np.nan, dtype=np.float64)
    if n <= period:
        return pd.Series(rsi_values, index=df.index, name=f"RSI_{period}")

    deltas = np.diff(prices)
    gains = np.where(deltas > 0, deltas, 0.0)
    losses = np.where(deltas < 0, -deltas, 0.0)

    # Initial average gain and loss using simple average of the first `period` changes
    avg_gain = np.mean(gains[:period])
    avg_loss = np.mean(losses[:period])

    # First RSI value is at index `period` (corresponding to price index `period`)
    if avg_loss == 0.0:
        rsi_values[period] = 100.0 if avg_gain > 0.0 else 50.0
    else:
        rs = avg_gain / avg_loss
        rsi_values[period] = 100.0 - (100.0 / (1.0 + rs))

    # Wilder's smoothing for subsequent periods
    for i in range(period, len(deltas)):
        curr_gain = gains[i]
        curr_loss = losses[i]
        avg_gain = (avg_gain * (period - 1) + curr_gain) / period
        avg_loss = (avg_loss * (period - 1) + curr_loss) / period

        idx = i + 1  # prices index
        if avg_loss == 0.0:
            rsi_values[idx] = 100.0 if avg_gain > 0.0 else 50.0
        elif avg_gain == 0.0:
            rsi_values[idx] = 0.0
        else:
            rs = avg_gain / avg_loss
            rsi_values[idx] = 100.0 - (100.0 / (1.0 + rs))

    return pd.Series(rsi_values, index=df.index, name=f"RSI_{period}")
