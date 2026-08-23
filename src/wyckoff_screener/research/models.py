"""Data models and type definitions for Phase 9C Research Screening Engine."""

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, Final, Optional


class CandidateCategory(str, Enum):
    """Mutually exclusive research workflow categorization for screened securities."""

    DISQUALIFIED = "DISQUALIFIED"
    HIGH_PRIORITY_CANDIDATE = "HIGH_PRIORITY_CANDIDATE"
    QUALIFIED_CANDIDATE = "QUALIFIED_CANDIDATE"
    WATCHLIST = "WATCHLIST"
    NO_SETUP = "NO_SETUP"


@dataclass(frozen=True)
class ResearchCandidateResult:
    """Complete quantitative research evaluation outcome for a single security."""

    # 1. Identifier & Provenance
    symbol: str
    yfinance_ticker: str
    company_name: str
    as_of_date: str
    data_bars: int
    dataset_snapshot_path: str
    dataset_date: str

    # 2. Research Triage & Categorization
    candidate_category: str  # Member of CandidateCategory
    is_research_eligible: bool  # True (inherited from Phase 9A/9B)
    is_mechanically_qualified: bool  # Compound 3-gate rule outcome
    is_disqualified: bool  # Structural red flags present
    disqualifying_flags: list[str]  # Specific red flag reasons

    # 3. Setup Scoring Breakdown
    composite_score: float  # 0.0 - 100.0
    score_breakdown: dict[str, float]  # mechanical_filters, recent_event, peer_rank, pf_upside
    peer_analysis_skipped: bool  # True when peer comparisons not supplied

    # 4. Mechanical Filter Sub-Results
    filter_flags: dict[str, bool]  # weekly_uptrend, dma_50_above_100, rsi_in_band, atr_contracting, etc.
    filter_values: dict[str, Any]  # close, rsi_14, dma_50, dma_100, wma_30, wma_40, etc.

    # 5. VSA Observations (Latest Bar)
    vsa_volume_ratio: float
    vsa_spread_ratio: float
    vsa_close_position: float
    is_stopping_volume: bool
    is_no_demand: bool
    is_no_supply: bool
    is_effort_vs_result: bool

    # 6. Wyckoff Schematic Events
    most_recent_event_type: Optional[str]
    most_recent_event_date: Optional[str]
    possible_LPS: bool
    possible_SOS: bool
    possible_Spring: bool
    is_UTAD_warning: bool
    total_events_detected: int
    numeric_evidence: str

    # 7. Point & Figure Objectives
    pf_target_price: Optional[float]
    pf_upside_pct: Optional[float]
    pf_count_columns: Optional[int]
    pf_is_stale_anchor: bool

    # 8. Evidence-First Explanation Narrative
    explanation_summary: str

    # 9. Optional Visual Review Layer
    tradingview_daily_url: str
    tradingview_weekly_url: str
    tradingview_75m_url: str
    chart_review_status: str = "pending"
    screening_errors: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert candidate result to flat dictionary for tabular export."""
        return {
            "symbol": self.symbol,
            "yfinance_ticker": self.yfinance_ticker,
            "company_name": self.company_name,
            "as_of_date": self.as_of_date,
            "data_bars": self.data_bars,
            "candidate_category": self.candidate_category,
            "is_research_eligible": self.is_research_eligible,
            "is_mechanically_qualified": self.is_mechanically_qualified,
            "composite_score": round(self.composite_score, 1),
            "is_disqualified": self.is_disqualified,
            "disqualifying_flags": "; ".join(self.disqualifying_flags) if self.disqualifying_flags else "None",
            "weekly_uptrend": self.filter_flags.get("weekly_uptrend", False),
            "dma_50_above_100": self.filter_flags.get("dma_50_above_100", False),
            "rsi_in_band": self.filter_flags.get("rsi_in_band", False),
            "atr_contracting": self.filter_flags.get("atr_contracting", False),
            "vcp_bbw_contracting": self.filter_flags.get("vcp_bbw_contracting", False),
            "min_liquidity_passed": self.filter_flags.get("min_liquidity_passed", False),
            "close": self.filter_values.get("close"),
            "rsi_14": self.filter_values.get("rsi_14"),
            "dma_50": self.filter_values.get("dma_50"),
            "dma_100": self.filter_values.get("dma_100"),
            "wma_30": self.filter_values.get("wma_30"),
            "wma_40": self.filter_values.get("wma_40"),
            "atr_contraction_ratio": self.filter_values.get("atr_contraction_ratio"),
            "bb_width_20": self.filter_values.get("bb_width_20"),
            "avg_20_turnover_cr": self.filter_values.get("avg_daily_turnover_cr"),
            "vsa_volume_ratio": round(self.vsa_volume_ratio, 2),
            "vsa_spread_ratio": round(self.vsa_spread_ratio, 2),
            "vsa_close_position": round(self.vsa_close_position, 2),
            "is_stopping_volume": self.is_stopping_volume,
            "is_no_demand": self.is_no_demand,
            "is_no_supply": self.is_no_supply,
            "is_effort_vs_result": self.is_effort_vs_result,
            "most_recent_event_type": self.most_recent_event_type or "None",
            "most_recent_event_date": self.most_recent_event_date or "None",
            "possible_LPS": self.possible_LPS,
            "possible_SOS": self.possible_SOS,
            "possible_Spring": self.possible_Spring,
            "is_UTAD_warning": self.is_UTAD_warning,
            "total_events_detected": self.total_events_detected,
            "numeric_evidence": self.numeric_evidence,
            "pf_target_price": round(self.pf_target_price, 2) if self.pf_target_price is not None else None,
            "pf_upside_pct": round(self.pf_upside_pct, 1) if self.pf_upside_pct is not None else None,
            "pf_count_columns": self.pf_count_columns,
            "pf_is_stale_anchor": self.pf_is_stale_anchor,
            "explanation_summary": self.explanation_summary,
            "tradingview_daily_url": self.tradingview_daily_url,
            "tradingview_weekly_url": self.tradingview_weekly_url,
            "tradingview_75m_url": self.tradingview_75m_url,
            "chart_review_status": self.chart_review_status,
            "dataset_snapshot_path": self.dataset_snapshot_path,
            "dataset_date": self.dataset_date,
        }


@dataclass
class ResearchScreeningManifest:
    """Complete machine-readable audit manifest for a research screening execution."""

    screening_run_id: str
    dataset_snapshot_path: str
    dataset_date: str
    generated_at_utc: str
    schema_version: str = "1.0"
    total_input_securities: int = 0
    attempted_evaluations: int = 0
    successful_evaluations: int = 0
    failed_evaluations: int = 0
    high_priority_candidates_count: int = 0
    qualified_candidates_count: int = 0
    watchlist_candidates_count: int = 0
    no_setup_count: int = 0
    disqualified_count: int = 0
    mechanically_qualified_count: int = 0
    tradingview_link_failures_count: int = 0
    screening_policy: dict[str, Any] = field(default_factory=dict)
    disclaimer: str = (
        "RESEARCH TRIAGE NOTICE: All candidate classifications and scores are mathematical research "
        "triage aids for human visual chart review on TradingView. Not investment advice or trade signals."
    )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ResearchScreeningResult:
    """Container for the output of a research screening execution."""

    manifest: ResearchScreeningManifest
    all_results_df: Any  # pd.DataFrame
    candidates_df: Any  # pd.DataFrame
    disqualified_df: Any  # pd.DataFrame
    failures_df: Any  # pd.DataFrame
    results_dir: Any  # Path
