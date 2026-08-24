"""Data models and schemas for Phase 10 Historical Validation & Backtesting."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional
import pandas as pd


SURVIVORSHIP_BIAS_WARNING = (
    "CURRENT-UNIVERSE HISTORICAL VALIDATION (Subject to Survivorship Bias; for forward triage evaluation only)"
)


@dataclass
class HistoricalSignalObservation:
    """Point-in-time signal classification and subsequent forward performance observation."""
    symbol: str
    yfinance_ticker: str
    company_name: str
    checkpoint_date: str
    bar_index: int
    close_at_checkpoint: float
    candidate_category: str
    is_mechanically_qualified: bool
    composite_score: float
    is_disqualified: bool
    disqualifying_flags: str
    most_recent_event: str
    numeric_evidence: str
    pf_target_price: Optional[float]
    pf_upside_pct: Optional[float]
    fwd_ret_10d: Optional[float]
    fwd_ret_20d: Optional[float]
    fwd_ret_60d: Optional[float]
    mfe_10d: Optional[float]
    mfe_20d: Optional[float]
    mfe_60d: Optional[float]
    mae_10d: Optional[float]
    mae_20d: Optional[float]
    mae_60d: Optional[float]
    period_split: str  # "in_sample" vs "out_of_sample"
    tradingview_url_daily: Optional[str] = None
    tradingview_url_weekly: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "symbol": self.symbol,
            "yfinance_ticker": self.yfinance_ticker,
            "company_name": self.company_name,
            "checkpoint_date": self.checkpoint_date,
            "bar_index": self.bar_index,
            "close_at_checkpoint": self.close_at_checkpoint,
            "candidate_category": self.candidate_category,
            "is_mechanically_qualified": self.is_mechanically_qualified,
            "composite_score": self.composite_score,
            "is_disqualified": self.is_disqualified,
            "disqualifying_flags": self.disqualifying_flags,
            "most_recent_event": self.most_recent_event,
            "numeric_evidence": self.numeric_evidence,
            "pf_target_price": self.pf_target_price,
            "pf_upside_pct": self.pf_upside_pct,
            "fwd_ret_10d": self.fwd_ret_10d,
            "fwd_ret_20d": self.fwd_ret_20d,
            "fwd_ret_60d": self.fwd_ret_60d,
            "mfe_10d": self.mfe_10d,
            "mfe_20d": self.mfe_20d,
            "mfe_60d": self.mfe_60d,
            "mae_10d": self.mae_10d,
            "mae_20d": self.mae_20d,
            "mae_60d": self.mae_60d,
            "period_split": self.period_split,
            "tradingview_url_daily": self.tradingview_url_daily,
            "tradingview_url_weekly": self.tradingview_url_weekly,
        }


@dataclass
class ValidationFailureRecord:
    """Isolated error encountered during point-in-time slice evaluation."""
    symbol: str
    checkpoint_date: str
    bar_index: Optional[int]
    exception_type: str
    error_message: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "symbol": self.symbol,
            "checkpoint_date": self.checkpoint_date,
            "bar_index": self.bar_index,
            "exception_type": self.exception_type,
            "error_message": self.error_message,
        }


@dataclass
class CohortSummaryStats:
    """Statistical forward performance metrics for a specific cohort and horizon."""
    cohort_group: str  # e.g. "candidate_category", "mechanical_qualification", "score_band", "universe_baseline"
    cohort_name: str   # e.g. "HIGH_PRIORITY_CANDIDATE", "QUALIFIED", ">= 60", "ALL"
    horizon: str       # e.g. "10d", "20d", "60d"
    observation_count: int
    valid_return_count: int
    win_rate_pct: float
    mean_return_pct: float
    median_return_pct: float
    std_return_pct: float
    p25_return_pct: float
    p75_return_pct: float
    mean_mfe_pct: float
    mean_mae_pct: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "cohort_group": self.cohort_group,
            "cohort_name": self.cohort_name,
            "horizon": self.horizon,
            "observation_count": self.observation_count,
            "valid_return_count": self.valid_return_count,
            "win_rate_pct": self.win_rate_pct,
            "mean_return_pct": self.mean_return_pct,
            "median_return_pct": self.median_return_pct,
            "std_return_pct": self.std_return_pct,
            "p25_return_pct": self.p25_return_pct,
            "p75_return_pct": self.p75_return_pct,
            "mean_mfe_pct": self.mean_mfe_pct,
            "mean_mae_pct": self.mean_mae_pct,
        }


@dataclass
class ValidationManifest:
    """Machine-readable metadata and reconciliation audit manifest for Phase 10."""
    validation_run_id: str
    dataset_snapshot_dir: str
    dataset_date_str: str
    run_timestamp: str
    total_securities_in_dataset: int
    securities_evaluated: int
    total_checkpoints_attempted: int
    total_successful_observations: int
    total_failed_observations: int
    warmup_bars: int
    step_bars: int
    forward_horizons: list[int]
    split_date: str
    in_sample_start: str
    in_sample_end: str
    out_of_sample_start: str
    out_of_sample_end: str
    in_sample_observation_count: int
    out_of_sample_observation_count: int
    category_observation_counts: dict[str, int]
    horizon_valid_observation_counts: dict[str, int]
    survivorship_bias_warning: str
    software_version: str = "1.0.0"

    def to_dict(self) -> dict[str, Any]:
        return {
            "validation_run_id": self.validation_run_id,
            "dataset_snapshot_dir": self.dataset_snapshot_dir,
            "dataset_date_str": self.dataset_date_str,
            "run_timestamp": self.run_timestamp,
            "total_securities_in_dataset": self.total_securities_in_dataset,
            "securities_evaluated": self.securities_evaluated,
            "total_checkpoints_attempted": self.total_checkpoints_attempted,
            "total_successful_observations": self.total_successful_observations,
            "total_failed_observations": self.total_failed_observations,
            "warmup_bars": self.warmup_bars,
            "step_bars": self.step_bars,
            "forward_horizons": self.forward_horizons,
            "split_date": self.split_date,
            "in_sample_start": self.in_sample_start,
            "in_sample_end": self.in_sample_end,
            "out_of_sample_start": self.out_of_sample_start,
            "out_of_sample_end": self.out_of_sample_end,
            "in_sample_observation_count": self.in_sample_observation_count,
            "out_of_sample_observation_count": self.out_of_sample_observation_count,
            "category_observation_counts": self.category_observation_counts,
            "horizon_valid_observation_counts": self.horizon_valid_observation_counts,
            "survivorship_bias_warning": self.survivorship_bias_warning,
            "software_version": self.software_version,
        }


@dataclass
class ValidationRunResult:
    """Complete in-memory output bundle of historical validation run."""
    manifest: ValidationManifest
    signal_events_df: pd.DataFrame
    category_performance_df: pd.DataFrame
    score_band_performance_df: pd.DataFrame
    in_sample_vs_out_sample_df: pd.DataFrame
    failures_df: pd.DataFrame
    output_dir: Path
