"""Backtest validation and forward return analysis package."""

from wyckoff_screener.backtest.forward_return_analysis import (
    compute_forward_returns,
    summarize_forward_returns,
)
from wyckoff_screener.backtest.historical_scorer import run_rolling_score
from wyckoff_screener.backtest.signal_generator import (
    determine_historical_signal_dates,
    evaluate_point_in_time_signal,
    export_backtest_dataset,
    generate_backtest_dataset,
)

__all__ = [
    "run_rolling_score",
    "compute_forward_returns",
    "summarize_forward_returns",
    "evaluate_point_in_time_signal",
    "determine_historical_signal_dates",
    "generate_backtest_dataset",
    "export_backtest_dataset",
]

