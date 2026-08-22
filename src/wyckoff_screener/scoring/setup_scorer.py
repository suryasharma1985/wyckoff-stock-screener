"""Wyckoff setup scoring and watchlist ranking engine.

Guiding Principle (AGENTS.md):
- Evidence-first: composite scores are ranking aids, never buy signals.
- Every composite score must be presented alongside its full numeric breakdown.
- Disqualifying flags identify structural red flags regardless of numerical score.
"""

from dataclasses import dataclass, field
from typing import Any, Final, Optional
import pandas as pd

from wyckoff_screener.indicators.momentum import (
    RSI_BULLISH_BAND_LOWER,
    RSI_BULLISH_BAND_UPPER,
    rsi,
)
from wyckoff_screener.indicators.moving_averages import (
    PERIOD_MA_50,
    PERIOD_MA_100,
    simple_moving_average,
    weekly_simple_moving_average,
)
from wyckoff_screener.indicators.volatility import atr_contraction_ratio
from wyckoff_screener.pointfigure.pf_chart import (
    PFPriceObjective,
    build_point_and_figure_chart,
    count_price_objective,
)
from wyckoff_screener.wyckoff.events import WyckoffEvent
from wyckoff_screener.wyckoff.schematic_events import detect_all_schematic_events

# Module-Level Weighted Scoring Constants (Sum to 100.0)
WEIGHT_MECHANICAL_FILTERS: Final[float] = 30.0  # 4 sub-filters: 7.5 pts each
WEIGHT_RECENT_EVENT: Final[float] = 40.0        # Bullish schematic recency (LPS/SOS/Spring)
WEIGHT_PEER_RANK: Final[float] = 20.0           # Comparative Bogomazov relative strength
WEIGHT_PF_UPSIDE: Final[float] = 10.0           # Point & Figure horizontal price target upside

# Maximum bars an anchor event can be in the past before its P&F objective is flagged stale
PF_ANCHOR_MAX_STALENESS_BARS: Final[int] = 60

# Mechanical filter sub-weights (4 * 7.5 = 30.0)
POINTS_PER_MECHANICAL_FILTER: Final[float] = WEIGHT_MECHANICAL_FILTERS / 4.0


@dataclass(frozen=True)
class ScoredSetup:
    """Represents a scored Wyckoff setup with full metric breakdown and red flags."""

    symbol: str
    as_of_date: Any
    mechanical_filters_passed: dict[str, bool]
    detected_events: dict[str, list[WyckoffEvent]]
    most_recent_event_type: Optional[str]
    most_recent_event_date: Any
    pf_price_objective: Optional[PFPriceObjective]
    peer_rank: Optional[int]
    composite_score: float
    score_breakdown: dict[str, float]
    disqualifying_flags: list[str] = field(default_factory=list)
    peer_analysis_skipped: bool = False

    @property
    def is_disqualified(self) -> bool:
        """True if setup has any red flags/disqualifying conditions."""
        return len(self.disqualifying_flags) > 0

    def to_dict(self) -> dict[str, Any]:
        """Convert setup to dictionary."""
        return {
            "symbol": self.symbol,
            "as_of_date": str(self.as_of_date),
            "composite_score": round(self.composite_score, 1),
            "is_disqualified": self.is_disqualified,
            "disqualifying_flags": self.disqualifying_flags,
            "most_recent_event": self.most_recent_event_type,
            "most_recent_event_date": str(self.most_recent_event_date) if self.most_recent_event_date else None,
            "peer_rank": self.peer_rank,
            "peer_analysis_skipped": self.peer_analysis_skipped,
            "mechanical_filters_passed": self.mechanical_filters_passed,
            "score_breakdown": {k: round(v, 1) for k, v in self.score_breakdown.items()},
            "pf_price_objective": self.pf_price_objective.to_dict() if self.pf_price_objective else None,
        }


def score_setup(
    df: pd.DataFrame,
    symbol: str,
    peer_rank: Optional[int] = None,
    total_peers: Optional[int] = None,
    count_row_price: Optional[float] = None,
    date_col: str = "Date",
    close_col: str = "Close",
    high_col: str = "High",
    low_col: str = "Low",
    volume_col: str = "Volume",
) -> ScoredSetup:
    """Score a single stock setup across technical filters, schematic events, P&F target, and peer rank.

    Args:
        df: Clean OHLCV DataFrame.
        symbol: Ticker symbol.
        peer_rank: 1-indexed relative strength rank (1 = strongest). If None, peer scoring is skipped (scores 0.0).
        total_peers: Total number of peers ranked.
        count_row_price: Optional custom count row price for P&F. If None, uses the most recent LPS/Spring level or current close.
        date_col: Date column name.
        close_col: Close column name.
        high_col: High column name.
        low_col: Low column name.
        volume_col: Volume column name.

    Returns:
        ScoredSetup: Complete scored setup with score breakdown, disqualification flags, and peer analysis status.
    """
    if df.empty:
        raise ValueError(f"Cannot score setup on empty DataFrame for {symbol}.")

    wdf = df.copy()
    if date_col in wdf.columns:
        wdf[date_col] = pd.to_datetime(wdf[date_col])
        wdf = wdf.sort_values(by=date_col).reset_index(drop=True)

    as_of_date = wdf[date_col].iloc[-1] if date_col in wdf.columns else len(wdf) - 1
    current_close = float(wdf[close_col].iloc[-1])

    # -------------------------------------------------------------
    # 1. Phase 3: Mechanical Filters (30 pts max)
    # -------------------------------------------------------------
    filters_passed: dict[str, bool] = {}

    # 1.1 Weekly Uptrend (30-week > 40-week MA)
    try:
        if date_col in wdf.columns and len(wdf) >= 40 * 5:  # Approx 40 weeks of daily bars
            w_ma30 = weekly_simple_moving_average(wdf, column=close_col, period_weeks=30, date_col=date_col)
            w_ma40 = weekly_simple_moving_average(wdf, column=close_col, period_weeks=40, date_col=date_col)
            valid_w = w_ma30.dropna()
            valid_w40 = w_ma40.dropna()
            if not valid_w.empty and not valid_w40.empty:
                filters_passed["weekly_uptrend"] = bool(valid_w.iloc[-1] >= valid_w40.iloc[-1])
            else:
                filters_passed["weekly_uptrend"] = False
        else:
            # Fallback for shorter series: check if Close > 50-bar SMA
            sma50 = simple_moving_average(wdf, column=close_col, period=min(50, len(wdf)))
            filters_passed["weekly_uptrend"] = bool(current_close >= sma50.iloc[-1])
    except Exception:
        filters_passed["weekly_uptrend"] = False

    # 1.2 50 DMA > 100 DMA
    try:
        sma50 = simple_moving_average(wdf, column=close_col, period=min(PERIOD_MA_50, len(wdf)))
        sma100 = simple_moving_average(wdf, column=close_col, period=min(PERIOD_MA_100, len(wdf)))
        filters_passed["dma_50_above_100"] = bool(sma50.iloc[-1] >= sma100.iloc[-1])
    except Exception:
        filters_passed["dma_50_above_100"] = False

    # 1.3 RSI in 55-70 Momentum Band
    try:
        rsi_series = rsi(wdf, column=close_col, period=14)
        latest_rsi = float(rsi_series.iloc[-1])
        filters_passed["rsi_in_band"] = bool(RSI_BULLISH_BAND_LOWER <= latest_rsi <= RSI_BULLISH_BAND_UPPER)
    except Exception:
        filters_passed["rsi_in_band"] = False

    # 1.4 ATR Contraction (ATR_14 < ATR_50)
    try:
        atr_ratio_series = atr_contraction_ratio(wdf, short_period=14, long_period=min(50, len(wdf)))
        filters_passed["atr_contracting"] = bool(atr_ratio_series.iloc[-1] < 1.0)
    except Exception:
        filters_passed["atr_contracting"] = False

    mechanical_pts = sum(POINTS_PER_MECHANICAL_FILTER for passed in filters_passed.values() if passed)

    # -------------------------------------------------------------
    # 2. Phase 4: Schematic Events & Recency (40 pts max)
    # -------------------------------------------------------------
    detected_events = detect_all_schematic_events(
        wdf,
        date_col=date_col,
        open_col="Open",
        high_col=high_col,
        low_col=low_col,
        close_col=close_col,
        volume_col=volume_col,
    )

    # Flatten all events into chronological list
    all_events_flat: list[WyckoffEvent] = []
    for ev_list in detected_events.values():
        all_events_flat.extend(ev_list)

    all_events_sorted = sorted(all_events_flat, key=lambda ev: pd.to_datetime(ev.date))

    most_recent_event_type: Optional[str] = None
    most_recent_event_date: Any = None
    event_pts = 0.0

    if all_events_sorted:
        last_ev = all_events_sorted[-1]
        most_recent_event_type = last_ev.event_type
        most_recent_event_date = last_ev.date

        # Calculate bars since last event
        date_to_idx = {wdf[date_col].iloc[k]: k for k in range(len(wdf))} if date_col in wdf.columns else {}
        last_ev_idx = date_to_idx.get(last_ev.date, len(wdf) - 1)
        bars_ago = (len(wdf) - 1) - last_ev_idx

        # Bullish accumulation events score higher when fresh
        if most_recent_event_type in ("LPS", "SOS"):
            if bars_ago <= 10:
                event_pts = WEIGHT_RECENT_EVENT  # Full 40 pts
            elif bars_ago <= 25:
                event_pts = 28.0
            else:
                event_pts = 15.0
        elif most_recent_event_type == "Spring":
            if bars_ago <= 15:
                event_pts = 35.0
            elif bars_ago <= 30:
                event_pts = 22.0
            else:
                event_pts = 12.0
        elif most_recent_event_type in ("SC", "AR", "ST"):
            if bars_ago <= 20:
                event_pts = 18.0
            else:
                event_pts = 8.0
        elif most_recent_event_type == "UTAD":
            event_pts = 0.0  # Bearish event gets 0 pts

    # -------------------------------------------------------------
    # 3. Phase 5: Peer Relative Strength Rank (20 pts max)
    # -------------------------------------------------------------
    peer_pts = 0.0
    peer_analysis_skipped = True
    if peer_rank is not None and peer_rank > 0:
        peer_analysis_skipped = False
        tot = total_peers if total_peers and total_peers > 1 else max(peer_rank, 3)
        # Scaled smoothly: Rank 1 gets full 20 pts; lower ranks decay linearly
        peer_score_fraction = max(0.0, 1.0 - ((peer_rank - 1) / tot))
        peer_pts = WEIGHT_PEER_RANK * peer_score_fraction
    else:
        # Per AGENTS.md 'No Fabricated Confidence': missing peer analysis scores 0.0 points
        peer_pts = 0.0
        peer_analysis_skipped = True

    # -------------------------------------------------------------
    # 4. Phase 5: Point & Figure Price Objective (10 pts max)
    # -------------------------------------------------------------
    pf_obj: Optional[PFPriceObjective] = None
    pf_pts = 0.0
    try:
        columns, box_size = build_point_and_figure_chart(wdf, box_pct=0.01, reversal=3, high_col=high_col, low_col=low_col, close_col=close_col, date_col=date_col)
        if columns:
            stale_anchor = False
            stale_warning = ""

            if count_row_price is not None:
                target_row = count_row_price
            elif detected_events.get("LPS") or detected_events.get("Spring"):
                anchor_ev = detected_events["LPS"][-1] if detected_events.get("LPS") else detected_events["Spring"][-1]
                target_row = anchor_ev.price
                date_to_idx = {wdf[date_col].iloc[k]: k for k in range(len(wdf))} if date_col in wdf.columns else {}
                anchor_idx = date_to_idx.get(anchor_ev.date, len(wdf) - 1)
                anchor_bars_ago = (len(wdf) - 1) - anchor_idx
                if anchor_bars_ago > PF_ANCHOR_MAX_STALENESS_BARS:
                    stale_anchor = True
                    stale_warning = (
                        f"WARNING: Count row anchor ({anchor_ev.event_type} on {str(anchor_ev.date)[:10]}) "
                        f"is {anchor_bars_ago} bars old (threshold: {PF_ANCHOR_MAX_STALENESS_BARS} bars) — "
                        "objective may not reflect current structure. "
                    )
            else:
                target_row = current_close

            pf_obj = count_price_objective(
                columns,
                count_row_price=target_row,
                box_size=box_size,
                reversal=3,
                direction="bullish",
                stale_anchor=stale_anchor,
                stale_anchor_warning=stale_warning,
            )

            upside_pct = ((pf_obj.price_objective - current_close) / current_close) * 100.0

            # Stale anchors do not contribute points per 'No Fabricated Confidence'
            if stale_anchor:
                pf_pts = 0.0
            elif upside_pct >= 20.0:
                pf_pts = WEIGHT_PF_UPSIDE  # 10 pts
            elif upside_pct >= 10.0:
                pf_pts = 6.0
            elif upside_pct > 0.0:
                pf_pts = 3.0
            else:
                pf_pts = 0.0
    except Exception:
        pf_obj = None
        pf_pts = 0.0

    # -------------------------------------------------------------
    # 5. Composite Score & Disqualifying Flags (Red Flags)
    # -------------------------------------------------------------
    composite_score = round(mechanical_pts + event_pts + peer_pts + pf_pts, 1)

    score_breakdown = {
        "mechanical_filters": round(mechanical_pts, 1),
        "schematic_recency": round(event_pts, 1),
        "peer_relative_strength": round(peer_pts, 1),
        "pf_target_upside": round(pf_pts, 1),
    }

    disqualifying_flags: list[str] = []

    # Flag 1: Most recent event is UTAD (potential distribution)
    if most_recent_event_type == "UTAD":
        disqualifying_flags.append("Most recent event is UTAD (Upthrust After Distribution / potential distribution phase).")

    # Flag 2: No base accumulation anchor ever found (never formed SC, Spring, or LPS)
    has_sc = len(detected_events.get("SC", [])) > 0
    has_spring = len(detected_events.get("Spring", [])) > 0
    has_lps = len(detected_events.get("LPS", [])) > 0
    if not (has_sc or has_spring or has_lps):
        disqualifying_flags.append("No base accumulation structure detected (no SC, Spring, or LPS in dataset).")

    # Flag 3: Severe downtrend (all mechanical filters failed)
    if not any(filters_passed.values()):
        disqualifying_flags.append("Failed all mechanical trend & momentum filters.")

    return ScoredSetup(
        symbol=symbol,
        as_of_date=as_of_date,
        mechanical_filters_passed=filters_passed,
        detected_events=detected_events,
        most_recent_event_type=most_recent_event_type,
        most_recent_event_date=most_recent_event_date,
        pf_price_objective=pf_obj,
        peer_rank=peer_rank,
        composite_score=composite_score,
        score_breakdown=score_breakdown,
        disqualifying_flags=disqualifying_flags,
        peer_analysis_skipped=peer_analysis_skipped,
    )


def rank_watchlist(
    symbol_to_df: dict[str, pd.DataFrame],
    peer_rankings: Optional[dict[str, int]] = None,
) -> list[ScoredSetup]:
    """Score and rank an entire watchlist.

    Qualified setups (no red flags) are ranked by composite_score descending.
    Disqualified setups are sorted to the bottom regardless of raw score.

    Args:
        symbol_to_df: Dictionary mapping ticker symbols to their OHLCV DataFrames.
        peer_rankings: Optional dictionary of {symbol: rank_int}.

    Returns:
        list[ScoredSetup]: Sorted list of scored setups.
    """
    total_peers = len(symbol_to_df)
    scored_list: list[ScoredSetup] = []

    for sym, df_item in symbol_to_df.items():
        p_rank = peer_rankings.get(sym) if peer_rankings else None
        scored = score_setup(df_item, symbol=sym, peer_rank=p_rank, total_peers=total_peers)
        scored_list.append(scored)

    # Sort key: (not is_disqualified, composite_score) descending
    sorted_setups = sorted(
        scored_list,
        key=lambda s: (not s.is_disqualified, s.composite_score),
        reverse=True,
    )

    return sorted_setups
