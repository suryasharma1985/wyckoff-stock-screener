"""CLI Batch Screener for NSE Equities with TradingView Review Export.

Usage:
    python -m wyckoff_screener.scan --universe data/sample_nse_symbols.csv
"""

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import sys
from typing import Any
import pandas as pd

from wyckoff_screener.data.batch_downloader import download_and_cache_universe
from wyckoff_screener.data.dataset_builder import build_research_dataset
from wyckoff_screener.research.screening_engine import run_research_screening
from wyckoff_screener.scanning.broad_filter import evaluate_broad_setup
from wyckoff_screener.universe.builder import build_research_universe
from wyckoff_screener.universe.nse_symbols import (
    DEFAULT_ELIGIBLE_SERIES,
    load_nse_universe_csv,
)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Wyckoff & VSA Batch Screener for NSE Equities with TradingView Review Integration."
    )
    parser.add_argument(
        "--universe",
        type=str,
        default="data/sample_nse_symbols.csv",
        help="Path to CSV containing NSE universe or snapshot eligible.csv (default 'data/sample_nse_symbols.csv').",
    )
    parser.add_argument(
        "--build-universe",
        action="store_true",
        help="Build a new dated research universe snapshot before screening.",
    )
    parser.add_argument(
        "--build-dataset",
        action="store_true",
        help="Build a new dated canonical research dataset snapshot from the universe before screening.",
    )
    parser.add_argument(
        "--research-screening",
        action="store_true",
        help="Execute Phase 9C Research Screening Engine across the dataset instead of standard scan.",
    )
    parser.add_argument(
        "--dataset-dir",
        type=str,
        default=None,
        help="Path to materialized research dataset directory (containing manifest.json, symbols.csv, data/).",
    )
    parser.add_argument(
        "--dataset-base-dir",
        type=str,
        default="data/research_datasets",
        help="Base directory to save research datasets (default 'data/research_datasets').",
    )
    parser.add_argument(
        "--universe-source",
        type=str,
        default="sample",
        help="Universe source to build from: 'sample', 'nse_eq' (official NSE live), or 'custom_csv' (default 'sample').",
    )
    parser.add_argument(
        "--snapshot-dir",
        type=str,
        default="data/universe_snapshots",
        help="Base directory to save universe snapshots (default 'data/universe_snapshots').",
    )
    parser.add_argument(
        "--eligible-series",
        type=str,
        default="EQ",
        help="Comma-separated eligible series list (default 'EQ'). Note: 'BE' must be explicitly selected.",
    )
    parser.add_argument(
        "--cache-dir",
        type=str,
        default="data/cache",
        help="Directory to cache OHLCV CSVs and metadata (default 'data/cache').",
    )
    parser.add_argument(
        "--start-date",
        type=str,
        default="2023-01-01",
        help="Start date for historical OHLCV data (default '2023-01-01').",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="data/screening_results.csv",
        help="Path to export screening results CSV (default 'data/screening_results.csv').",
    )
    parser.add_argument(
        "--error-log",
        type=str,
        default="data/scan_errors.log",
        help="Path to write complete scan error log (default 'data/scan_errors.log').",
    )
    parser.add_argument(
        "--min-turnover-cr",
        type=float,
        default=1.0,
        help="Minimum 20-day average daily turnover in INR Crores (default 1.0).",
    )
    parser.add_argument(
        "--force-refresh",
        action="store_true",
        help="Force re-downloading market data even if local cache exists.",
    )

    args = parser.parse_args()

    print("=" * 90)
    print("WYCKOFF & VSA BATCH SCREENER (NSE) — BATCH SCANNER")
    print("=" * 90)

    # 1. Ingest & Validate Universe
    eligible_series_tuple = tuple(s.strip().upper() for s in args.eligible_series.split(","))

    if args.build_universe:
        print(f"Building research universe from source '{args.universe_source}'...")
        build_res = build_research_universe(
            source=args.universe_source,
            output_base_dir=args.snapshot_dir,
            eligible_series=eligible_series_tuple,
            min_avg_turnover_cr=args.min_turnover_cr,
        )
        rep = build_res.report
        print(f"  Snapshot created at:         {rep.snapshot_dir}")
        print(f"  Total source records:        {rep.total_source_records}")
        print(f"  Valid EQ symbols:            {rep.eq_series_count}")
        print(f"  Final research-eligible:     {rep.final_research_eligible_count}")
        print(f"  Total excluded records:      {rep.final_excluded_count}")
        print("  Rejections breakdown:")
        for r_name, r_count in rep.rejections_by_reason.items():
            print(f"    - {r_name}: {r_count}")

        # Set universe path to generated eligible.csv for downstream screening
        args.universe = str(Path(rep.snapshot_dir) / "eligible.csv")
        print(f"Proceeding to screen {len(build_res.eligible_records)} eligible securities from {args.universe}...\n")

    if args.build_dataset:
        print(f"Building canonical research dataset from universe '{args.universe}'...")
        ds_res = build_research_dataset(
            universe_snapshot_path=args.universe,
            output_base_dir=args.dataset_base_dir,
            start_date=args.start_date,
            force_refresh=args.force_refresh,
        )
        man = ds_res.manifest
        print(f"  Dataset materialized at:    {ds_res.dataset_dir}")
        print(f"  Total requested:            {man.total_requested}")
        print(f"  Successful materialized:    {man.successful_symbols}")
        print(f"  Failed symbols:             {man.failed_symbols}")
        print(f"  Cache hits:                 {man.cache_hits}")
        print(f"  Fresh downloads:            {man.fresh_downloads}")
        print(f"  Date range observed:        {man.earliest_available_date} -> {man.latest_available_date}")
        print(f"  Average bars/symbol:        {man.avg_bars_per_symbol}")
        args.dataset_dir = str(ds_res.dataset_dir)
        args.universe = str(Path(args.dataset_dir) / "symbols.csv")

    if args.research_screening:
        if not args.dataset_dir:
            print("ERROR: --research-screening requires --dataset-dir or --build-dataset.", file=sys.stderr)
            sys.exit(1)
        print("=" * 90)
        print("RUNNING PHASE 9C BROAD RESEARCH SCREENING ENGINE...")
        print(f"Target Dataset: {args.dataset_dir}")
        print("=" * 90)
        r_res = run_research_screening(
            dataset_dir=args.dataset_dir,
            output_base_dir="data/research_results",
            min_avg_turnover_cr=args.min_turnover_cr,
        )
        m = r_res.manifest
        print("\n" + "=" * 90)
        print(f"RESEARCH SCREENING COMPLETE: {r_res.results_dir}")
        print(f"Total Evaluated: {m.successful_evaluations} / {m.total_input_securities}")
        print(f"Categories: High Priority={m.high_priority_candidates_count}, Qualified={m.qualified_candidates_count}, Watchlist={m.watchlist_candidates_count}, Disqualified={m.disqualified_count}, No Setup={m.no_setup_count}")
        print("=" * 90)
        return

    print(f"Loading universe from: {args.universe}")
    print(f"Eligible series: {eligible_series_tuple}")

    try:
        report = load_nse_universe_csv(args.universe, eligible_series=eligible_series_tuple)
    except Exception as exc:
        print(f"ERROR: Failed to load universe CSV: {exc}", file=sys.stderr)
        sys.exit(1)

    print(f"  Total rows ingested: {report.total_rows_ingested}")
    print(f"  Accepted symbols:    {report.accepted_count}")
    print(f"  Rejected rows:       {report.rejected_count}")
    print(f"  Duplicates detected: {len(report.duplicate_symbols)}")

    if report.accepted_count == 0:
        print("No valid symbols found in universe. Exiting.", file=sys.stderr)
        sys.exit(1)

    # 2. Acquire Market Data (from materialized dataset or cache)
    successful_data_map: dict[str, pd.DataFrame] = {}
    download_failures: list[Any] = []

    if args.dataset_dir:
        data_path = Path(args.dataset_dir) / "data" if (Path(args.dataset_dir) / "data").exists() else Path(args.dataset_dir)
        print(f"\nLoading canonical OHLCV DataFrames from dataset: {data_path}...")
        for rec in report.accepted_symbols:
            csv_f = data_path / f"{rec.yfinance_ticker}.csv"
            if csv_f.exists():
                try:
                    df = pd.read_csv(csv_f)
                    successful_data_map[rec.yfinance_ticker] = df
                except Exception as exc:
                    print(f"  Warning: failed to read {csv_f}: {exc}")
        print(f"  Loaded {len(successful_data_map)} canonical DataFrames directly from dataset.")
    else:
        tickers = report.get_tickers_list()
        print(f"\nFetching/loading market data for {len(tickers)} tickers (cache: {args.cache_dir})...")

        download_result = download_and_cache_universe(
            tickers=tickers,
            cache_dir=args.cache_dir,
            start_date=args.start_date,
            force_refresh=args.force_refresh,
        )

        print(f"  Cached data used:     {download_result.cached_count}")
        print(f"  Newly downloaded:     {download_result.downloaded_count}")
        print(f"  Download failures:    {download_result.failed_count}")
        successful_data_map = download_result.successful_data
        download_failures = download_result.failures

    # Build symbol -> company name mapping
    company_map = {rec.yfinance_ticker: rec.company_name for rec in report.accepted_symbols}

    # 3. Quantitative Screening Loop
    print("\nRunning quantitative filters & Wyckoff event detectors...")
    all_results = []
    error_logs: list[str] = []

    for failure in download_failures:
        error_logs.append(
            f"[{failure.timestamp_utc}] DOWNLOAD_ERROR ticker={failure.ticker} "
            f"stage={failure.stage} error={failure.error_message}"
        )

    for ticker, df in successful_data_map.items():
        comp_name = company_map.get(ticker, ticker)
        try:
            res = evaluate_broad_setup(
                df,
                symbol=ticker,
                company_name=comp_name,
                min_avg_turnover_cr=args.min_turnover_cr,
            )
            all_results.append(res)
            if res.errors:
                for err in res.errors:
                    error_logs.append(f"[{datetime.now(timezone.utc).isoformat()}] EVAL_ERROR symbol={ticker} error={err}")
        except Exception as exc:
            error_logs.append(f"[{datetime.now(timezone.utc).isoformat()}] FATAL_EVAL_ERROR symbol={ticker} error={exc}")

    # 4. Compute Counts & Statistics
    total_screened = len(all_results)
    mech_qualified = [r for r in all_results if r.is_mechanically_qualified]
    phase_c_or_d = [
        r for r in all_results
        if r.candidate_event_summary.get("is_possible_LPS")
        or r.candidate_event_summary.get("is_possible_SOS")
        or r.candidate_event_summary.get("is_possible_Spring")
    ]
    possible_lps = [r for r in all_results if r.candidate_event_summary.get("is_possible_LPS")]
    possible_sos = [r for r in all_results if r.candidate_event_summary.get("is_possible_SOS")]
    utad_warnings = [r for r in all_results if r.candidate_event_summary.get("is_UTAD_warning")]
    pending_reviews = [r for r in all_results if r.manual_review_pending]

    # 5. Export Results CSV
    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    rows = [r.to_dict() for r in all_results]
    if rows:
        results_df = pd.DataFrame(rows)
        # Order by candidate events first, then mechanically qualified
        results_df.sort_values(
            by=["is_mechanically_qualified", "possible_LPS", "possible_SOS", "possible_Spring"],
            ascending=[False, False, False, False],
            inplace=True,
        )
        results_df.to_csv(out_path, index=False)

    # Export Error Log
    err_path = Path(args.error_log)
    err_path.parent.mkdir(parents=True, exist_ok=True)
    with open(err_path, "w", encoding="utf-8") as ef:
        ef.write("\n".join(error_logs) if error_logs else "No errors encountered during scan.\n")

    # 6. Print Summary Report to Console
    print("\n" + "=" * 90)
    print("SCREENING EXECUTION SUMMARY")
    print("=" * 90)
    print(f"Accepted Universe Symbols:      {report.accepted_count}")
    print(f"Rejected Universe Symbols:      {report.rejected_count}")
    print(f"Cached Market Data:             {download_result.cached_count}")
    print(f"Newly Downloaded:               {download_result.downloaded_count}")
    print(f"Download Failures:              {download_result.failed_count}")
    print(f"Total Evaluated Stocks:         {total_screened}")
    print(f"Mechanically Qualified:         {len(mech_qualified)}")
    print(f"Candidate Phase C/D Setups:     {len(phase_c_or_d)}")
    print(f"  - Possible LPS Candidates:    {len(possible_lps)}")
    print(f"  - Possible SOS Candidates:    {len(possible_sos)}")
    print(f"UTAD Distribution Warnings:     {len(utad_warnings)}")
    print(f"Pending TradingView Reviews:    {len(pending_reviews)}")
    print(f"\nResults CSV exported to:        {out_path.resolve()}")
    print(f"Complete error log written to:  {err_path.resolve()}")
    print("=" * 90)


if __name__ == "__main__":
    main()
