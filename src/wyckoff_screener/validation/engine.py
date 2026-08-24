"""Historical walk-forward validation engine for the Wyckoff Research Engine."""

from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
import json
import logging
from pathlib import Path
from typing import Optional, Sequence
import pandas as pd

from wyckoff_screener.data_loader import validate_ohlcv_dataframe
from wyckoff_screener.research.models import CandidateCategory
from wyckoff_screener.research.explanation import generate_candidate_explanation
from wyckoff_screener.scanning.broad_filter import evaluate_broad_setup
from wyckoff_screener.scoring.setup_scorer import score_setup
from wyckoff_screener.charting.tradingview_links import generate_tradingview_links
from wyckoff_screener.validation.models import (
    HistoricalSignalObservation,
    ValidationFailureRecord,
    ValidationManifest,
    ValidationRunResult,
    SURVIVORSHIP_BIAS_WARNING,
)
from wyckoff_screener.validation.metrics import (
    calculate_forward_metrics_for_bar,
    aggregate_all_cohorts,
)

logger = logging.getLogger(__name__)


def evaluate_single_security_history(
    csv_path: Path,
    symbol: str,
    yf_ticker: str,
    company_name: str,
    warmup_bars: int = 200,
    step_bars: int = 5,
    horizons: Sequence[int] = (10, 20, 60),
    split_date: str = "2025-01-01",
    min_avg_turnover_cr: float = 1.0,
    high_priority_score_threshold: float = 60.0,
    qualified_score_threshold: float = 40.0,
    watchlist_score_threshold: float = 30.0,
) -> tuple[list[HistoricalSignalObservation], list[ValidationFailureRecord], int]:
    """Walk forward through historical OHLCV data for a single security and evaluate point-in-time signals.

    Returns:
        tuple: (list_of_observations, list_of_failures, attempted_checkpoints_count)
    """
    observations: list[HistoricalSignalObservation] = []
    failures: list[ValidationFailureRecord] = []

    if not csv_path.exists():
        fail = ValidationFailureRecord(
            symbol=symbol,
            checkpoint_date="N/A",
            bar_index=None,
            exception_type="FileNotFoundError",
            error_message=f"Canonical CSV file not found: {csv_path}",
        )
        return [], [fail], 0

    try:
        raw_df = pd.read_csv(csv_path)
        df = validate_ohlcv_dataframe(raw_df, reject_duplicates=True)
    except Exception as exc:
        fail = ValidationFailureRecord(
            symbol=symbol,
            checkpoint_date="N/A",
            bar_index=None,
            exception_type=type(exc).__name__,
            error_message=f"CSV validation error: {exc}",
        )
        return [], [fail], 0

    # Ensure Date is formatted as YYYY-MM-DD
    df["Date"] = pd.to_datetime(df["Date"]).dt.strftime("%Y-%m-%d")
    total_bars = len(df)

    if total_bars < warmup_bars:
        # Insufficient historical depth to reach warm-up threshold
        return [], [], 0

    max_h = max(horizons)
    # Checkpoint range: start at warmup_bars - 1 (0-indexed), stop at total_bars - max_h (so 60d horizon is available)
    checkpoint_indices = list(range(warmup_bars - 1, total_bars - max_h, step_bars))
    attempted_count = len(checkpoint_indices)

    prices_close = df["Close"].to_numpy()
    prices_high = df["High"].to_numpy()
    prices_low = df["Low"].to_numpy()

    # Pre-generate TradingView review links (isolated human visual layer)
    tv_daily: Optional[str] = None
    tv_weekly: Optional[str] = None
    try:
        tv_bundle = generate_tradingview_links(symbol=yf_ticker)
        tv_daily = tv_bundle.daily_url
        tv_weekly = tv_bundle.weekly_url
    except Exception as tv_exc:
        logger.debug(f"Optional TradingView link generation bypassed for {symbol}: {tv_exc}")

    for t in checkpoint_indices:
        checkpoint_date = str(df["Date"].iloc[t])
        close_at_checkpoint = float(prices_close[t])

        try:
            # 1. Strict Point-in-Time Slice (ZERO future data visibility)
            point_in_time_slice = df.iloc[: t + 1].copy().reset_index(drop=True)

            # 2. Evaluate Frozen Analytical Layers
            broad_res = evaluate_broad_setup(
                point_in_time_slice,
                symbol=yf_ticker,
                min_avg_turnover_cr=min_avg_turnover_cr,
            )

            scored = score_setup(
                point_in_time_slice,
                symbol=yf_ticker,
                peer_rank=None,
            )

            # 3. Categorization Precedence
            is_disqualified = bool(scored.is_disqualified)
            is_mech_qual = bool(broad_res.is_mechanically_qualified)
            comp_score = float(scored.composite_score)
            recent_ev = scored.most_recent_event_type

            has_high_priority_event = recent_ev in ("LPS", "SOS", "Spring")

            if is_disqualified:
                cat = CandidateCategory.DISQUALIFIED.value
            elif is_mech_qual and comp_score >= high_priority_score_threshold and has_high_priority_event:
                cat = CandidateCategory.HIGH_PRIORITY_CANDIDATE.value
            elif is_mech_qual and comp_score >= qualified_score_threshold:
                cat = CandidateCategory.QUALIFIED_CANDIDATE.value
            elif (not is_disqualified) and (
                is_mech_qual
                or (recent_ev is not None)
                or comp_score >= watchlist_score_threshold
            ):
                cat = CandidateCategory.WATCHLIST.value
            else:
                cat = CandidateCategory.NO_SETUP.value

            # Evidence & P&F values
            num_ev = "No active candidate event"
            if scored.most_recent_event_type and scored.detected_events:
                ev_list = scored.detected_events.get(scored.most_recent_event_type, [])
                if ev_list:
                    last_ev = ev_list[-1]
                    num_ev = last_ev.supporting_note if hasattr(last_ev, "supporting_note") else str(last_ev)

            pf_target: Optional[float] = None
            pf_upside: Optional[float] = None
            if scored.pf_price_objective is not None and not scored.pf_price_objective.stale_anchor:
                pf_target = round(float(scored.pf_price_objective.price_objective), 2)
                if close_at_checkpoint > 0:
                    pf_upside = round(((pf_target - close_at_checkpoint) / close_at_checkpoint) * 100.0, 2)

            disq_flags_str = "; ".join(scored.disqualifying_flags) if scored.disqualifying_flags else "None"

            # 4. Forward Return & Excursion Measurement (Separate Outcome Layer)
            fwd_metrics = calculate_forward_metrics_for_bar(
                prices_close=prices_close,
                prices_high=prices_high,
                prices_low=prices_low,
                bar_idx=t,
                horizons=horizons,
            )

            # 5. Train / Test Split
            period_split = "in_sample" if checkpoint_date < split_date else "out_of_sample"

            obs = HistoricalSignalObservation(
                symbol=symbol,
                yfinance_ticker=yf_ticker,
                company_name=company_name,
                checkpoint_date=checkpoint_date,
                bar_index=t,
                close_at_checkpoint=close_at_checkpoint,
                candidate_category=cat,
                is_mechanically_qualified=is_mech_qual,
                composite_score=comp_score,
                is_disqualified=is_disqualified,
                disqualifying_flags=disq_flags_str,
                most_recent_event=recent_ev or "None",
                numeric_evidence=num_ev,
                pf_target_price=pf_target,
                pf_upside_pct=pf_upside,
                fwd_ret_10d=fwd_metrics.get("fwd_ret_10d"),
                fwd_ret_20d=fwd_metrics.get("fwd_ret_20d"),
                fwd_ret_60d=fwd_metrics.get("fwd_ret_60d"),
                mfe_10d=fwd_metrics.get("mfe_10d"),
                mfe_20d=fwd_metrics.get("mfe_20d"),
                mfe_60d=fwd_metrics.get("mfe_60d"),
                mae_10d=fwd_metrics.get("mae_10d"),
                mae_20d=fwd_metrics.get("mae_20d"),
                mae_60d=fwd_metrics.get("mae_60d"),
                period_split=period_split,
                tradingview_url_daily=tv_daily,
                tradingview_url_weekly=tv_weekly,
            )
            observations.append(obs)

        except Exception as checkpoint_exc:
            failures.append(ValidationFailureRecord(
                symbol=symbol,
                checkpoint_date=checkpoint_date,
                bar_index=t,
                exception_type=type(checkpoint_exc).__name__,
                error_message=f"Point-in-time evaluation error at bar {t}: {checkpoint_exc}",
            ))

    return observations, failures, attempted_count


def run_historical_validation(
    dataset_dir: Path,
    output_base_dir: Path = Path("data/validation_results"),
    warmup_bars: int = 200,
    step_bars: int = 5,
    horizons: Sequence[int] = (10, 20, 60),
    split_date: str = "2025-01-01",
    min_avg_turnover_cr: float = 1.0,
    high_priority_score_threshold: float = 60.0,
    qualified_score_threshold: float = 40.0,
    watchlist_score_threshold: float = 30.0,
    max_workers: int = 4,
    custom_date_tag: Optional[str] = None,
) -> ValidationRunResult:
    """Execute historical walk-forward validation across all securities in a Phase 9B research dataset.

    Args:
        dataset_dir: Path to versioned Phase 9B dataset.
        output_base_dir: Base directory for validation results.
        warmup_bars: Minimum historical bars required before evaluating checkpoints (default 200).
        step_bars: Stride between rolling checkpoints (default 5 bars).
        horizons: List of forward horizon bar counts (default 10, 20, 60).
        split_date: Date dividing in-sample from out-of-sample periods (default 2025-01-01).
        min_avg_turnover_cr: Liquidity threshold in INR Crores.
        high_priority_score_threshold: Score threshold for high-priority candidates.
        qualified_score_threshold: Score threshold for qualified candidates.
        watchlist_score_threshold: Score threshold for watchlist candidates.
        max_workers: Maximum worker threads.
        custom_date_tag: Optional custom folder name tag.

    Returns:
        ValidationRunResult: Output bundle containing manifest, signal events, and performance tables.
    """
    dataset_dir = Path(dataset_dir)
    output_base_dir = Path(output_base_dir)

    symbols_file = dataset_dir / "symbols.csv"
    if not symbols_file.exists():
        raise FileNotFoundError(f"Missing symbols.csv in research dataset: {symbols_file}")

    symbols_df = pd.read_csv(symbols_file)
    total_securities_in_dataset = len(symbols_df)

    date_tag = custom_date_tag or datetime.now(timezone.utc).strftime("%Y%m%d")
    output_dir = output_base_dir / date_tag
    output_dir.mkdir(parents=True, exist_ok=True)

    all_observations: list[HistoricalSignalObservation] = []
    all_failures: list[ValidationFailureRecord] = []
    total_checkpoints_attempted = 0
    securities_evaluated = 0

    tasks = []
    for _, row in symbols_df.iterrows():
        sym = str(row["symbol"]).strip()
        yf_t = str(row["yfinance_ticker"]).strip()
        comp = str(row.get("company_name", sym)).strip()
        csv_file = dataset_dir / "data" / f"{yf_t}.csv"
        tasks.append((csv_file, sym, yf_t, comp))

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_sym = {
            executor.submit(
                evaluate_single_security_history,
                csv_path=t[0],
                symbol=t[1],
                yf_ticker=t[2],
                company_name=t[3],
                warmup_bars=warmup_bars,
                step_bars=step_bars,
                horizons=horizons,
                split_date=split_date,
                min_avg_turnover_cr=min_avg_turnover_cr,
                high_priority_score_threshold=high_priority_score_threshold,
                qualified_score_threshold=qualified_score_threshold,
                watchlist_score_threshold=watchlist_score_threshold,
            ): t[1]
            for t in tasks
        }

        for future in as_completed(future_to_sym):
            sym = future_to_sym[future]
            try:
                obs_list, fail_list, attempted = future.result()
                all_observations.extend(obs_list)
                all_failures.extend(fail_list)
                total_checkpoints_attempted += attempted
                securities_evaluated += 1
                print(f"[{securities_evaluated}/{len(tasks)}] Validated {sym} ({len(obs_list)} checkpoints, {len(fail_list)} errors)", flush=True)
            except Exception as task_exc:
                logger.error(f"Unexpected worker failure for {sym}: {task_exc}")
                all_failures.append(ValidationFailureRecord(
                    symbol=sym,
                    checkpoint_date="N/A",
                    bar_index=None,
                    exception_type=type(task_exc).__name__,
                    error_message=str(task_exc),
                ))

    # Convert observations to DataFrame and sort deterministically
    if all_observations:
        signal_events_df = pd.DataFrame([obs.to_dict() for obs in all_observations])
        signal_events_df = signal_events_df.sort_values(
            by=["checkpoint_date", "symbol"]
        ).reset_index(drop=True)
    else:
        signal_events_df = pd.DataFrame(columns=[
            "symbol", "yfinance_ticker", "company_name", "checkpoint_date", "bar_index",
            "close_at_checkpoint", "candidate_category", "is_mechanically_qualified",
            "composite_score", "is_disqualified", "disqualifying_flags", "most_recent_event",
            "numeric_evidence", "pf_target_price", "pf_upside_pct", "fwd_ret_10d", "fwd_ret_20d",
            "fwd_ret_60d", "mfe_10d", "mfe_20d", "mfe_60d", "mae_10d", "mae_20d", "mae_60d",
            "period_split", "tradingview_url_daily", "tradingview_url_weekly"
        ])

    failures_df = pd.DataFrame([f.to_dict() for f in all_failures]) if all_failures else pd.DataFrame(
        columns=["symbol", "checkpoint_date", "bar_index", "exception_type", "error_message"]
    )

    # Aggregate performance tables
    cat_perf_df, score_perf_df, split_perf_df = aggregate_all_cohorts(
        signal_events_df=signal_events_df,
        horizons=horizons,
    )

    # Compute manifest reconciliation counts
    total_success = len(signal_events_df)
    total_failed = len(all_failures)

    category_counts: dict[str, int] = {}
    for cat in CandidateCategory:
        category_counts[cat.value] = int((signal_events_df["candidate_category"] == cat.value).sum()) if not signal_events_df.empty else 0

    horizon_valid_counts: dict[str, int] = {}
    for h in horizons:
        col = f"fwd_ret_{h}d"
        horizon_valid_counts[f"{h}d"] = int(signal_events_df[col].notna().sum()) if col in signal_events_df.columns else 0

    in_sample_count = int((signal_events_df["period_split"] == "in_sample").sum()) if not signal_events_df.empty else 0
    out_sample_count = int((signal_events_df["period_split"] == "out_of_sample").sum()) if not signal_events_df.empty else 0

    # Determine date spans
    in_dates = signal_events_df.loc[signal_events_df["period_split"] == "in_sample", "checkpoint_date"] if not signal_events_df.empty else pd.Series()
    out_dates = signal_events_df.loc[signal_events_df["period_split"] == "out_of_sample", "checkpoint_date"] if not signal_events_df.empty else pd.Series()

    in_start = str(in_dates.min()) if not in_dates.empty else "N/A"
    in_end = str(in_dates.max()) if not in_dates.empty else "N/A"
    out_start = str(out_dates.min()) if not out_dates.empty else "N/A"
    out_end = str(out_dates.max()) if not out_dates.empty else "N/A"

    manifest = ValidationManifest(
        validation_run_id=f"val_{date_tag}",
        dataset_snapshot_dir=str(dataset_dir),
        dataset_date_str=date_tag,
        run_timestamp=datetime.now(timezone.utc).isoformat(),
        total_securities_in_dataset=total_securities_in_dataset,
        securities_evaluated=securities_evaluated,
        total_checkpoints_attempted=total_checkpoints_attempted,
        total_successful_observations=total_success,
        total_failed_observations=total_failed,
        warmup_bars=warmup_bars,
        step_bars=step_bars,
        forward_horizons=list(horizons),
        split_date=split_date,
        in_sample_start=in_start,
        in_sample_end=in_end,
        out_of_sample_start=out_start,
        out_of_sample_end=out_end,
        in_sample_observation_count=in_sample_count,
        out_of_sample_observation_count=out_sample_count,
        category_observation_counts=category_counts,
        horizon_valid_observation_counts=horizon_valid_counts,
        survivorship_bias_warning=SURVIVORSHIP_BIAS_WARNING,
        software_version="1.0.0",
    )

    # Save output artifacts to disk
    manifest_path = output_dir / "validation_manifest.json"
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest.to_dict(), f, indent=2)

    signal_events_df.to_csv(output_dir / "signal_events.csv", index=False)
    cat_perf_df.to_csv(output_dir / "category_performance.csv", index=False)
    score_perf_df.to_csv(output_dir / "score_band_performance.csv", index=False)
    split_perf_df.to_csv(output_dir / "in_sample_vs_out_sample.csv", index=False)
    failures_df.to_csv(output_dir / "failures.csv", index=False)

    return ValidationRunResult(
        manifest=manifest,
        signal_events_df=signal_events_df,
        category_performance_df=cat_perf_df,
        score_band_performance_df=score_perf_df,
        in_sample_vs_out_sample_df=split_perf_df,
        failures_df=failures_df,
        output_dir=output_dir,
    )
