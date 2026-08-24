"""Forward return metrics, excursion calculations, and cohort statistical aggregation."""

from typing import Sequence
import numpy as np
import pandas as pd

from wyckoff_screener.research.models import CandidateCategory
from wyckoff_screener.validation.models import CohortSummaryStats


def calculate_forward_metrics_for_bar(
    prices_close: np.ndarray,
    prices_high: np.ndarray,
    prices_low: np.ndarray,
    bar_idx: int,
    horizons: Sequence[int] = (10, 20, 60),
) -> dict[str, float | None]:
    """Calculate forward return percentage, MFE, and MAE for a given bar index across horizons.

    Args:
        prices_close: 1D numpy array of Close prices.
        prices_high: 1D numpy array of High prices.
        prices_low: 1D numpy array of Low prices.
        bar_idx: Index of checkpoint bar T.
        horizons: List of forward horizon bar counts.

    Returns:
        dict: Mapping of fwd_ret_{h}d, mfe_{h}d, mae_{h}d.
    """
    total_bars = len(prices_close)
    base_close = float(prices_close[bar_idx])
    results: dict[str, float | None] = {}

    for h in horizons:
        target_idx = bar_idx + h
        if target_idx < total_bars:
            future_close = float(prices_close[target_idx])
            ret_pct = ((future_close - base_close) / base_close) * 100.0

            # Forward window from bar_idx + 1 through target_idx (inclusive)
            fwd_highs = prices_high[bar_idx + 1 : target_idx + 1]
            fwd_lows = prices_low[bar_idx + 1 : target_idx + 1]

            max_high = float(np.max(fwd_highs))
            min_low = float(np.min(fwd_lows))

            mfe_pct = ((max_high - base_close) / base_close) * 100.0
            mae_pct = ((min_low - base_close) / base_close) * 100.0

            results[f"fwd_ret_{h}d"] = round(ret_pct, 2)
            results[f"mfe_{h}d"] = round(mfe_pct, 2)
            results[f"mae_{h}d"] = round(mae_pct, 2)
        else:
            results[f"fwd_ret_{h}d"] = None
            results[f"mfe_{h}d"] = None
            results[f"mae_{h}d"] = None

    return results


def summarize_series_statistics(
    cohort_group: str,
    cohort_name: str,
    horizon_str: str,
    total_observations: int,
    returns_series: pd.Series,
    mfe_series: pd.Series,
    mae_series: pd.Series,
) -> CohortSummaryStats:
    """Compute summary statistics for a return series."""
    valid_returns = returns_series.dropna()
    valid_mfe = mfe_series.dropna()
    valid_mae = mae_series.dropna()

    valid_count = len(valid_returns)
    if valid_count == 0:
        return CohortSummaryStats(
            cohort_group=cohort_group,
            cohort_name=cohort_name,
            horizon=horizon_str,
            observation_count=total_observations,
            valid_return_count=0,
            win_rate_pct=0.0,
            mean_return_pct=0.0,
            median_return_pct=0.0,
            std_return_pct=0.0,
            p25_return_pct=0.0,
            p75_return_pct=0.0,
            mean_mfe_pct=0.0,
            mean_mae_pct=0.0,
        )

    win_rate = float((valid_returns > 0.0).mean() * 100.0)
    mean_ret = float(valid_returns.mean())
    median_ret = float(valid_returns.median())
    std_ret = float(valid_returns.std()) if valid_count > 1 else 0.0
    p25_ret = float(np.percentile(valid_returns, 25))
    p75_ret = float(np.percentile(valid_returns, 75))

    mean_mfe = float(valid_mfe.mean()) if len(valid_mfe) > 0 else 0.0
    mean_mae = float(valid_mae.mean()) if len(valid_mae) > 0 else 0.0

    return CohortSummaryStats(
        cohort_group=cohort_group,
        cohort_name=cohort_name,
        horizon=horizon_str,
        observation_count=total_observations,
        valid_return_count=valid_count,
        win_rate_pct=round(win_rate, 2),
        mean_return_pct=round(mean_ret, 2),
        median_return_pct=round(median_ret, 2),
        std_return_pct=round(std_ret, 2),
        p25_return_pct=round(p25_ret, 2),
        p75_return_pct=round(p75_ret, 2),
        mean_mfe_pct=round(mean_mfe, 2),
        mean_mae_pct=round(mean_mae, 2),
    )


def compute_cohort_breakdown(
    df: pd.DataFrame,
    mask: pd.Series,
    cohort_group: str,
    cohort_name: str,
    horizons: Sequence[int] = (10, 20, 60),
) -> list[CohortSummaryStats]:
    """Compute statistics for each horizon for a subset matching mask."""
    subset = df[mask]
    total_obs = len(subset)
    stats_list: list[CohortSummaryStats] = []

    for h in horizons:
        ret_col = f"fwd_ret_{h}d"
        mfe_col = f"mfe_{h}d"
        mae_col = f"mae_{h}d"

        rets = subset[ret_col] if ret_col in subset.columns else pd.Series(dtype=float)
        mfes = subset[mfe_col] if mfe_col in subset.columns else pd.Series(dtype=float)
        maes = subset[mae_col] if mae_col in subset.columns else pd.Series(dtype=float)

        st = summarize_series_statistics(
            cohort_group=cohort_group,
            cohort_name=cohort_name,
            horizon_str=f"{h}d",
            total_observations=total_obs,
            returns_series=rets,
            mfe_series=mfes,
            mae_series=maes,
        )
        stats_list.append(st)

    return stats_list


def aggregate_all_cohorts(
    signal_events_df: pd.DataFrame,
    horizons: Sequence[int] = (10, 20, 60),
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Compute complete aggregated performance tables across categories, score tiers, and in-sample vs out-sample splits.

    Returns:
        tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
            (category_performance_df, score_band_performance_df, in_sample_vs_out_sample_df)
    """
    if signal_events_df.empty:
        empty_df = pd.DataFrame(columns=[
            "cohort_group", "cohort_name", "horizon", "observation_count", "valid_return_count",
            "win_rate_pct", "mean_return_pct", "median_return_pct", "std_return_pct",
            "p25_return_pct", "p75_return_pct", "mean_mfe_pct", "mean_mae_pct"
        ])
        return empty_df.copy(), empty_df.copy(), empty_df.copy()

    cat_stats: list[CohortSummaryStats] = []

    # 1. Universe baseline (ALL observations)
    cat_stats.extend(compute_cohort_breakdown(
        signal_events_df,
        pd.Series(True, index=signal_events_df.index),
        cohort_group="universe_baseline",
        cohort_name="ALL_SECURITIES",
        horizons=horizons,
    ))

    # 2. All 5 Candidate Categories
    for cat in CandidateCategory:
        mask = signal_events_df["candidate_category"] == cat.value
        cat_stats.extend(compute_cohort_breakdown(
            signal_events_df,
            mask,
            cohort_group="candidate_category",
            cohort_name=cat.value,
            horizons=horizons,
        ))

    # 3. Mechanical Qualification (True vs False)
    cat_stats.extend(compute_cohort_breakdown(
        signal_events_df,
        signal_events_df["is_mechanically_qualified"] == True,
        cohort_group="mechanical_qualification",
        cohort_name="QUALIFIED_TRUE",
        horizons=horizons,
    ))
    cat_stats.extend(compute_cohort_breakdown(
        signal_events_df,
        signal_events_df["is_mechanically_qualified"] == False,
        cohort_group="mechanical_qualification",
        cohort_name="QUALIFIED_FALSE",
        horizons=horizons,
    ))

    # 4. Disqualification Gate (True vs False)
    cat_stats.extend(compute_cohort_breakdown(
        signal_events_df,
        signal_events_df["is_disqualified"] == True,
        cohort_group="disqualification_gate",
        cohort_name="DISQUALIFIED_TRUE",
        horizons=horizons,
    ))
    cat_stats.extend(compute_cohort_breakdown(
        signal_events_df,
        signal_events_df["is_disqualified"] == False,
        cohort_group="disqualification_gate",
        cohort_name="DISQUALIFIED_FALSE",
        horizons=horizons,
    ))

    category_performance_df = pd.DataFrame([s.to_dict() for s in cat_stats])

    # 5. Score Band Performance
    score_stats: list[CohortSummaryStats] = []
    high_score_mask = signal_events_df["composite_score"] >= 60.0
    mid_score_mask = (signal_events_df["composite_score"] >= 40.0) & (signal_events_df["composite_score"] < 60.0)
    low_score_mask = signal_events_df["composite_score"] < 40.0

    score_stats.extend(compute_cohort_breakdown(
        signal_events_df,
        high_score_mask,
        cohort_group="score_band",
        cohort_name="SCORE_HIGH (>=60.0)",
        horizons=horizons,
    ))
    score_stats.extend(compute_cohort_breakdown(
        signal_events_df,
        mid_score_mask,
        cohort_group="score_band",
        cohort_name="SCORE_MID (40.0-59.9)",
        horizons=horizons,
    ))
    score_stats.extend(compute_cohort_breakdown(
        signal_events_df,
        low_score_mask,
        cohort_group="score_band",
        cohort_name="SCORE_LOW (<40.0)",
        horizons=horizons,
    ))
    score_band_performance_df = pd.DataFrame([s.to_dict() for s in score_stats])

    # 6. In-Sample vs Out-of-Sample Comparative Performance
    split_stats: list[CohortSummaryStats] = []
    in_sample_mask = signal_events_df["period_split"] == "in_sample"
    out_sample_mask = signal_events_df["period_split"] == "out_of_sample"

    # Universe level in-sample vs out-sample
    split_stats.extend(compute_cohort_breakdown(
        signal_events_df,
        in_sample_mask,
        cohort_group="temporal_split_universe",
        cohort_name="IN_SAMPLE_ALL",
        horizons=horizons,
    ))
    split_stats.extend(compute_cohort_breakdown(
        signal_events_df,
        out_sample_mask,
        cohort_group="temporal_split_universe",
        cohort_name="OUT_OF_SAMPLE_ALL",
        horizons=horizons,
    ))

    # Category level in-sample vs out-sample
    for cat in CandidateCategory:
        split_stats.extend(compute_cohort_breakdown(
            signal_events_df,
            in_sample_mask & (signal_events_df["candidate_category"] == cat.value),
            cohort_group="in_sample_by_category",
            cohort_name=f"IN_SAMPLE_{cat.value}",
            horizons=horizons,
        ))
        split_stats.extend(compute_cohort_breakdown(
            signal_events_df,
            out_sample_mask & (signal_events_df["candidate_category"] == cat.value),
            cohort_group="out_of_sample_by_category",
            cohort_name=f"OUT_SAMPLE_{cat.value}",
            horizons=horizons,
        ))

    in_sample_vs_out_sample_df = pd.DataFrame([s.to_dict() for s in split_stats])

    return category_performance_df, score_band_performance_df, in_sample_vs_out_sample_df
