"""Broad mechanical filter and batch screening engine for NSE equities.

Guiding Principles (AGENTS.md):
- Exact numeric calculations strictly separate from TradingView visual review.
- Never call a passing stock a 'buy signal' or 'confirmed accumulation'.
- Use candidate_event_detected, possible_LPS, and manual_review_pending terminology.
- Explicitly check whether the latest weekly bar is complete.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Final, Optional, Sequence
import numpy as np
import pandas as pd

from wyckoff_screener.charting.tradingview_links import (
    ChartReviewRecord,
    TradingViewLinks,
    generate_tradingview_links,
)
from wyckoff_screener.indicators.momentum import (
    RSI_BULLISH_BAND_LOWER,
    RSI_BULLISH_BAND_UPPER,
    rsi,
)
from wyckoff_screener.indicators.moving_averages import (
    PERIOD_MA_50,
    PERIOD_MA_100,
    PERIOD_MA_30_WEEK,
    PERIOD_MA_40_WEEK,
    simple_moving_average,
    sma_30_week,
    sma_40_week,
    weekly_simple_moving_average,
)
from wyckoff_screener.indicators.volatility import (
    atr_contraction_ratio,
    bollinger_band_width,
)
from wyckoff_screener.wyckoff.schematic_events import detect_all_schematic_events

# Default minimum 20-day average daily turnover in INR Crores (1 Crore = 10,000,000 INR)
DEFAULT_MIN_AVG_TURNOVER_CR: Final[float] = 1.0


@dataclass
class BatchScreeningResult:
    """Complete quantitative screening outcome for a single stock."""

    symbol: str
    company_name: str
    as_of_date: str
    data_bars: int
    data_quality_flags: list[str]
    filter_results: dict[str, bool]
    filter_values: dict[str, Any]
    is_mechanically_qualified: bool
    latest_weekly_bar_complete: bool
    candidate_event_summary: dict[str, Any]
    liquidity_metrics: dict[str, float]
    tradingview_chart_links: TradingViewLinks
    chart_review_record: ChartReviewRecord
    manual_review_pending: bool = True
    errors: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert result to flat dictionary for tabular export."""
        return {
            "symbol": self.symbol,
            "company_name": self.company_name,
            "as_of_date": self.as_of_date,
            "data_bars": self.data_bars,
            "is_mechanically_qualified": self.is_mechanically_qualified,
            "latest_weekly_bar_complete": self.latest_weekly_bar_complete,
            "candidate_event_detected": self.candidate_event_summary.get("candidate_event_detected"),
            "event_date": self.candidate_event_summary.get("event_date"),
            "possible_LPS": self.candidate_event_summary.get("is_possible_LPS", False),
            "possible_SOS": self.candidate_event_summary.get("is_possible_SOS", False),
            "possible_Spring": self.candidate_event_summary.get("is_possible_Spring", False),
            "UTAD_warning": self.candidate_event_summary.get("is_UTAD_warning", False),
            "manual_review_pending": self.manual_review_pending,
            "chart_review_status": self.chart_review_record.chart_review_status,
            "weekly_uptrend": self.filter_results.get("weekly_uptrend", False),
            "dma_50_above_100": self.filter_results.get("dma_50_above_100", False),
            "rsi_in_band": self.filter_results.get("rsi_in_band", False),
            "atr_contracting": self.filter_results.get("atr_contracting", False),
            "vcp_bbw_contracting": self.filter_results.get("vcp_bbw_contracting", False),
            "min_liquidity_passed": self.filter_results.get("min_liquidity_passed", False),
            "close": self.filter_values.get("close"),
            "rsi_14": self.filter_values.get("rsi_14"),
            "dma_50": self.filter_values.get("dma_50"),
            "dma_100": self.filter_values.get("dma_100"),
            "atr_contraction_ratio": self.filter_values.get("atr_contraction_ratio"),
            "bb_width_20": self.filter_values.get("bb_width_20"),
            "avg_daily_turnover_cr": self.liquidity_metrics.get("avg_20_turnover_cr"),
            "tradingview_daily_url": self.tradingview_chart_links.daily_url,
            "tradingview_weekly_url": self.tradingview_chart_links.weekly_url,
            "tradingview_intraday_url": self.tradingview_chart_links.intraday_75m_url,
            "numeric_evidence": self.candidate_event_summary.get("numeric_evidence", ""),
            "data_quality_flags": "; ".join(self.data_quality_flags) if self.data_quality_flags else "None",
            "errors": "; ".join(self.errors) if self.errors else "None",
        }


def check_weekly_bar_completeness(df: pd.DataFrame, date_col: str = "Date") -> bool:
    """Determine if the latest bar represents a completed trading week (Friday close)."""
    if df.empty or date_col not in df.columns:
        return False
    latest_dt = pd.to_datetime(df[date_col].iloc[-1])
    # Day 4 in Python datetime is Friday (Monday=0, Friday=4)
    # If latest date is Friday or weekend, the trading week is complete
    return latest_dt.weekday() >= 4


def evaluate_broad_setup(
    df: pd.DataFrame,
    symbol: str,
    company_name: str = "",
    min_avg_turnover_cr: float = DEFAULT_MIN_AVG_TURNOVER_CR,
    min_bars: int = 60,
    date_col: str = "Date",
    close_col: str = "Close",
    high_col: str = "High",
    low_col: str = "Low",
    volume_col: str = "Volume",
    events: Optional[dict[str, list[Any]]] = None,
) -> BatchScreeningResult:
    """Run reproducible quantitative screening across OHLCV history for a single stock.

    Args:
        df: Validated OHLCV DataFrame.
        symbol: Ticker symbol.
        company_name: Optional company name.
        min_avg_turnover_cr: Minimum 20-day average daily turnover threshold in Crores (default 1.0).
        min_bars: Minimum historical bars required.
        date_col: Date column name.
        close_col: Close column name.
        high_col: High column name.
        low_col: Low column name.
        volume_col: Volume column name.
        events: Optional precomputed dictionary of Wyckoff events to avoid duplicate calculation.

    Returns:
        BatchScreeningResult containing exact filter values, candidate event summary, and TradingView links.
    """
    errors: list[str] = []
    quality_flags: list[str] = []

    if df.empty or len(df) < min_bars:
        quality_flags.append(f"Insufficient history: {len(df)} bars (min {min_bars}).")

    wdf = df.copy()
    if date_col in wdf.columns:
        wdf[date_col] = pd.to_datetime(wdf[date_col])
        wdf = wdf.sort_values(by=date_col).reset_index(drop=True)

    as_of_date = str(wdf[date_col].iloc[-1])[:10] if date_col in wdf.columns and not wdf.empty else "N/A"
    is_weekly_complete = check_weekly_bar_completeness(wdf, date_col=date_col)

    # 1. Moving Averages & Trend
    close_series = wdf[close_col]
    sma_50 = simple_moving_average(wdf, period=PERIOD_MA_50, column=close_col)
    sma_100 = simple_moving_average(wdf, period=PERIOD_MA_100, column=close_col)

    cur_close = float(close_series.iloc[-1]) if not close_series.empty else 0.0
    cur_sma_50 = float(sma_50.iloc[-1]) if not sma_50.empty and pd.notna(sma_50.iloc[-1]) else None
    cur_sma_100 = float(sma_100.iloc[-1]) if not sma_100.empty and pd.notna(sma_100.iloc[-1]) else None

    # Weekly MA (resampled)
    try:
        wma_30 = sma_30_week(wdf, date_col=date_col, column=close_col)
        wma_40 = sma_40_week(wdf, date_col=date_col, column=close_col)
        cur_wma_30 = float(wma_30.iloc[-1]) if not wma_30.empty and pd.notna(wma_30.iloc[-1]) else None
        cur_wma_40 = float(wma_40.iloc[-1]) if not wma_40.empty and pd.notna(wma_40.iloc[-1]) else None
    except Exception as exc:
        cur_wma_30, cur_wma_40 = None, None
        errors.append(f"Weekly MA error: {exc}")

    # 2. Momentum / RSI
    rsi_series = rsi(wdf, column=close_col)
    cur_rsi = float(rsi_series.iloc[-1]) if not rsi_series.empty and pd.notna(rsi_series.iloc[-1]) else None

    # 3. Volatility & VCP Contraction
    try:
        atr_ratio_series = atr_contraction_ratio(wdf, high_col=high_col, low_col=low_col, close_col=close_col)
        cur_atr_ratio = float(atr_ratio_series.iloc[-1]) if not atr_ratio_series.empty and pd.notna(atr_ratio_series.iloc[-1]) else None
    except Exception as exc:
        cur_atr_ratio = None
        errors.append(f"ATR Contraction error: {exc}")

    bbw_series = bollinger_band_width(wdf, column=close_col)
    cur_bbw = float(bbw_series.iloc[-1]) if not bbw_series.empty and pd.notna(bbw_series.iloc[-1]) else None

    # 4. Liquidity & Turnover
    # Daily turnover = Close * Volume in INR; In Crores = (Close * Volume) / 10,000,000
    daily_turnover_cr = (wdf[close_col] * wdf[volume_col]) / 10_000_000.0
    avg_20_turnover_cr = float(daily_turnover_cr.rolling(20).mean().iloc[-1]) if len(daily_turnover_cr) >= 20 else float(daily_turnover_cr.mean())
    avg_20_vol = float(wdf[volume_col].rolling(20).mean().iloc[-1]) if len(wdf) >= 20 else float(wdf[volume_col].mean())

    # 5. Filter evaluations
    pass_weekly = bool(cur_wma_30 is not None and cur_wma_40 is not None and cur_wma_30 > cur_wma_40 and cur_close > cur_wma_30)
    pass_dma = bool(cur_sma_50 is not None and cur_sma_100 is not None and cur_sma_50 > cur_sma_100 and cur_close > cur_sma_50)
    pass_rsi = bool(cur_rsi is not None and RSI_BULLISH_BAND_LOWER <= cur_rsi <= RSI_BULLISH_BAND_UPPER)
    pass_atr = bool(cur_atr_ratio is not None and cur_atr_ratio < 1.0)
    pass_bbw = bool(cur_bbw is not None and len(bbw_series.dropna()) >= 20 and cur_bbw <= bbw_series.rolling(20).mean().iloc[-1])
    pass_liq = bool(avg_20_turnover_cr >= min_avg_turnover_cr)

    filter_results = {
        "weekly_uptrend": pass_weekly,
        "dma_50_above_100": pass_dma,
        "rsi_in_band": pass_rsi,
        "atr_contracting": pass_atr,
        "vcp_bbw_contracting": pass_bbw,
        "min_liquidity_passed": pass_liq,
    }

    # Compound Mechanical Qualification Rule:
    is_mechanically_qualified = bool(
        pass_liq and (pass_weekly or pass_dma) and (pass_rsi or pass_atr or pass_bbw)
    )

    filter_values = {
        "close": round(cur_close, 2),
        "dma_50": round(cur_sma_50, 2) if cur_sma_50 else None,
        "dma_100": round(cur_sma_100, 2) if cur_sma_100 else None,
        "weekly_sma_30": round(cur_wma_30, 2) if cur_wma_30 else None,
        "weekly_sma_40": round(cur_wma_40, 2) if cur_wma_40 else None,
        "rsi_14": round(cur_rsi, 1) if cur_rsi else None,
        "atr_contraction_ratio": round(cur_atr_ratio, 2) if cur_atr_ratio else None,
        "bb_width_20": round(cur_bbw, 3) if cur_bbw else None,
    }

    liquidity_metrics = {
        "latest_close": round(cur_close, 2),
        "avg_20_volume": round(avg_20_vol, 0),
        "avg_20_turnover_cr": round(avg_20_turnover_cr, 2),
    }

    # 6. Schematic Event Detection
    candidate_summary: dict[str, Any] = {
        "candidate_event_detected": None,
        "event_date": None,
        "is_possible_LPS": False,
        "is_possible_SOS": False,
        "is_possible_Spring": False,
        "is_UTAD_warning": False,
        "numeric_evidence": "",
    }

    try:
        ev_dict = events if events is not None else detect_all_schematic_events(
            wdf,
            date_col=date_col,
            close_col=close_col,
            high_col=high_col,
            low_col=low_col,
            volume_col=volume_col,
        )


        all_flat = []
        for ev_type, ev_list in ev_dict.items():
            for ev in ev_list:
                all_flat.append(ev)


        if all_flat:
            # Sort by date descending (most recent first)
            all_flat.sort(key=lambda x: pd.to_datetime(x.date), reverse=True)
            latest_ev = all_flat[0]

            candidate_summary["candidate_event_detected"] = latest_ev.event_type
            candidate_summary["event_date"] = str(latest_ev.date)[:10]
            candidate_summary["is_possible_LPS"] = latest_ev.event_type == "LPS"
            candidate_summary["is_possible_SOS"] = latest_ev.event_type == "SOS"
            candidate_summary["is_possible_Spring"] = latest_ev.event_type == "Spring"
            candidate_summary["is_UTAD_warning"] = latest_ev.event_type == "UTAD"
            candidate_summary["numeric_evidence"] = (
                f"Bar vol_ratio={latest_ev.volume_ratio:.2f}x, spread_ratio={latest_ev.spread_ratio:.2f}x, "
                f"close_pos={latest_ev.close_position:.2f}. {latest_ev.supporting_note}"
            )
    except Exception as exc:
        errors.append(f"Schematic detection error: {exc}")

    # 7. TradingView Links & Review Record
    tv_links = generate_tradingview_links(symbol)
    chart_review = ChartReviewRecord(
        symbol=symbol,
        tradingview_daily_url=tv_links.daily_url,
        tradingview_weekly_url=tv_links.weekly_url,
        tradingview_intraday_url=tv_links.intraday_75m_url,
        chart_review_status="pending",
    )

    return BatchScreeningResult(
        symbol=symbol,
        company_name=company_name or symbol,
        as_of_date=as_of_date,
        data_bars=len(wdf),
        data_quality_flags=quality_flags,
        filter_results=filter_results,
        filter_values=filter_values,
        is_mechanically_qualified=is_mechanically_qualified,
        latest_weekly_bar_complete=is_weekly_complete,
        candidate_event_summary=candidate_summary,
        liquidity_metrics=liquidity_metrics,
        tradingview_chart_links=tv_links,
        chart_review_record=chart_review,
        manual_review_pending=True,
        errors=errors,
    )
