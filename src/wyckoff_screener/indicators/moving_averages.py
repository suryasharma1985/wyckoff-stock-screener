"""Moving averages module for Wyckoff screener.

Implements daily and weekly simple moving averages (SMA) as required by AGENTS.md
for trend structural filters (50, 100, 150, 200 daily SMAs and 30, 40-week SMAs).
"""

from typing import Final
import pandas as pd

DEFAULT_PRICE_COL: Final[str] = "Close"
DEFAULT_DATE_COL: Final[str] = "Date"

DEFAULT_SMA_PERIOD: Final[int] = 20
PERIOD_MA_50: Final[int] = 50
PERIOD_MA_100: Final[int] = 100
PERIOD_MA_150: Final[int] = 150
PERIOD_MA_200: Final[int] = 200
PERIOD_MA_30_WEEK: Final[int] = 30
PERIOD_MA_40_WEEK: Final[int] = 40


def simple_moving_average(
    df: pd.DataFrame,
    column: str = DEFAULT_PRICE_COL,
    period: int = DEFAULT_SMA_PERIOD,
) -> pd.Series:
    """Calculate Simple Moving Average (SMA) over a specified rolling window.

    Implements daily moving average filters as specified in AGENTS.md.

    Args:
        df: DataFrame containing price series.
        column: Column name on which to compute SMA. Defaults to 'Close'.
        period: Number of periods for rolling window. Defaults to 20.

    Returns:
        pd.Series containing the SMA values.
    """
    if column not in df.columns:
        raise KeyError(f"Column '{column}' not found in DataFrame.")
    if period <= 0:
        raise ValueError(f"Period must be a positive integer, got {period}.")

    return df[column].rolling(window=period, min_periods=period).mean()


def weekly_simple_moving_average(
    df: pd.DataFrame,
    column: str = DEFAULT_PRICE_COL,
    date_col: str = DEFAULT_DATE_COL,
    period_weeks: int = PERIOD_MA_30_WEEK,
    align_to_daily: bool = True,
) -> pd.Series:
    """Calculate weekly Simple Moving Average from daily OHLCV data.

    Resamples daily data to weekly periods (ending Friday) and computes the SMA of
    weekly close prices. When `align_to_daily=True`, the weekly SMA is mapped back
    and forward-filled onto the original daily DataFrame index.

    Implements the 30-week and 40-week institutional trend filters in AGENTS.md.

    Args:
        df: Daily OHLCV DataFrame.
        column: Price column name (default 'Close').
        date_col: Date column name (default 'Date').
        period_weeks: Number of weeks for the SMA (default 30).
        align_to_daily: If True, returns Series aligned with df.index; if False, returns weekly Series.

    Returns:
        pd.Series of weekly SMA values.
    """
    if column not in df.columns:
        raise KeyError(f"Column '{column}' not found in DataFrame.")
    if date_col not in df.columns:
        raise KeyError(f"Date column '{date_col}' not found in DataFrame.")
    if period_weeks <= 0:
        raise ValueError(f"period_weeks must be a positive integer, got {period_weeks}.")

    temp_df = df[[date_col, column]].copy()
    temp_df[date_col] = pd.to_datetime(temp_df[date_col])
    temp_df = temp_df.sort_values(by=date_col)

    # Resample daily close to weekly Friday close
    weekly_series = (
        temp_df.set_index(date_col)[column]
        .resample("W-FRI")
        .last()
        .dropna()
    )

    weekly_ma = weekly_series.rolling(window=period_weeks, min_periods=period_weeks).mean()

    if not align_to_daily:
        return weekly_ma

    # Map weekly MA back to daily dates using forward-fill merge_asof
    weekly_ma_df = weekly_ma.reset_index()
    weekly_ma_df.columns = [date_col, f"weekly_sma_{period_weeks}"]

    merged = pd.merge_asof(
        temp_df[[date_col]],
        weekly_ma_df,
        on=date_col,
        direction="backward",
    )
    # Restore original df index
    merged.index = df.index
    return merged[f"weekly_sma_{period_weeks}"]


def sma_50(df: pd.DataFrame, column: str = DEFAULT_PRICE_COL) -> pd.Series:
    """Convenience function for 50-period Simple Moving Average."""
    return simple_moving_average(df, column=column, period=PERIOD_MA_50)


def sma_100(df: pd.DataFrame, column: str = DEFAULT_PRICE_COL) -> pd.Series:
    """Convenience function for 100-period Simple Moving Average."""
    return simple_moving_average(df, column=column, period=PERIOD_MA_100)


def sma_150(df: pd.DataFrame, column: str = DEFAULT_PRICE_COL) -> pd.Series:
    """Convenience function for 150-period Simple Moving Average."""
    return simple_moving_average(df, column=column, period=PERIOD_MA_150)


def sma_200(df: pd.DataFrame, column: str = DEFAULT_PRICE_COL) -> pd.Series:
    """Convenience function for 200-period Simple Moving Average."""
    return simple_moving_average(df, column=column, period=PERIOD_MA_200)


def sma_30_week(
    df: pd.DataFrame,
    column: str = DEFAULT_PRICE_COL,
    date_col: str = DEFAULT_DATE_COL,
    align_to_daily: bool = True,
) -> pd.Series:
    """Convenience function for 30-week Simple Moving Average."""
    return weekly_simple_moving_average(
        df,
        column=column,
        date_col=date_col,
        period_weeks=PERIOD_MA_30_WEEK,
        align_to_daily=align_to_daily,
    )


def sma_40_week(
    df: pd.DataFrame,
    column: str = DEFAULT_PRICE_COL,
    date_col: str = DEFAULT_DATE_COL,
    align_to_daily: bool = True,
) -> pd.Series:
    """Convenience function for 40-week Simple Moving Average."""
    return weekly_simple_moving_average(
        df,
        column=column,
        date_col=date_col,
        period_weeks=PERIOD_MA_40_WEEK,
        align_to_daily=align_to_daily,
    )
