"""Universe security models, exclusion taxonomy, and audit report structures.

Guiding Principles:
- Strict separation between Universe Eligibility, Research Eligibility, and Setup Qualification.
- Every excluded security has an unambiguous, machine-readable primary exclusion reason.
- Deterministic, auditable eligibility calculations.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Final, Optional


class ExclusionReason(str, Enum):
    """Machine-readable taxonomy of security exclusion reasons."""

    INVALID_SYMBOL = "INVALID_SYMBOL"
    NON_EQ_SERIES = "NON_EQ_SERIES"
    DUPLICATE_SYMBOL = "DUPLICATE_SYMBOL"
    MISSING_REQUIRED_FIELDS = "MISSING_REQUIRED_FIELDS"
    DATA_DOWNLOAD_FAILED = "DATA_DOWNLOAD_FAILED"
    EMPTY_DATA = "EMPTY_DATA"
    MISSING_REQUIRED_COLUMNS = "MISSING_REQUIRED_COLUMNS"
    INSUFFICIENT_HISTORY = "INSUFFICIENT_HISTORY"
    DATA_QUALITY_FAILURE = "DATA_QUALITY_FAILURE"
    LIQUIDITY_FAILURE = "LIQUIDITY_FAILURE"


@dataclass
class UniverseSecurityRecord:
    """Represents the complete eligibility lifecycle of a security in the research universe."""

    symbol: str
    company_name: str
    series: str
    exchange: str
    yfinance_ticker: str
    source_date: str
    universe_source: str
    is_valid_symbol: bool = True
    is_eligible_series: bool = True
    is_duplicate: bool = False
    has_data_available: bool = False
    has_sufficient_history: bool = False
    has_acceptable_data_quality: bool = False
    passes_liquidity: bool = False
    is_research_eligible: bool = False
    primary_exclusion_reason: Optional[str] = None
    exclusion_details: list[str] = field(default_factory=list)
    data_bars_count: int = 0
    avg_20_daily_turnover_cr: Optional[float] = None
    zero_volume_pct: Optional[float] = None

    def evaluate_research_eligibility(self) -> bool:
        """Compute research eligibility using the exact deterministic compound rule.

        Rule:
            is_research_eligible = (
                is_valid_symbol
                AND is_eligible_series
                AND NOT is_duplicate
                AND has_data_available
                AND has_sufficient_history
                AND has_acceptable_data_quality
                AND passes_liquidity
            )

        Note:
            is_mechanically_qualified (Wyckoff setup / trend / momentum) is strictly EXCLUDED
            from research eligibility. A security can be research-eligible without having any
            current setup.
        """
        eligible = bool(
            self.is_valid_symbol
            and self.is_eligible_series
            and (not self.is_duplicate)
            and self.has_data_available
            and self.has_sufficient_history
            and self.has_acceptable_data_quality
            and self.passes_liquidity
        )
        self.is_research_eligible = eligible
        if eligible:
            self.primary_exclusion_reason = None
        return eligible

    def to_dict(self) -> dict[str, Any]:
        """Convert record to dictionary for CSV / JSON serialization."""
        return {
            "symbol": self.symbol,
            "company_name": self.company_name,
            "series": self.series,
            "exchange": self.exchange,
            "yfinance_ticker": self.yfinance_ticker,
            "source_date": self.source_date,
            "universe_source": self.universe_source,
            "is_valid_symbol": self.is_valid_symbol,
            "is_eligible_series": self.is_eligible_series,
            "is_duplicate": self.is_duplicate,
            "has_data_available": self.has_data_available,
            "has_sufficient_history": self.has_sufficient_history,
            "has_acceptable_data_quality": self.has_acceptable_data_quality,
            "passes_liquidity": self.passes_liquidity,
            "is_research_eligible": self.is_research_eligible,
            "primary_exclusion_reason": self.primary_exclusion_reason or "",
            "exclusion_details": "; ".join(self.exclusion_details) if self.exclusion_details else "",
            "data_bars_count": self.data_bars_count,
            "avg_20_daily_turnover_cr": self.avg_20_daily_turnover_cr,
            "zero_volume_pct": self.zero_volume_pct,
        }


@dataclass
class UniverseBuildReport:
    """Comprehensive machine-readable audit report for a universe build."""

    source_name: str
    source_date: str
    snapshot_dir: str
    total_source_records: int
    valid_symbol_count: int
    eq_series_count: int
    rejected_non_eq_count: int
    duplicate_count: int
    missing_fields_count: int
    data_fetch_attempted: int
    data_success_count: int
    data_failure_count: int
    insufficient_history_count: int
    data_quality_failure_count: int
    liquidity_failure_count: int
    final_research_eligible_count: int
    final_excluded_count: int
    rejections_by_reason: dict[str, int] = field(default_factory=dict)
    survivorship_bias_notice: str = (
        "SURVIVORSHIP BIAS NOTICE: This snapshot reflects currently available/surviving securities "
        "at the time of creation. It is valid for forward monitoring and research screening, but does NOT "
        "represent a historical point-in-time constituent list for bias-free backtesting."
    )
    built_at_utc: str = field(
        default_factory=lambda: datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_name": self.source_name,
            "source_date": self.source_date,
            "snapshot_dir": self.snapshot_dir,
            "built_at_utc": self.built_at_utc,
            "total_source_records": self.total_source_records,
            "valid_symbol_count": self.valid_symbol_count,
            "eq_series_count": self.eq_series_count,
            "rejected_non_eq_count": self.rejected_non_eq_count,
            "duplicate_count": self.duplicate_count,
            "missing_fields_count": self.missing_fields_count,
            "data_fetch_attempted": self.data_fetch_attempted,
            "data_success_count": self.data_success_count,
            "data_failure_count": self.data_failure_count,
            "insufficient_history_count": self.insufficient_history_count,
            "data_quality_failure_count": self.data_quality_failure_count,
            "liquidity_failure_count": self.liquidity_failure_count,
            "final_research_eligible_count": self.final_research_eligible_count,
            "final_excluded_count": self.final_excluded_count,
            "rejections_by_reason": self.rejections_by_reason,
            "survivorship_bias_notice": self.survivorship_bias_notice,
        }
