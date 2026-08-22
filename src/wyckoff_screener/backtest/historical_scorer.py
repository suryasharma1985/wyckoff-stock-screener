"""Point-in-time historical rolling scorer for backtest validation.

Guiding Principle (AGENTS.md):
- Strict point-in-time execution: df.iloc[:i] slices only.
- Never look ahead or use future bars when evaluating historical setup scores.
"""

from typing import Optional
import pandas as pd

from wyckoff_screener.scoring.setup_scorer import score_setup


def run_rolling_score(
    df: pd.DataFrame,
    symbol: str,
    lookback_window: Optional[int] = 250,
    step: int = 5,
    min_bars: int = 60,
    date_col: str = "Date",
    close_col: str = "Close",
    high_col: str = "High",
    low_col: str = "Low",
    volume_col: str = "Volume",
) -> pd.DataFrame:
    """Walk forward through historical OHLCV data and compute point-in-time setup scores.

    Args:
        df: Full historical OHLCV DataFrame.
        symbol: Ticker symbol.
        lookback_window: Rolling lookback window size (e.g. 250 bars ~ 1 year), or None for expanding window.
        step: Stride between rolling evaluation checkpoints (default 5 bars = weekly checkpoints).
        min_bars: Minimum historical bars required before evaluating the first checkpoint.
        date_col: Date column name.
        close_col: Close price column name.
        high_col: High price column name.
        low_col: Low price column name.
        volume_col: Volume column name.

    Returns:
        pd.DataFrame: One row per evaluation checkpoint with score breakdown and disqualification status.
    """
    if len(df) < min_bars:
        raise ValueError(f"DataFrame has {len(df)} bars, which is less than min_bars={min_bars}.")

    wdf = df.copy()
    if date_col in wdf.columns:
        wdf[date_col] = pd.to_datetime(wdf[date_col])
        wdf = wdf.sort_values(by=date_col).reset_index(drop=True)

    records: list[dict] = []
    total_bars = len(wdf)

    start_idx = max(min_bars, lookback_window) if lookback_window else min_bars

    for end_idx in range(start_idx, total_bars + 1, step):
        # Strict point-in-time slice: only data up to end_idx is visible
        if lookback_window is not None:
            slice_start = max(0, end_idx - lookback_window)
            point_in_time_slice = wdf.iloc[slice_start:end_idx].reset_index(drop=True)
        else:
            point_in_time_slice = wdf.iloc[:end_idx].reset_index(drop=True)

        checkpoint_bar_idx = end_idx - 1
        checkpoint_date = wdf[date_col].iloc[checkpoint_bar_idx] if date_col in wdf.columns else checkpoint_bar_idx
        checkpoint_close = float(wdf[close_col].iloc[checkpoint_bar_idx])

        # Score point-in-time setup (peer rankings omitted in single-asset historical rolling scan)
        scored = score_setup(
            point_in_time_slice,
            symbol=symbol,
            peer_rank=None,
            date_col=date_col,
            close_col=close_col,
            high_col=high_col,
            low_col=low_col,
            volume_col=volume_col,
        )

        records.append({
            "bar_index": checkpoint_bar_idx,
            "date": checkpoint_date,
            "symbol": symbol,
            "close_price": checkpoint_close,
            "composite_score": scored.composite_score,
            "is_disqualified": scored.is_disqualified,
            "disqualifying_flags": "; ".join(scored.disqualifying_flags) if scored.disqualifying_flags else "None",
            "most_recent_event_type": scored.most_recent_event_type,
            "most_recent_event_date": scored.most_recent_event_date,
            "mechanical_score": scored.score_breakdown["mechanical_filters"],
            "recency_score": scored.score_breakdown["schematic_recency"],
            "pf_upside_score": scored.score_breakdown["pf_target_upside"],
            "pf_price_objective": scored.pf_price_objective.price_objective if scored.pf_price_objective else None,
            "pf_stale_anchor": scored.pf_price_objective.stale_anchor if scored.pf_price_objective else None,
        })

    return pd.DataFrame(records)
