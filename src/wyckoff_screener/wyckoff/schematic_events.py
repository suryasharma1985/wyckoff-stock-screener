"""Wyckoff schematic event detection module.

Implements candidate Wyckoff schematic event detection strictly per AGENTS.md rules:
- Selling Climax (SC)
- Automatic Rally (AR)
- Secondary Test (ST)
- Spring
- Last Point of Support (LPS)
- Sign of Strength (SOS)
- Upthrust After Distribution (UTAD)

Guiding Principle — No Fabricated Confidence:
Every flagged event cites the exact numeric evidence behind it.
"""

from typing import Final, Optional, Sequence
import pandas as pd

from wyckoff_screener.indicators.vsa_metrics import (
    close_position as compute_close_position,
    spread_ratio as compute_spread_ratio,
    volume_ratio as compute_volume_ratio,
)
from wyckoff_screener.wyckoff.events import WyckoffEvent
from wyckoff_screener.wyckoff.swing_points import (
    DEFAULT_DECLINE_LOOKBACK,
    DEFAULT_MIN_DECLINE_PCT,
    DEFAULT_RANGE_LOOKBACK,
    detect_prior_decline,
    get_prior_trading_range,
)

# Standard OHLCV column constants
DEFAULT_DATE_COL: Final[str] = "Date"
DEFAULT_OPEN_COL: Final[str] = "Open"
DEFAULT_HIGH_COL: Final[str] = "High"
DEFAULT_LOW_COL: Final[str] = "Low"
DEFAULT_CLOSE_COL: Final[str] = "Close"
DEFAULT_VOLUME_COL: Final[str] = "Volume"

# Selling Climax (SC) Thresholds (AGENTS.md)
# spread_ratio >= 1.5, down-close, volume_ratio >= 2.0, after a clear prior decline
SC_MIN_SPREAD_RATIO: Final[float] = 1.5
SC_MIN_VOLUME_RATIO: Final[float] = 2.0
SC_MIN_DECLINE_PCT: Final[float] = DEFAULT_MIN_DECLINE_PCT

# Automatic Rally (AR) Thresholds (AGENTS.md)
# sharp up bar immediately following an SC candidate, volume_ratio >= 1.0
AR_MIN_VOLUME_RATIO: Final[float] = 1.0
AR_MAX_BARS_AFTER_SC: Final[int] = 3

# Secondary Test (ST) Thresholds (AGENTS.md)
# retest of the SC-candidate low area, volume_ratio lower than the SC candidate's own volume_ratio
ST_PRICE_TOLERANCE_PCT: Final[float] = 0.03
ST_MAX_BARS_AFTER_SC: Final[int] = 15  # Bounded search window: ST develops typically within 2-15 bars after SC

# Spring Thresholds (AGENTS.md)
# bar's low undercuts prior support (even intrabar) then closes back above that level
SPRING_LOOKBACK: Final[int] = DEFAULT_RANGE_LOOKBACK

# Last Point of Support (LPS) Thresholds (AGENTS.md)
# higher low than the most recent Spring/ST candidate, volume_ratio < 0.75, holding above range support
LPS_MAX_VOLUME_RATIO: Final[float] = 0.75
LPS_LOOKBACK: Final[int] = DEFAULT_RANGE_LOOKBACK
LPS_MAX_BARS_AFTER_ANCHOR: Final[int] = 20  # Bounded search window: LPS pullback develops within 1-20 bars of anchor

# Sign of Strength (SOS) Thresholds (AGENTS.md)
# close breaks above range resistance, volume_ratio >= 1.5, close_position > 0.7
SOS_MIN_VOLUME_RATIO: Final[float] = 1.5
SOS_MIN_CLOSE_POSITION: Final[float] = 0.7
SOS_LOOKBACK: Final[int] = DEFAULT_RANGE_LOOKBACK

# Upthrust After Distribution (UTAD) Thresholds (AGENTS.md)
# high breaks above range resistance intrabar but closes back below it, often on elevated volume_ratio
# Note: 1.5 is chosen for UTAD_MIN_VOLUME_RATIO to align with the "High" volume band (1.5 - 2.0)
# defined in AGENTS.md, ensuring "elevated volume" is strictly elevated rather than Average (0.75 - 1.5).
UTAD_MIN_VOLUME_RATIO: Final[float] = 1.5
UTAD_LOOKBACK: Final[int] = DEFAULT_RANGE_LOOKBACK


def _ensure_vsa_columns(
    df: pd.DataFrame,
    high_col: str = DEFAULT_HIGH_COL,
    low_col: str = DEFAULT_LOW_COL,
    close_col: str = DEFAULT_CLOSE_COL,
    volume_col: str = DEFAULT_VOLUME_COL,
) -> pd.DataFrame:
    """Ensure DataFrame has volume_ratio, spread_ratio, and close_position columns."""
    working_df = df.copy()
    if "volume_ratio" not in working_df.columns:
        working_df["volume_ratio"] = compute_volume_ratio(working_df, volume_col=volume_col)
    if "spread_ratio" not in working_df.columns:
        working_df["spread_ratio"] = compute_spread_ratio(
            working_df, high_col=high_col, low_col=low_col, close_col=close_col
        )
    if "close_position" not in working_df.columns:
        working_df["close_position"] = compute_close_position(
            working_df, high_col=high_col, low_col=low_col, close_col=close_col
        )
    return working_df


def detect_selling_climax_candidates(
    df: pd.DataFrame,
    spread_ratio_min: float = SC_MIN_SPREAD_RATIO,
    volume_ratio_min: float = SC_MIN_VOLUME_RATIO,
    min_decline_pct: float = SC_MIN_DECLINE_PCT,
    decline_lookback: int = DEFAULT_DECLINE_LOOKBACK,
    date_col: str = DEFAULT_DATE_COL,
    open_col: str = DEFAULT_OPEN_COL,
    high_col: str = DEFAULT_HIGH_COL,
    low_col: str = DEFAULT_LOW_COL,
    close_col: str = DEFAULT_CLOSE_COL,
    volume_col: str = DEFAULT_VOLUME_COL,
) -> list[WyckoffEvent]:
    """Detect candidate Selling Climax (SC) bars.

    AGENTS.md Rule:
        "SC candidate: spread_ratio >= 1.5, down-close, volume_ratio >= 2.0, after a clear prior decline"

    Args:
        df: Input OHLCV DataFrame.
        spread_ratio_min: Minimum spread ratio threshold (default 1.5).
        volume_ratio_min: Minimum volume ratio threshold (default 2.0).
        min_decline_pct: Minimum prior decline fractional drop (default 0.03).
        decline_lookback: Lookback window for prior decline (default 10).
        date_col: Date column name.
        open_col: Open column name.
        high_col: High column name.
        low_col: Low column name.
        close_col: Close column name.
        volume_col: Volume column name.

    Returns:
        list[WyckoffEvent]: List of detected candidate SC events with quantitative evidence.
    """
    wdf = _ensure_vsa_columns(df, high_col=high_col, low_col=low_col, close_col=close_col, volume_col=volume_col)
    events: list[WyckoffEvent] = []

    for i in range(len(wdf)):
        vr = float(wdf["volume_ratio"].iloc[i])
        sr = float(wdf["spread_ratio"].iloc[i])
        cp = float(wdf["close_position"].iloc[i])
        close_val = float(wdf[close_col].iloc[i])
        open_val = float(wdf[open_col].iloc[i])
        date_val = wdf[date_col].iloc[i] if date_col in wdf.columns else i

        if pd.isna(vr) or pd.isna(sr):
            continue

        # Down-close check: close below open
        is_down_close = close_val < open_val

        # Numeric criteria check
        if sr >= spread_ratio_min and vr >= volume_ratio_min and is_down_close:
            is_decline, drop_pct, decline_note = detect_prior_decline(
                wdf,
                end_idx=i,
                lookback=decline_lookback,
                min_drop_pct=min_decline_pct,
                close_col=close_col,
                high_col=high_col,
                low_col=low_col,
            )

            if is_decline:
                note = (
                    f"Candidate SC: volume {vr:.2f}x 20-period avg (threshold >= {volume_ratio_min:.1f}x), "
                    f"spread {sr:.2f}x 20-period ATR (threshold >= {spread_ratio_min:.1f}x), "
                    f"down-close (Open={open_val:.2f}, Close={close_val:.2f}, close pos={cp:.2f}), "
                    f"{decline_note}"
                )
                events.append(
                    WyckoffEvent(
                        event_type="SC",
                        date=date_val,
                        price=close_val,
                        volume_ratio=vr,
                        spread_ratio=sr,
                        close_position=cp,
                        supporting_note=note,
                    )
                )

    return events


def detect_automatic_rally_candidates(
    df: pd.DataFrame,
    sc_events: Optional[Sequence[WyckoffEvent]] = None,
    volume_ratio_min: float = AR_MIN_VOLUME_RATIO,
    max_bars_after_sc: int = AR_MAX_BARS_AFTER_SC,
    date_col: str = DEFAULT_DATE_COL,
    open_col: str = DEFAULT_OPEN_COL,
    high_col: str = DEFAULT_HIGH_COL,
    low_col: str = DEFAULT_LOW_COL,
    close_col: str = DEFAULT_CLOSE_COL,
    volume_col: str = DEFAULT_VOLUME_COL,
) -> list[WyckoffEvent]:
    """Detect candidate Automatic Rally (AR) bars.

    AGENTS.md Rule:
        "AR candidate: sharp up bar immediately following an SC candidate, volume_ratio >= 1.0"

    Args:
        df: Input OHLCV DataFrame.
        sc_events: Prior SC events to search after. If None, auto-detects SCs.
        volume_ratio_min: Minimum volume ratio threshold (default 1.0).
        max_bars_after_sc: Maximum bars to search after an SC (default 3).
        date_col: Date column name.
        open_col: Open column name.
        high_col: High column name.
        low_col: Low column name.
        close_col: Close column name.
        volume_col: Volume column name.

    Returns:
        list[WyckoffEvent]: List of candidate AR events.
    """
    wdf = _ensure_vsa_columns(df, high_col=high_col, low_col=low_col, close_col=close_col, volume_col=volume_col)
    if sc_events is None:
        sc_events = detect_selling_climax_candidates(
            wdf, date_col=date_col, open_col=open_col, high_col=high_col, low_col=low_col, close_col=close_col, volume_col=volume_col
        )

    events: list[WyckoffEvent] = []
    date_to_idx = {wdf[date_col].iloc[k]: k for k in range(len(wdf))} if date_col in wdf.columns else {k: k for k in range(len(wdf))}

    for sc in sc_events:
        sc_idx = date_to_idx.get(sc.date)
        if sc_idx is None:
            continue

        # Search immediately following bars (1 to max_bars_after_sc)
        for offset in range(1, max_bars_after_sc + 1):
            idx = sc_idx + offset
            if idx >= len(wdf):
                break

            vr = float(wdf["volume_ratio"].iloc[idx])
            sr = float(wdf["spread_ratio"].iloc[idx])
            cp = float(wdf["close_position"].iloc[idx])
            close_val = float(wdf[close_col].iloc[idx])
            open_val = float(wdf[open_col].iloc[idx])
            date_val = wdf[date_col].iloc[idx] if date_col in wdf.columns else idx

            # Up bar condition: Close > Open and Close > sc.price
            is_up_bar = close_val > open_val and close_val > sc.price
            if is_up_bar and vr >= volume_ratio_min:
                note = (
                    f"Candidate AR: up bar {offset} bar(s) after SC (SC date={sc.date}, SC price={sc.price:.2f}), "
                    f"Open={open_val:.2f}, Close={close_val:.2f}, close pos={cp:.2f}, "
                    f"volume {vr:.2f}x avg (threshold >= {volume_ratio_min:.1f}x), spread {sr:.2f}x ATR"
                )
                events.append(
                    WyckoffEvent(
                        event_type="AR",
                        date=date_val,
                        price=close_val,
                        volume_ratio=vr,
                        spread_ratio=sr,
                        close_position=cp,
                        supporting_note=note,
                    )
                )
                break  # Record the primary initial sharp AR following SC

    return events


def detect_secondary_test_candidates(
    df: pd.DataFrame,
    sc_events: Optional[Sequence[WyckoffEvent]] = None,
    tolerance_pct: float = ST_PRICE_TOLERANCE_PCT,
    max_bars_after_sc: int = ST_MAX_BARS_AFTER_SC,
    date_col: str = DEFAULT_DATE_COL,
    open_col: str = DEFAULT_OPEN_COL,
    high_col: str = DEFAULT_HIGH_COL,
    low_col: str = DEFAULT_LOW_COL,
    close_col: str = DEFAULT_CLOSE_COL,
    volume_col: str = DEFAULT_VOLUME_COL,
) -> list[WyckoffEvent]:
    """Detect candidate Secondary Test (ST) bars.

    AGENTS.md Rule:
        "ST candidate: retest of the SC-candidate low area, volume_ratio lower than the SC candidate's own volume_ratio"

    Args:
        df: Input OHLCV DataFrame.
        sc_events: Prior SC events to test against. If None, auto-detects SCs.
        tolerance_pct: Retest low area tolerance (default 0.03 / 3%).
        max_bars_after_sc: Maximum bars to search forward from the SC anchor (default 15).
        date_col: Date column name.
        open_col: Open column name.
        high_col: High column name.
        low_col: Low column name.
        close_col: Close column name.
        volume_col: Volume column name.

    Returns:
        list[WyckoffEvent]: List of candidate ST events (at most one per SC anchor).
    """
    wdf = _ensure_vsa_columns(df, high_col=high_col, low_col=low_col, close_col=close_col, volume_col=volume_col)
    if sc_events is None:
        sc_events = detect_selling_climax_candidates(
            wdf, date_col=date_col, open_col=open_col, high_col=high_col, low_col=low_col, close_col=close_col, volume_col=volume_col
        )

    events: list[WyckoffEvent] = []
    date_to_idx = {wdf[date_col].iloc[k]: k for k in range(len(wdf))} if date_col in wdf.columns else {k: k for k in range(len(wdf))}

    for sc in sc_events:
        sc_idx = date_to_idx.get(sc.date)
        if sc_idx is None:
            continue

        sc_low = float(wdf[low_col].iloc[sc_idx])
        # Look within bounded window after SC (start 2 bars after to allow AR rebound first)
        end_search_idx = min(len(wdf), sc_idx + max_bars_after_sc + 1)
        for idx in range(sc_idx + 2, end_search_idx):
            curr_low = float(wdf[low_col].iloc[idx])
            vr = float(wdf["volume_ratio"].iloc[idx])
            sr = float(wdf["spread_ratio"].iloc[idx])
            cp = float(wdf["close_position"].iloc[idx])
            close_val = float(wdf[close_col].iloc[idx])
            date_val = wdf[date_col].iloc[idx] if date_col in wdf.columns else idx

            # Retest of low area: low is within tolerance band of SC low
            retest_dist = abs(curr_low - sc_low) / sc_low
            is_retest = retest_dist <= tolerance_pct or (curr_low >= sc_low * (1.0 - tolerance_pct) and curr_low <= sc_low * (1.0 + tolerance_pct))

            # Strictly lower volume than SC candidate's own volume ratio
            is_lower_vol = vr < sc.volume_ratio

            if is_retest and is_lower_vol:
                note = (
                    f"Candidate ST: retest of SC low area (SC low={sc_low:.2f}, bar low={curr_low:.2f}, diff={retest_dist * 100:.1f}%), "
                    f"volume {vr:.2f}x avg strictly lower than SC volume {sc.volume_ratio:.2f}x, "
                    f"spread {sr:.2f}x ATR, close pos={cp:.2f}"
                )
                events.append(
                    WyckoffEvent(
                        event_type="ST",
                        date=date_val,
                        price=close_val,
                        volume_ratio=vr,
                        spread_ratio=sr,
                        close_position=cp,
                        supporting_note=note,
                    )
                )
                break  # Record only the first qualifying ST per SC anchor

    return events


def detect_spring_candidates(
    df: pd.DataFrame,
    lookback: int = SPRING_LOOKBACK,
    date_col: str = DEFAULT_DATE_COL,
    open_col: str = DEFAULT_OPEN_COL,
    high_col: str = DEFAULT_HIGH_COL,
    low_col: str = DEFAULT_LOW_COL,
    close_col: str = DEFAULT_CLOSE_COL,
    volume_col: str = DEFAULT_VOLUME_COL,
) -> list[WyckoffEvent]:
    """Detect candidate Spring bars.

    AGENTS.md Rule:
        "Spring candidate: bar's low undercuts prior support (even intrabar) then closes back above that level"

    Args:
        df: Input OHLCV DataFrame.
        lookback: Trading range support lookback window (default 50).
        date_col: Date column name.
        open_col: Open column name.
        high_col: High column name.
        low_col: Low column name.
        close_col: Close column name.
        volume_col: Volume column name.

    Returns:
        list[WyckoffEvent]: List of candidate Spring events.
    """
    wdf = _ensure_vsa_columns(df, high_col=high_col, low_col=low_col, close_col=close_col, volume_col=volume_col)
    events: list[WyckoffEvent] = []

    for i in range(1, len(wdf)):
        range_ctx = get_prior_trading_range(wdf, end_idx=i, lookback=lookback, high_col=high_col, low_col=low_col)
        prior_support = range_ctx.support

        bar_low = float(wdf[low_col].iloc[i])
        bar_close = float(wdf[close_col].iloc[i])
        vr = float(wdf["volume_ratio"].iloc[i])
        sr = float(wdf["spread_ratio"].iloc[i])
        cp = float(wdf["close_position"].iloc[i])
        date_val = wdf[date_col].iloc[i] if date_col in wdf.columns else i

        # Undercut support intrabar and close back above support level
        if bar_low < prior_support and bar_close > prior_support:
            undercut_pct = (prior_support - bar_low) / prior_support
            note = (
                f"Candidate Spring: low={bar_low:.2f} undercut prior support={prior_support:.2f} "
                f"by {undercut_pct * 100:.2f}%, closed back above support at {bar_close:.2f} "
                f"(close pos={cp:.2f}, volume {vr:.2f}x avg, spread {sr:.2f}x ATR)"
            )
            events.append(
                WyckoffEvent(
                    event_type="Spring",
                    date=date_val,
                    price=bar_close,
                    volume_ratio=vr,
                    spread_ratio=sr,
                    close_position=cp,
                    supporting_note=note,
                )
            )

    return events


def detect_lps_candidates(
    df: pd.DataFrame,
    prior_events: Optional[Sequence[WyckoffEvent]] = None,
    max_volume_ratio: float = LPS_MAX_VOLUME_RATIO,
    lookback: int = LPS_LOOKBACK,
    max_bars_after_anchor: int = LPS_MAX_BARS_AFTER_ANCHOR,
    date_col: str = DEFAULT_DATE_COL,
    open_col: str = DEFAULT_OPEN_COL,
    high_col: str = DEFAULT_HIGH_COL,
    low_col: str = DEFAULT_LOW_COL,
    close_col: str = DEFAULT_CLOSE_COL,
    volume_col: str = DEFAULT_VOLUME_COL,
) -> list[WyckoffEvent]:
    """Detect candidate Last Point of Support (LPS) bars.

    AGENTS.md Rule:
        "LPS candidate: higher low than the most recent Spring/ST candidate, volume_ratio < 0.75, holding above range support"

    Args:
        df: Input OHLCV DataFrame.
        prior_events: Prior detected events (Spring or ST). If None, auto-detected.
        max_volume_ratio: Maximum volume ratio threshold (default 0.75).
        lookback: Trading range lookback (default 50).
        max_bars_after_anchor: Maximum bars to search forward from each anchor (default 20).
        date_col: Date column name.
        open_col: Open column name.
        high_col: High column name.
        low_col: Low column name.
        close_col: Close column name.
        volume_col: Volume column name.

    Returns:
        list[WyckoffEvent]: List of candidate LPS events (at most one per anchor).
    """
    wdf = _ensure_vsa_columns(df, high_col=high_col, low_col=low_col, close_col=close_col, volume_col=volume_col)
    if prior_events is None:
        springs = detect_spring_candidates(wdf, lookback=lookback, date_col=date_col, open_col=open_col, high_col=high_col, low_col=low_col, close_col=close_col, volume_col=volume_col)
        sts = detect_secondary_test_candidates(wdf, date_col=date_col, open_col=open_col, high_col=high_col, low_col=low_col, close_col=close_col, volume_col=volume_col)
        prior_events = springs + sts

    events: list[WyckoffEvent] = []
    date_to_idx = {wdf[date_col].iloc[k]: k for k in range(len(wdf))} if date_col in wdf.columns else {k: k for k in range(len(wdf))}

    for prev_event in prior_events:
        prev_idx = date_to_idx.get(prev_event.date)
        if prev_idx is None:
            continue

        prev_low = float(wdf[low_col].iloc[prev_idx])
        end_search_idx = min(len(wdf), prev_idx + max_bars_after_anchor + 1)

        for idx in range(prev_idx + 1, end_search_idx):
            curr_low = float(wdf[low_col].iloc[idx])
            curr_close = float(wdf[close_col].iloc[idx])
            vr = float(wdf["volume_ratio"].iloc[idx])
            sr = float(wdf["spread_ratio"].iloc[idx])
            cp = float(wdf["close_position"].iloc[idx])
            date_val = wdf[date_col].iloc[idx] if date_col in wdf.columns else idx

            range_ctx = get_prior_trading_range(wdf, end_idx=idx, lookback=lookback, high_col=high_col, low_col=low_col)

            # Higher low than prior Spring/ST candidate, volume < 0.75, holding above range support
            is_higher_low = curr_low > prev_low
            is_low_volume = vr < max_volume_ratio
            holds_support = curr_close >= range_ctx.support and curr_low >= range_ctx.support

            if is_higher_low and is_low_volume and holds_support:
                note = (
                    f"Candidate LPS: higher low={curr_low:.2f} vs prior {prev_event.event_type} low={prev_low:.2f} "
                    f"(+{((curr_low - prev_low) / prev_low) * 100:.1f}%), holding above range support={range_ctx.support:.2f}, "
                    f"low volume {vr:.2f}x avg (threshold < {max_volume_ratio:.2f}x), spread {sr:.2f}x ATR, close pos={cp:.2f}"
                )
                events.append(
                    WyckoffEvent(
                        event_type="LPS",
                        date=date_val,
                        price=curr_close,
                        volume_ratio=vr,
                        spread_ratio=sr,
                        close_position=cp,
                        supporting_note=note,
                    )
                )
                break  # Record only the first qualifying LPS per anchor

    return events


def detect_sos_candidates(
    df: pd.DataFrame,
    min_volume_ratio: float = SOS_MIN_VOLUME_RATIO,
    min_close_position: float = SOS_MIN_CLOSE_POSITION,
    lookback: int = SOS_LOOKBACK,
    date_col: str = DEFAULT_DATE_COL,
    open_col: str = DEFAULT_OPEN_COL,
    high_col: str = DEFAULT_HIGH_COL,
    low_col: str = DEFAULT_LOW_COL,
    close_col: str = DEFAULT_CLOSE_COL,
    volume_col: str = DEFAULT_VOLUME_COL,
) -> list[WyckoffEvent]:
    """Detect candidate Sign of Strength (SOS / Breakout) bars.

    AGENTS.md Rule:
        "SOS candidate: close breaks above range resistance, volume_ratio >= 1.5, close_position > 0.7"

    Args:
        df: Input OHLCV DataFrame.
        min_volume_ratio: Minimum volume ratio threshold (default 1.5).
        min_close_position: Minimum close position threshold (default 0.7).
        lookback: Trading range lookback window (default 50).
        date_col: Date column name.
        open_col: Open column name.
        high_col: High column name.
        low_col: Low column name.
        close_col: Close column name.
        volume_col: Volume column name.

    Returns:
        list[WyckoffEvent]: List of candidate SOS events.
    """
    wdf = _ensure_vsa_columns(df, high_col=high_col, low_col=low_col, close_col=close_col, volume_col=volume_col)
    events: list[WyckoffEvent] = []

    for i in range(1, len(wdf)):
        range_ctx = get_prior_trading_range(wdf, end_idx=i, lookback=lookback, high_col=high_col, low_col=low_col)
        range_resistance = range_ctx.resistance

        bar_close = float(wdf[close_col].iloc[i])
        vr = float(wdf["volume_ratio"].iloc[i])
        sr = float(wdf["spread_ratio"].iloc[i])
        cp = float(wdf["close_position"].iloc[i])
        date_val = wdf[date_col].iloc[i] if date_col in wdf.columns else i

        # Close breaks above range resistance, volume_ratio >= 1.5, close_position > 0.7
        if bar_close > range_resistance and vr >= min_volume_ratio and cp > min_close_position:
            breakout_pct = (bar_close - range_resistance) / range_resistance
            note = (
                f"Candidate SOS: close={bar_close:.2f} broke above range resistance={range_resistance:.2f} "
                f"(+{breakout_pct * 100:.2f}%), strong close position={cp:.2f} (threshold > {min_close_position:.1f}), "
                f"volume {vr:.2f}x avg (threshold >= {min_volume_ratio:.1f}x), spread {sr:.2f}x ATR"
            )
            events.append(
                WyckoffEvent(
                    event_type="SOS",
                    date=date_val,
                    price=bar_close,
                    volume_ratio=vr,
                    spread_ratio=sr,
                    close_position=cp,
                    supporting_note=note,
                )
            )

    return events


def detect_utad_candidates(
    df: pd.DataFrame,
    min_volume_ratio: float = UTAD_MIN_VOLUME_RATIO,
    lookback: int = UTAD_LOOKBACK,
    date_col: str = DEFAULT_DATE_COL,
    open_col: str = DEFAULT_OPEN_COL,
    high_col: str = DEFAULT_HIGH_COL,
    low_col: str = DEFAULT_LOW_COL,
    close_col: str = DEFAULT_CLOSE_COL,
    volume_col: str = DEFAULT_VOLUME_COL,
) -> list[WyckoffEvent]:
    """Detect candidate Upthrust After Distribution (UTAD) bars.

    AGENTS.md Rule:
        "UTAD candidate: high breaks above range resistance intrabar but closes back below it, often on elevated volume_ratio"

    Args:
        df: Input OHLCV DataFrame.
        min_volume_ratio: Minimum volume ratio threshold (default 1.5).
        lookback: Trading range lookback window (default 50).
        date_col: Date column name.
        open_col: Open column name.
        high_col: High column name.
        low_col: Low column name.
        close_col: Close column name.
        volume_col: Volume column name.

    Returns:
        list[WyckoffEvent]: List of candidate UTAD events.
    """
    wdf = _ensure_vsa_columns(df, high_col=high_col, low_col=low_col, close_col=close_col, volume_col=volume_col)
    events: list[WyckoffEvent] = []

    for i in range(1, len(wdf)):
        range_ctx = get_prior_trading_range(wdf, end_idx=i, lookback=lookback, high_col=high_col, low_col=low_col)
        range_resistance = range_ctx.resistance

        bar_high = float(wdf[high_col].iloc[i])
        bar_close = float(wdf[close_col].iloc[i])
        vr = float(wdf["volume_ratio"].iloc[i])
        sr = float(wdf["spread_ratio"].iloc[i])
        cp = float(wdf["close_position"].iloc[i])
        date_val = wdf[date_col].iloc[i] if date_col in wdf.columns else i

        # High breaks above resistance intrabar but closes back below it
        if bar_high > range_resistance and bar_close < range_resistance and vr >= min_volume_ratio:
            false_break_pct = (bar_high - range_resistance) / range_resistance
            note = (
                f"Candidate UTAD: intrabar high={bar_high:.2f} exceeded range resistance={range_resistance:.2f} "
                f"(+{false_break_pct * 100:.2f}%), closed back below at {bar_close:.2f} (close pos={cp:.2f}), "
                f"elevated volume {vr:.2f}x avg (threshold >= {min_volume_ratio:.1f}x), spread {sr:.2f}x ATR"
            )
            events.append(
                WyckoffEvent(
                    event_type="UTAD",
                    date=date_val,
                    price=bar_close,
                    volume_ratio=vr,
                    spread_ratio=sr,
                    close_position=cp,
                    supporting_note=note,
                )
            )

    return events


def detect_all_schematic_events(
    df: pd.DataFrame,
    date_col: str = DEFAULT_DATE_COL,
    open_col: str = DEFAULT_OPEN_COL,
    high_col: str = DEFAULT_HIGH_COL,
    low_col: str = DEFAULT_LOW_COL,
    close_col: str = DEFAULT_CLOSE_COL,
    volume_col: str = DEFAULT_VOLUME_COL,
) -> dict[str, list[WyckoffEvent]]:
    """Detect all candidate Wyckoff schematic events in the given dataset."""
    wdf = _ensure_vsa_columns(df, high_col=high_col, low_col=low_col, close_col=close_col, volume_col=volume_col)

    sc_events = detect_selling_climax_candidates(wdf, date_col=date_col, open_col=open_col, high_col=high_col, low_col=low_col, close_col=close_col, volume_col=volume_col)
    ar_events = detect_automatic_rally_candidates(wdf, sc_events=sc_events, date_col=date_col, open_col=open_col, high_col=high_col, low_col=low_col, close_col=close_col, volume_col=volume_col)
    st_events = detect_secondary_test_candidates(wdf, sc_events=sc_events, date_col=date_col, open_col=open_col, high_col=high_col, low_col=low_col, close_col=close_col, volume_col=volume_col)
    spring_events = detect_spring_candidates(wdf, date_col=date_col, open_col=open_col, high_col=high_col, low_col=low_col, close_col=close_col, volume_col=volume_col)
    lps_events = detect_lps_candidates(wdf, prior_events=spring_events + st_events, date_col=date_col, open_col=open_col, high_col=high_col, low_col=low_col, close_col=close_col, volume_col=volume_col)
    sos_events = detect_sos_candidates(wdf, date_col=date_col, open_col=open_col, high_col=high_col, low_col=low_col, close_col=close_col, volume_col=volume_col)
    utad_events = detect_utad_candidates(wdf, date_col=date_col, open_col=open_col, high_col=high_col, low_col=low_col, close_col=close_col, volume_col=volume_col)

    return {
        "SC": sc_events,
        "AR": ar_events,
        "ST": st_events,
        "Spring": spring_events,
        "LPS": lps_events,
        "SOS": sos_events,
        "UTAD": utad_events,
    }
