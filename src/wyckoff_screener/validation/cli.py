"""Command Line Interface for Phase 10 Historical Validation & Backtesting."""

import argparse
from pathlib import Path
import sys

from wyckoff_screener.validation.engine import run_historical_validation


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Wyckoff Stock Screener - Phase 10 Historical Validation & Backtesting Engine",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--dataset-dir",
        type=Path,
        required=True,
        help="Path to Phase 9B research dataset directory (e.g. data/research_datasets/20260823_31_AUDIT)",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("data/validation_results"),
        help="Base output directory for historical validation results",
    )
    parser.add_argument(
        "--warmup-bars",
        type=int,
        default=200,
        help="Minimum historical bars required before evaluating checkpoints",
    )
    parser.add_argument(
        "--step",
        type=int,
        default=5,
        help="Stride between rolling checkpoints in bars (e.g. 5 for weekly Friday cadence)",
    )
    parser.add_argument(
        "--horizons",
        type=str,
        default="10,20,60",
        help="Comma-separated forward horizon periods in bars",
    )
    parser.add_argument(
        "--split-date",
        type=str,
        default="2025-01-01",
        help="Date (YYYY-MM-DD) dividing in-sample from out-of-sample periods",
    )
    parser.add_argument(
        "--min-turnover-cr",
        type=float,
        default=1.0,
        help="Minimum average daily turnover in INR Crores for liquidity qualification",
    )
    parser.add_argument(
        "--high-priority-threshold",
        type=float,
        default=60.0,
        help="Score threshold for High Priority Candidate tier",
    )
    parser.add_argument(
        "--qualified-threshold",
        type=float,
        default=40.0,
        help="Score threshold for Qualified Candidate tier",
    )
    parser.add_argument(
        "--watchlist-threshold",
        type=float,
        default=30.0,
        help="Score threshold for Watchlist tier",
    )
    parser.add_argument(
        "--max-workers",
        type=int,
        default=4,
        help="Maximum worker threads for parallel security evaluation",
    )
    parser.add_argument(
        "--date-tag",
        type=str,
        default=None,
        help="Custom subfolder name under output-dir",
    )

    args = parser.parse_args()

    horizons_list = [int(h.strip()) for h in args.horizons.split(",") if h.strip()]

    print("=" * 90)
    print("WYCKOFF & VSA HISTORICAL VALIDATION & BACKTESTING ENGINE (PHASE 10)")
    print(f"Target Dataset:  {args.dataset_dir}")
    print(f"Output Base:     {args.output_dir}")
    print(f"Warm-up Bars:    {args.warmup_bars} bars (~10 months)")
    print(f"Checkpoint Step: {args.step} bars (weekly)")
    print(f"Horizons:        {horizons_list} bars")
    print(f"Split Date:      {args.split_date} (In-Sample < Split <= Out-of-Sample)")
    print("=" * 90)

    try:
        res = run_historical_validation(
            dataset_dir=args.dataset_dir,
            output_base_dir=args.output_dir,
            warmup_bars=args.warmup_bars,
            step_bars=args.step,
            horizons=horizons_list,
            split_date=args.split_date,
            min_avg_turnover_cr=args.min_turnover_cr,
            high_priority_score_threshold=args.high_priority_threshold,
            qualified_score_threshold=args.qualified_threshold,
            watchlist_score_threshold=args.watchlist_threshold,
            max_workers=args.max_workers,
            custom_date_tag=args.date_tag,
        )
    except Exception as exc:
        print(f"\n[FATAL ERROR] Historical validation run failed: {exc}", file=sys.stderr)
        sys.exit(1)

    m = res.manifest
    print("\n" + "=" * 90)
    print("HISTORICAL VALIDATION COMPLETED")
    print("=" * 90)
    print(f"Results Directory:               {res.output_dir}")
    print(f"Securities in Dataset:           {m.total_securities_in_dataset}")
    print(f"Securities Evaluated:            {m.securities_evaluated}")
    print(f"Total Checkpoints Attempted:     {m.total_checkpoints_attempted}")
    print(f"Successful Observations:         {m.total_successful_observations}")
    print(f"Failed Observations:             {m.total_failed_observations}")
    print("-" * 50)
    print("CANDIDATE CATEGORY BREAKDOWN:")
    for cat_name, count in m.category_observation_counts.items():
        print(f"  {cat_name:<30}: {count:>5}")
    print("-" * 50)
    print("TEMPORAL SPLIT OBSERVATIONS:")
    print(f"  In-Sample ({m.in_sample_start} to {m.in_sample_end}):      {m.in_sample_observation_count:>5}")
    print(f"  Out-of-Sample ({m.out_of_sample_start} to {m.out_of_sample_end}):  {m.out_of_sample_observation_count:>5}")
    print("-" * 50)
    print("VALID FORWARD OUTCOMES BY HORIZON:")
    for h_name, v_count in m.horizon_valid_observation_counts.items():
        print(f"  Horizon {h_name:<10}: {v_count:>5} / {m.total_successful_observations}")
    print("-" * 50)
    print(f"Survivorship Bias Notice: {m.survivorship_bias_warning}")
    print("=" * 90)


if __name__ == "__main__":
    main()
