"""Phase 10: Historical Validation & Backtesting package."""

from wyckoff_screener.validation.models import (
    HistoricalSignalObservation,
    ValidationFailureRecord,
    CohortSummaryStats,
    ValidationManifest,
    ValidationRunResult,
    SURVIVORSHIP_BIAS_WARNING,
)
from wyckoff_screener.validation.engine import (
    evaluate_single_security_history,
    run_historical_validation,
)
from wyckoff_screener.validation.metrics import (
    calculate_forward_metrics_for_bar,
    aggregate_all_cohorts,
)

__all__ = [
    "HistoricalSignalObservation",
    "ValidationFailureRecord",
    "CohortSummaryStats",
    "ValidationManifest",
    "ValidationRunResult",
    "SURVIVORSHIP_BIAS_WARNING",
    "evaluate_single_security_history",
    "run_historical_validation",
    "calculate_forward_metrics_for_bar",
    "aggregate_all_cohorts",
]
