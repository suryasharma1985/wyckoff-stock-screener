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
from wyckoff_screener.scanning.broad_filter import evaluate_broad_setup
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
        required=True,
        help="Path to CSV containing NSE universe (columns: Symbol, Series, Company Name).",
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

    # 2. Batch Download & Cache
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

    # Build symbol -> company name mapping
    company_map = {rec.yfinance_ticker: rec.company_name for rec in report.accepted_symbols}

    # 3. Quantitative Screening Loop
    print("\nRunning quantitative filters & Wyckoff event detectors...")
    all_results = []
    error_logs: list[str] = []

    for failure in download_result.failures:
        error_logs.append(
            f"[{failure.timestamp_utc}] DOWNLOAD_ERROR ticker={failure.ticker} "
            f"stage={failure.stage} error={failure.error_message}"
        )

    for ticker, df in download_result.successful_data.items():
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
