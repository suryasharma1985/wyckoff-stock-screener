"""Comparative peer-strength analysis module (Bogomazov-style).

Implements:
1. Multi-series price normalization to a common structural reference date.
2. Low-to-Low slope comparison between structural swing lows using is_swing_low().
3. Ranked comparative relative strength across primary stock and peer watchlist.
"""

from dataclasses import dataclass
from typing import Any, Final, Optional
import numpy as np
import pandas as pd

from wyckoff_screener.wyckoff.swing_points import is_swing_low

DEFAULT_DATE_COL: Final[str] = "Date"
DEFAULT_PRICE_COL: Final[str] = "Close"
DEFAULT_LOW_COL: Final[str] = "Low"


@dataclass(frozen=True)
class PeerSlopeResult:
    """Relative strength metrics and slope calculation for a stock."""

    symbol: str
    first_low_date: Any
    first_low_price: float
    second_low_date: Any
    second_low_price: float
    price_change_pct: float
    num_bars: int
    slope_per_bar: float
    is_higher_low: bool
    relative_strength_rank: int
    supporting_note: str
    is_first_swing_low: bool = True
    is_second_swing_low: bool = True
    swing_validated: bool = True

    def to_dict(self) -> dict[str, Any]:
        """Convert result to dictionary."""
        return {
            "symbol": self.symbol,
            "rank": self.relative_strength_rank,
            "first_low_price": self.first_low_price,
            "second_low_price": self.second_low_price,
            "price_change_pct": round(self.price_change_pct, 2),
            "num_bars": self.num_bars,
            "slope_per_bar": round(self.slope_per_bar, 4),
            "is_higher_low": self.is_higher_low,
            "is_first_swing_low": self.is_first_swing_low,
            "is_second_swing_low": self.is_second_swing_low,
            "swing_validated": self.swing_validated,
            "supporting_note": self.supporting_note,
        }


def synchronize_to_reference_date(
    primary_df: pd.DataFrame,
    peer_df: pd.DataFrame,
    reference_date: Any,
    date_col: str = DEFAULT_DATE_COL,
    price_col: str = DEFAULT_PRICE_COL,
    primary_label: str = "primary",
    peer_label: str = "peer",
) -> pd.DataFrame:
    """Align primary and peer series to percentage change from a common reference date.

    Formula:
        pct_change(t) = ((Price(t) - Price(ref_date)) / Price(ref_date)) * 100%

    Args:
        primary_df: Primary stock OHLCV DataFrame.
        peer_df: Peer stock OHLCV DataFrame.
        reference_date: Common structural reference date (e.g. market bottom / SC date).
        date_col: Date column name.
        price_col: Price column name (default 'Close').
        primary_label: Label for primary stock column.
        peer_label: Label for peer stock column.

    Returns:
        pd.DataFrame containing Date, primary_pct, and peer_pct columns.
    """
    ref_ts = pd.to_datetime(reference_date)

    p_df = primary_df[[date_col, price_col]].copy()
    p_df[date_col] = pd.to_datetime(p_df[date_col])
    p_df = p_df.sort_values(by=date_col)

    q_df = peer_df[[date_col, price_col]].copy()
    q_df[date_col] = pd.to_datetime(q_df[date_col])
    q_df = q_df.sort_values(by=date_col)

    # Find reference price (exact date or closest preceding date)
    p_ref_row = p_df[p_df[date_col] <= ref_ts]
    q_ref_row = q_df[q_df[date_col] <= ref_ts]

    if p_ref_row.empty or q_ref_row.empty:
        raise ValueError(f"Reference date {reference_date} is before the start of one or both datasets.")

    p_ref_price = float(p_ref_row.iloc[-1][price_col])
    q_ref_price = float(q_ref_row.iloc[-1][price_col])

    if p_ref_price <= 0 or q_ref_price <= 0:
        raise ValueError("Reference price must be strictly positive.")

    p_df[f"{primary_label}_pct"] = ((p_df[price_col] - p_ref_price) / p_ref_price) * 100.0
    q_df[f"{peer_label}_pct"] = ((q_df[price_col] - q_ref_price) / q_ref_price) * 100.0

    merged = pd.merge(
        p_df[[date_col, f"{primary_label}_pct"]],
        q_df[[date_col, f"{peer_label}_pct"]],
        on=date_col,
        how="inner",
    ).sort_values(by=date_col).reset_index(drop=True)

    return merged


def compare_low_to_low_slope(
    df: pd.DataFrame,
    first_low_date: Any,
    second_low_date: Any,
    symbol: str = "TARGET",
    date_col: str = DEFAULT_DATE_COL,
    price_col: str = DEFAULT_PRICE_COL,
    low_col: str = DEFAULT_LOW_COL,
    validate_swing: bool = True,
    swing_window: int = 3,
) -> PeerSlopeResult:
    """Calculate the low-to-low slope between two structural lows per Bogomazov's method.

    Evaluates:
        slope = (Price(second_low) - Price(first_low)) / num_bars
        A steeper/positive slope indicates higher low / relative strength.
        A flatter/negative slope indicates lower low / relative weakness.

    Args:
        df: Stock OHLCV DataFrame.
        first_low_date: Date of first structural low.
        second_low_date: Date of second structural low.
        symbol: Ticker symbol.
        date_col: Date column name.
        price_col: Price column name.
        low_col: Low column name.
        validate_swing: If True, requires both dates to be validated swing lows; raises ValueError if not.
        swing_window: Swing detection window (default 3).

    Returns:
        PeerSlopeResult: Detailed slope metrics and strength classification.

    Raises:
        ValueError: If first_low_date >= second_low_date or if validate_swing=True and dates fail swing check.
        KeyError: If either date is not found in the DataFrame.
    """
    wdf = df.copy()
    wdf[date_col] = pd.to_datetime(wdf[date_col])
    wdf = wdf.sort_values(by=date_col).reset_index(drop=True)

    first_ts = pd.to_datetime(first_low_date)
    second_ts = pd.to_datetime(second_low_date)

    if first_ts >= second_ts:
        raise ValueError(f"first_low_date ({first_low_date}) must strictly precede second_low_date ({second_low_date}).")

    first_match = wdf[wdf[date_col] == first_ts]
    second_match = wdf[wdf[date_col] == second_ts]

    if first_match.empty:
        raise KeyError(f"first_low_date {first_low_date} not found in DataFrame for {symbol}.")
    if second_match.empty:
        raise KeyError(f"second_low_date {second_low_date} not found in DataFrame for {symbol}.")

    idx1 = int(first_match.index[0])
    idx2 = int(second_match.index[0])

    is_first_swing = is_swing_low(wdf, idx1, window=swing_window, low_col=low_col)
    is_second_swing = is_swing_low(wdf, idx2, window=swing_window, low_col=low_col)
    swing_validated = bool(is_first_swing and is_second_swing)

    if validate_swing and not swing_validated:
        raise ValueError(
            f"Swing low validation failed for {symbol}: first_low_date ({first_ts.strftime('%Y-%m-%d')}) "
            f"is_swing_low={is_first_swing}, second_low_date ({second_ts.strftime('%Y-%m-%d')}) "
            f"is_swing_low={is_second_swing} at window={swing_window}."
        )

    price1 = float(wdf[low_col].iloc[idx1])
    price2 = float(wdf[low_col].iloc[idx2])

    num_bars = idx2 - idx1
    price_change_pct = ((price2 - price1) / price1) * 100.0
    slope_per_bar = (price2 - price1) / num_bars
    is_higher_low = price2 > price1

    status_str = "Higher Low (Relative Strength)" if is_higher_low else "Lower Low (Relative Weakness)"
    warning_str = "" if swing_validated else " (WARNING: unvalidated swing lows)"
    note = (
        f"{symbol}: low1={price1:.2f} ({first_ts.strftime('%Y-%m-%d')}) -> "
        f"low2={price2:.2f} ({second_ts.strftime('%Y-%m-%d')}), "
        f"change={price_change_pct:+.2f}%, slope={slope_per_bar:+.4f}/bar over {num_bars} bars. "
        f"Structure: {status_str}{warning_str}."
    )

    return PeerSlopeResult(
        symbol=symbol,
        first_low_date=first_low_date,
        first_low_price=price1,
        second_low_date=second_low_date,
        second_low_price=price2,
        price_change_pct=price_change_pct,
        num_bars=num_bars,
        slope_per_bar=slope_per_bar,
        is_higher_low=is_higher_low,
        relative_strength_rank=1,
        supporting_note=note,
        is_first_swing_low=is_first_swing,
        is_second_swing_low=is_second_swing,
        swing_validated=swing_validated,
    )


def rank_peer_relative_strength(
    primary_symbol: str,
    primary_df: pd.DataFrame,
    peer_dict: dict[str, pd.DataFrame],
    first_low_date: Any,
    second_low_date: Any,
    date_col: str = DEFAULT_DATE_COL,
    price_col: str = DEFAULT_PRICE_COL,
    low_col: str = DEFAULT_LOW_COL,
    validate_swing: bool = True,
    swing_window: int = 3,
) -> tuple[list[PeerSlopeResult], list[tuple[str, str]]]:
    """Rank primary stock and peer watchlist by low-to-low percentage slope.

    Sorts candidates from steepest positive slope (Strongest) to lowest/negative slope (Weakest).

    Args:
        primary_symbol: Primary stock symbol.
        primary_df: Primary stock DataFrame.
        peer_dict: Dictionary of {peer_symbol: peer_df}.
        first_low_date: Structural low #1 date.
        second_low_date: Structural low #2 date.
        date_col: Date column name.
        price_col: Price column name.
        low_col: Low column name.
        validate_swing: Whether to strictly validate swing lows (default True).
        swing_window: Window for swing check (default 3).

    Returns:
        tuple[list[PeerSlopeResult], list[tuple[str, str]]]:
            (ranked_results from strongest to weakest, list of (symbol, error_message) for skipped peers).
    """
    all_stocks = {primary_symbol: primary_df, **peer_dict}
    results: list[PeerSlopeResult] = []
    failed_peers: list[tuple[str, str]] = []

    for sym, df_item in all_stocks.items():
        try:
            res = compare_low_to_low_slope(
                df_item,
                first_low_date=first_low_date,
                second_low_date=second_low_date,
                symbol=sym,
                date_col=date_col,
                price_col=price_col,
                low_col=low_col,
                validate_swing=validate_swing,
                swing_window=swing_window,
            )
            results.append(res)
        except Exception as exc:
            failed_peers.append((sym, str(exc)))

    # Sort descending by price_change_pct (or slope_per_bar)
    sorted_results = sorted(results, key=lambda x: x.price_change_pct, reverse=True)

    # Assign 1-indexed ranks
    ranked_results: list[PeerSlopeResult] = []
    for rank_idx, r in enumerate(sorted_results, start=1):
        ranked_results.append(
            PeerSlopeResult(
                symbol=r.symbol,
                first_low_date=r.first_low_date,
                first_low_price=r.first_low_price,
                second_low_date=r.second_low_date,
                second_low_price=r.second_low_price,
                price_change_pct=r.price_change_pct,
                num_bars=r.num_bars,
                slope_per_bar=r.slope_per_bar,
                is_higher_low=r.is_higher_low,
                relative_strength_rank=rank_idx,
                supporting_note=f"Rank #{rank_idx}: {r.supporting_note}",
                is_first_swing_low=r.is_first_swing_low,
                is_second_swing_low=r.is_second_swing_low,
                swing_validated=r.swing_validated,
            )
        )

    return ranked_results, failed_peers
