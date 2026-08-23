"""Command-line interface for Phase 9C Broad NSE EQ Research Screening Engine."""

import argparse
from pathlib import Path
import sys

from wyckoff_screener.research.screening_engine import (
    DEFAULT_HIGH_PRIORITY_THRESHOLD,
    DEFAULT_QUALIFIED_THRESHOLD,
    DEFAULT_RESULTS_BASE_DIR,
    DEFAULT_WATCHLIST_THRESHOLD,
    run_research_screening,
)
from wyckoff_screener.scanning.broad_filter import DEFAULT_MIN_AVG_TURNOVER_CR


def main() -> None:
    """CLI entrypoint for standalone broad research screening."""
    parser = argparse.ArgumentParser(
        description="Wyckoff & VSA Broad NSE EQ Research Screening Engine (Phase 9C)"
    )
    parser.add_argument(
        "--dataset-dir",
        type=str,
        default=None,
        help="Path to Phase 9B research dataset directory (e.g. 'data/research_datasets/20260823').",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=DEFAULT_RESULTS_BASE_DIR,
        help=f"Base directory for storing research screening results (default '{DEFAULT_RESULTS_BASE_DIR}').",
    )
    parser.add_argument(
        "--min-turnover-cr",
        type=float,
        default=DEFAULT_MIN_AVG_TURNOVER_CR,
        help=f"Minimum 20-day average daily turnover in INR Crores for liquidity gate (default {DEFAULT_MIN_AVG_TURNOVER_CR}).",
    )
    parser.add_argument(
        "--high-priority-threshold",
        type=float,
        default=DEFAULT_HIGH_PRIORITY_THRESHOLD,
        help=f"Score threshold for HIGH_PRIORITY_CANDIDATE (default {DEFAULT_HIGH_PRIORITY_THRESHOLD}).",
    )
    parser.add_argument(
        "--qualified-threshold",
        type=float,
        default=DEFAULT_QUALIFIED_THRESHOLD,
        help=f"Score threshold for QUALIFIED_CANDIDATE (default {DEFAULT_QUALIFIED_THRESHOLD}).",
    )
    parser.add_argument(
        "--watchlist-threshold",
        type=float,
        default=DEFAULT_WATCHLIST_THRESHOLD,
        help=f"Score threshold for WATCHLIST (default {DEFAULT_WATCHLIST_THRESHOLD}).",
    )

    args = parser.parse_args()

    # Determine dataset directory
    target_ds_dir: Path
    if args.dataset_dir:
        target_ds_dir = Path(args.dataset_dir)
    else:
        # Locate latest dataset in data/research_datasets
        base_ds = Path("data/research_datasets")
        if base_ds.exists():
            subdirs = sorted([d for d in base_ds.iterdir() if d.is_dir() and (d / "symbols.csv").exists()])
            if subdirs:
                target_ds_dir = subdirs[-1]
            else:
                print("ERROR: No valid Phase 9B research datasets found in data/research_datasets.", file=sys.stderr)
                sys.exit(1)
        else:
            print("ERROR: data/research_datasets does not exist. Build a dataset first.", file=sys.stderr)
            sys.exit(1)

    print("=" * 90)
    print("WYCKOFF & VSA RESEARCH SCREENING ENGINE (PHASE 9C)")
    print(f"Target Dataset: {target_ds_dir}")
    print(f"Output Base:    {args.output_dir}")
    print("=" * 90)

    try:
        res = run_research_screening(
            dataset_dir=target_ds_dir,
            output_base_dir=args.output_dir,
            min_avg_turnover_cr=args.min_turnover_cr,
            high_priority_score_threshold=args.high_priority_threshold,
            qualified_score_threshold=args.qualified_threshold,
            watchlist_score_threshold=args.watchlist_threshold,
        )
    except Exception as exc:
        print(f"ERROR: Research screening execution failed: {exc}", file=sys.stderr)
        sys.exit(1)

    m = res.manifest
    print("\n" + "=" * 90)
    print("RESEARCH SCREENING COMPLETED")
    print("=" * 90)
    print(f"Results Directory:         {res.results_dir}")
    print(f"Total Input Securities:    {m.total_input_securities}")
    print(f"Successful Evaluations:    {m.successful_evaluations}")
    print(f"Failed Evaluations:        {m.failed_evaluations}")
    print("-" * 50)
    print("CANDIDATE CATEGORY BREAKDOWN:")
    print(f"  [1] HIGH_PRIORITY_CANDIDATE: {m.high_priority_candidates_count}")
    print(f"  [2] QUALIFIED_CANDIDATE:     {m.qualified_candidates_count}")
    print(f"  [3] WATCHLIST:               {m.watchlist_candidates_count}")
    print(f"  [4] NO_SETUP:                {m.no_setup_count}")
    print(f"  [5] DISQUALIFIED:            {m.disqualified_count}")
    print("-" * 50)
    print(f"Mechanically Qualified:    {m.mechanically_qualified_count} / {m.successful_evaluations}")
    print(f"TradingView Link Failures: {m.tradingview_link_failures_count}")
    print("=" * 90)


if __name__ == "__main__":
    main()
