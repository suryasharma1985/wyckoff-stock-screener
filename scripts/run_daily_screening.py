"""Production Daily Research Screening Runner.

Orchestrates the complete NSE equity research screening pipeline:
1. Builds official NSE universe snapshot (or loads fallback).
2. Materializes the canonical research dataset with data caching.
3. Executes the Phase 9C Research Screening Engine.
4. Validates output manifest integrity and candidate counts.
5. Emits detailed structured summary for CI/CD logging.

Usage:
    python scripts/run_daily_screening.py --universe-source nse_eq
"""

from __future__ import annotations
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import sys
import pandas as pd

# Add repo root to sys.path
_repo_root = Path(__file__).resolve().parent.parent
if str(_repo_root) not in sys.path:
    sys.path.insert(0, str(_repo_root))
if str(_repo_root / "src") not in sys.path:
    sys.path.insert(0, str(_repo_root / "src"))

from wyckoff_screener.data.dataset_builder import build_research_dataset
from wyckoff_screener.research.screening_engine import run_research_screening
from wyckoff_screener.universe.builder import build_research_universe
from wyckoff_screener.universe.nse_symbols import DEFAULT_ELIGIBLE_SERIES


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Daily NSE Equity Wyckoff & VSA Research Screener Runner"
    )
    parser.add_argument(
        "--universe-source",
        type=str,
        default="nse_eq",
        help="Universe source: 'nse_eq' (live official NSE archive), 'sample', or 'custom_csv' (default 'nse_eq').",
    )
    parser.add_argument(
        "--date-tag",
        type=str,
        default=None,
        help="Custom YYYYMMDD date tag (defaults to current UTC/IST date).",
    )
    parser.add_argument(
        "--min-turnover-cr",
        type=float,
        default=1.0,
        help="Minimum 20-day average daily turnover in INR Crores (default 1.0).",
    )
    parser.add_argument(
        "--max-failure-rate-pct",
        type=float,
        default=30.0,
        help="Maximum allowable symbol evaluation failure percentage before triggering error (default 30.0%%).",
    )
    parser.add_argument(
        "--start-date",
        type=str,
        default="2023-01-01",
        help="Start date for historical OHLCV data lookback (default '2023-01-01').",
    )
    parser.add_argument(
        "--force-refresh",
        action="store_true",
        help="Force re-downloading market data even if cache exists.",
    )
    parser.add_argument(
        "--max-workers",
        type=int,
        default=4,
        help="Thread worker pool limit for concurrent screening (default 4).",
    )

    args = parser.parse_args()

    date_tag = args.date_tag or datetime.now(timezone.utc).strftime("%Y%m%d")

    print("=" * 90)
    print("WYCKOFF & VSA AUTOMATED DAILY RESEARCH SCREENER")
    print(f"Execution Date Tag: {date_tag}")
    print(f"Universe Source:    {args.universe_source}")
    print(f"Min Turnover Gate:  INR {args.min_turnover_cr} Cr")
    print("=" * 90)

    # -------------------------------------------------------------
    # Step 1: Ingest & Build Universe Snapshot
    # -------------------------------------------------------------
    print("\n[STEP 1/3] Building NSE Research Universe Snapshot...")
    try:
        uni_res = build_research_universe(
            source=args.universe_source,
            output_base_dir="data/universe_snapshots",
            custom_date_tag=date_tag,
            eligible_series=DEFAULT_ELIGIBLE_SERIES,
            min_avg_turnover_cr=args.min_turnover_cr,
            evaluate_data_layer=False,
        )
        rep = uni_res.report
        print(f"  Snapshot Path:            {rep.snapshot_dir}")
        print(f"  Total Source Records:     {rep.total_source_records}")
        print(f"  Valid EQ Series Symbols:  {rep.eq_series_count}")
        print(f"  Research-Eligible Count:  {rep.final_research_eligible_count}")
        print(f"  Excluded Records:         {rep.final_excluded_count}")

        universe_csv = Path(rep.snapshot_dir) / "eligible.csv"
        if not universe_csv.exists() or len(uni_res.eligible_records) == 0:
            print("ERROR: Research universe contains 0 eligible securities.", file=sys.stderr)
            sys.exit(1)

    except Exception as exc:
        print(f"ERROR: Failed to build universe snapshot: {exc}", file=sys.stderr)
        sys.exit(1)

    # -------------------------------------------------------------
    # Step 2: Build & Materialize Canonical Research Dataset
    # -------------------------------------------------------------
    print("\n[STEP 2/3] Materializing Canonical Research Dataset...")
    try:
        ds_res = build_research_dataset(
            universe_snapshot_path=universe_csv,
            output_base_dir="data/research_datasets",
            custom_date_tag=date_tag,
            start_date=args.start_date,
            force_refresh=args.force_refresh,
        )
        d_man = ds_res.manifest
        print(f"  Dataset Directory:        {ds_res.dataset_dir}")
        print(f"  Total Requested Symbols:  {d_man.total_requested}")
        print(f"  Materialized Symbols:     {d_man.successful_symbols}")
        print(f"  Failed Symbols:           {d_man.failed_symbols}")
        print(f"  Cache Hits:               {d_man.cache_hits}")
        print(f"  Fresh Downloads:          {d_man.fresh_downloads}")
        print(f"  Date Range Observed:      {d_man.earliest_available_date} -> {d_man.latest_available_date}")

        if d_man.successful_symbols == 0:
            print("ERROR: Research dataset contains 0 materialized securities.", file=sys.stderr)
            sys.exit(1)

    except Exception as exc:
        print(f"ERROR: Failed to build research dataset: {exc}", file=sys.stderr)
        sys.exit(1)

    # -------------------------------------------------------------
    # Step 3: Run Research Screening Engine
    # -------------------------------------------------------------
    print("\n[STEP 3/3] Executing Phase 9C Research Screening Engine...")
    try:
        scr_res = run_research_screening(
            dataset_dir=ds_res.dataset_dir,
            output_base_dir="data/research_results",
            custom_date_tag=date_tag,
            min_avg_turnover_cr=args.min_turnover_cr,
            max_workers=args.max_workers,
        )
        s_man = scr_res.manifest
        print(f"  Results Directory:        {scr_res.results_dir}")
        print(f"  Total Input Securities:   {s_man.total_input_securities}")
        print(f"  Successful Evaluations:   {s_man.successful_evaluations}")
        print(f"  Failed Evaluations:       {s_man.failed_evaluations}")

    except Exception as exc:
        print(f"ERROR: Research screening engine failed: {exc}", file=sys.stderr)
        sys.exit(1)

    # -------------------------------------------------------------
    # Step 4: Quality & Integrity Verification
    # -------------------------------------------------------------
    print("\n" + "=" * 90)
    print("DAILY SCREENING RESULTS INTEGRITY VERIFICATION")
    print("=" * 90)

    # 4.1 Verify Files Exist
    results_dir = scr_res.results_dir
    expected_files = [
        "all_results.csv",
        "candidates.csv",
        "disqualified.csv",
        "failures.csv",
        "research_manifest.json",
    ]
    missing = [f for f in expected_files if not (results_dir / f).exists()]
    if missing:
        print(f"ERROR: Missing output files in results directory: {missing}", file=sys.stderr)
        sys.exit(1)

    # 4.2 Failure Rate Check
    total = s_man.total_input_securities
    success = s_man.successful_evaluations
    failed = s_man.failed_evaluations
    failure_rate = (failed / total * 100.0) if total > 0 else 100.0

    print(f"Total Evaluated:           {success} / {total} ({failure_rate:.1f}% failure rate)")
    print(f"High Priority Candidates:  {s_man.high_priority_candidates_count}")
    print(f"Qualified Candidates:      {s_man.qualified_candidates_count}")
    print(f"Watchlist Setups:          {s_man.watchlist_candidates_count}")
    print(f"Disqualified Setups:       {s_man.disqualified_count}")
    print(f"Mechanically Qualified:    {s_man.mechanically_qualified_count}")

    if failure_rate > args.max_failure_rate_pct:
        print(
            f"ERROR: Failure rate {failure_rate:.1f}% exceeds maximum allowable threshold ({args.max_failure_rate_pct}%). "
            "Halting deployment to prevent bad data publication.",
            file=sys.stderr,
        )
        sys.exit(1)

    if success == 0:
        print("ERROR: Zero securities evaluated successfully.", file=sys.stderr)
        sys.exit(1)

    print("\nSUCCESS: Daily screening run verified and ready for Streamlit dashboard.")
    print("=" * 90)
    sys.exit(0)


if __name__ == "__main__":
    main()
