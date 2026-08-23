"""TradingView chart URL generator and manual chart-review record structures.

Guiding Principles (AGENTS.md):
- TradingView is a visual review and navigation layer for human confirmation.
- A generated TradingView link is NOT evidence that a symbol, setup, or event is confirmed.
- Numeric calculations strictly use validated application OHLCV data, not TradingView.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
import re
from typing import Any, Final, Optional, Union
from urllib.parse import quote

DEFAULT_EXCHANGE_PREFIX: Final[str] = "NSE"
DEFAULT_TRADINGVIEW_BASE_URL: Final[str] = "https://www.tradingview.com/chart/"

# Documented 9-point manual chart-review checklist
CHART_REVIEW_CHECKLIST: Final[list[str]] = [
    "1. Daily chart with volume (inspect bar-by-bar spread & volume interaction)",
    "2. Weekly chart with volume (confirm larger-timeframe macro trend/base)",
    "3. RSI(14) in 55-70 bullish momentum zone",
    "4. 20-period volume average (compare volume ratio >= 1.5x or < 0.75x)",
    "5. 50 EMA and 100 EMA / SMA alignment",
    "6. ATR / VCP volatility contraction across successive swings",
    "7. Marked support and resistance levels across trading range",
    "8. Schematic candidate: Spring / ST / LPS / SOS / UTAD candidate context",
    "9. Close-position (top/mid/bottom 30%) and effort-vs-result absorption check",
]

VALID_REVIEW_STATUSES: Final[tuple[str, ...]] = ("pending", "reviewed", "rejected")


@dataclass
class TradingViewLinks:
    """TradingView URLs for manual multi-timeframe chart review."""

    symbol: str
    exchange_symbol: str
    daily_url: str
    weekly_url: str
    intraday_75m_url: str
    intraday_note: str
    disclaimer: str = (
        "TradingView link is provided for manual human visual confirmation. "
        "It does NOT replace or modify the application's validated OHLCV quantitative calculations."
    )

    def to_dict(self) -> dict[str, str]:
        return {
            "symbol": self.symbol,
            "exchange_symbol": self.exchange_symbol,
            "daily_url": self.daily_url,
            "weekly_url": self.weekly_url,
            "intraday_75m_url": self.intraday_75m_url,
            "intraday_note": self.intraday_note,
            "disclaimer": self.disclaimer,
        }


@dataclass
class ChartReviewRecord:
    """Structured record of human manual chart inspection."""

    symbol: str
    tradingview_daily_url: str
    tradingview_weekly_url: str
    tradingview_intraday_url: str
    chart_review_status: str = "pending"  # "pending", "reviewed", "rejected"
    reviewer_notes: str = ""
    reviewed_at: Optional[str] = None
    reviewed_timeframes: list[str] = field(default_factory=list)
    confirmed_candidate_events: list[str] = field(default_factory=list)
    rejected_candidate_events: list[str] = field(default_factory=list)
    data_source_used_for_numeric_analysis: str = "Validated local OHLCV dataset"
    warning: str = (
        "TradingView visual review is a manual subjective overlay and is NOT automatically "
        "equivalent to algorithmic OHLCV quantitative computation."
    )

    def __post_init__(self) -> None:
        if self.chart_review_status not in VALID_REVIEW_STATUSES:
            raise ValueError(
                f"Invalid chart_review_status '{self.chart_review_status}'. "
                f"Must be one of {VALID_REVIEW_STATUSES}."
            )

    def mark_reviewed(
        self,
        notes: str,
        timeframes: list[str],
        accepted_events: list[str],
        rejected_events: list[str],
    ) -> None:
        """Update record upon completing human chart inspection."""
        self.chart_review_status = "reviewed"
        self.reviewer_notes = notes
        self.reviewed_timeframes = list(timeframes)
        self.confirmed_candidate_events = list(accepted_events)
        self.rejected_candidate_events = list(rejected_events)
        self.reviewed_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    def mark_rejected(self, reason: str) -> None:
        """Mark setup as manually rejected upon chart inspection."""
        self.chart_review_status = "rejected"
        self.reviewer_notes = reason
        self.reviewed_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    def to_dict(self) -> dict[str, Any]:
        return {
            "symbol": self.symbol,
            "chart_review_status": self.chart_review_status,
            "reviewer_notes": self.reviewer_notes,
            "reviewed_at": self.reviewed_at,
            "reviewed_timeframes": self.reviewed_timeframes,
            "confirmed_candidate_events": self.confirmed_candidate_events,
            "rejected_candidate_events": self.rejected_candidate_events,
            "tradingview_daily_url": self.tradingview_daily_url,
            "tradingview_weekly_url": self.tradingview_weekly_url,
            "tradingview_intraday_url": self.tradingview_intraday_url,
            "data_source_used_for_numeric_analysis": self.data_source_used_for_numeric_analysis,
            "warning": self.warning,
        }


def format_tradingview_symbol(symbol: str, exchange: str = DEFAULT_EXCHANGE_PREFIX) -> str:
    """Format an NSE ticker for TradingView symbol format (e.g. 'ANANTRAJ.NS' -> 'NSE:ANANTRAJ').

    Args:
        symbol: Input symbol (e.g. 'ANANTRAJ.NS', 'APOLLO.NS', 'HINDCOPPER', 'NSE:BEL').
        exchange: Target exchange prefix (default 'NSE').

    Returns:
        Formatted TradingView symbol string (e.g. 'NSE:ANANTRAJ').
    """
    clean = symbol.strip().upper()
    if clean.startswith(f"{exchange}:"):
        clean = clean[len(exchange) + 1 :]
    elif ":" in clean:
        clean = clean.split(":")[-1]

    if clean.endswith(".NS"):
        clean = clean[:-3]

    if not clean:
        raise ValueError(f"Invalid symbol provided for TradingView mapping: '{symbol}'")

    return f"{exchange}:{clean}"


def make_tradingview_symbol_url(
    symbol: str,
    interval: str = "D",
    exchange: str = DEFAULT_EXCHANGE_PREFIX,
    base_url: str = DEFAULT_TRADINGVIEW_BASE_URL,
) -> str:
    """Generate a direct TradingView chart URL for a specific symbol and timeframe interval.

    Args:
        symbol: Symbol string (e.g. 'ANANTRAJ.NS', 'HINDCOPPER.NS').
        interval: Timeframe ('D', '1D', 'W', '1W', '75', '60').
        exchange: Exchange prefix (default 'NSE').
        base_url: TradingView chart base URL.

    Returns:
        Full TradingView chart URL string.
    """
    tv_symbol = format_tradingview_symbol(symbol, exchange=exchange)
    norm_interval = interval.strip().upper()

    # Map intervals to TradingView URL standard interval codes
    if norm_interval in ("D", "1D", "DAILY"):
        iv_param = "D"
    elif norm_interval in ("W", "1W", "WEEKLY"):
        iv_param = "W"
    elif norm_interval in ("75", "75M", "75MIN"):
        iv_param = "75"
    elif norm_interval in ("60", "1H", "60M"):
        iv_param = "60"
    else:
        iv_param = norm_interval

    encoded_sym = quote(tv_symbol, safe="")
    return f"{base_url}?symbol={encoded_sym}&interval={iv_param}"


def generate_tradingview_links(
    symbol: str,
    exchange: str = DEFAULT_EXCHANGE_PREFIX,
) -> TradingViewLinks:
    """Generate full TradingView links bundle for Daily, Weekly, and 75-min charts.

    Args:
        symbol: NSE symbol (e.g. 'ANANTRAJ.NS', 'APOLLO.NS', 'HINDCOPPER.NS').
        exchange: Exchange prefix (default 'NSE').

    Returns:
        TradingViewLinks dataclass containing URLs and manual checklist notes.
    """
    tv_symbol = format_tradingview_symbol(symbol, exchange=exchange)

    daily_url = make_tradingview_symbol_url(symbol, interval="D", exchange=exchange)
    weekly_url = make_tradingview_symbol_url(symbol, interval="W", exchange=exchange)
    intraday_url = make_tradingview_symbol_url(symbol, interval="75", exchange=exchange)

    intraday_note = (
        "Note: TradingView 75-minute interval link opens with interval=75. "
        "If custom intraday intervals require a TradingView paid tier on your account, "
        "select 75m manually on the TradingView timeframe picker."
    )

    return TradingViewLinks(
        symbol=symbol,
        exchange_symbol=tv_symbol,
        daily_url=daily_url,
        weekly_url=weekly_url,
        intraday_75m_url=intraday_url,
        intraday_note=intraday_note,
    )
