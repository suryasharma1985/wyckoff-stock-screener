"""CLI Runner for Historical Signal Generation & Google Sheets Backtest Export.

Usage:
    python scripts/generate_historical_signals.py --universe-source sample --start-date 2024-01-01 --end-date 2024-06-30 --frequency monthly
    python scripts/generate_historical_signals.py --universe-source nse_eq --start-date 2024-01-01 --end-date 2024-12-31 --frequency monthly
"""

import argparse
from datetime import datetime, timezone
from pathlib import Path
import sys
import pandas as pd

# Add src/ to path
_repo_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_repo_root / "src"))

from wyckoff_screener.backtest.engine import (
    export_backtest_workbook,
    run_point_in_time_backtest,
)

DEFAULT_SAMPLE_CSV_PATH = "data/sample_nse_ohlcv.csv"
DEFAULT_RESEARCH_SNAPSHOT_PATH = "data/research_datasets/20260824/data"


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Wyckoff & VSA Historical Point-in-Time Signal Generation for Google Sheets Backtesting."
    )
    parser.add_argument(
        "--universe-source",
        choices=["sample", "nse_eq", "watchlist"],
        default="sample",
        help="Universe source: 'sample' (fast 3-stock validation), 'watchlist' (initial 31-stock), or 'nse_eq' (full canonical dataset).",
    )
    parser.add_argument(
        "--start-date",
        type=str,
        default="2023-06-01",
        help="Start date for signal generation (YYYY-MM-DD).",
    )
    parser.add_argument(
        "--end-date",
        type=str,
        default="2026-08-24",
        help="End date for signal generation (YYYY-MM-DD).",
    )
    parser.add_argument(
        "--frequency",
        choices=["monthly", "weekly", "daily"],
        default="monthly",
        help="Screening checkpoint frequency (default 'monthly').",
    )
    parser.add_argument(
        "--min-turnover-cr",
        type=float,
        default=1.0,
        help="Minimum 20-day average daily turnover in INR Crores (default 1.0).",
    )
    parser.add_argument(
        "--min-bars",
        type=int,
        default=60,
        help="Minimum historical bars required before evaluating a checkpoint (default 60).",
    )
    parser.add_argument(
        "--max-workers",
        type=int,
        default=4,
        help="Number of concurrent worker threads for historical evaluations (default 4).",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="data/backtest",
        help="Output directory for backtest export (default 'data/backtest').",
    )

    args = parser.parse_args()

    print("=" * 80)
    print("WYCKOFF & VSA HISTORICAL BACKTEST ENGINE (GOOGLE SHEETS & EXCEL READY)")
    print(f"Universe Source:   {args.universe_source}")
    print(f"Date Range:        {args.start_date} -> {args.end_date}")
    print(f"Frequency:         {args.frequency}")
    print(f"Min Turnover Gate: INR {args.min_turnover_cr} Cr")
    print(f"Entry Model:       next_trading_day_open (T+1 Open)")
    print(f"Workers:           {args.max_workers}")
    print(f"Survivorship Bias: Explicitly Disclosed (Current constituent snapshot)")
    print("=" * 80)

    # 1. Load securities according to universe source
    securities: list[tuple[str, pd.DataFrame, str, str]] = []

    if args.universe_source == "sample":
        primary_stocks = ["ANANTRAJ.NS", "APOLLO.NS", "HINDCOPPER.NS"]
        cache_dir = _repo_root / "data" / "cache"
        ds_dir = _repo_root / "data" / "research_datasets" / "20260824" / "data"
        for yf_t in primary_stocks:
            csv_path = cache_dir / f"{yf_t}.csv"
            if not csv_path.exists():
                csv_path = ds_dir / f"{yf_t}.csv"
            if csv_path.exists():
                sym = yf_t.replace(".NS", "")
                df = pd.read_csv(csv_path)
                securities.append((sym, df, yf_t, sym))

    elif args.universe_source == "watchlist":
        cache_dir = _repo_root / "data" / "cache"
        ds_dir = _repo_root / "data" / "research_datasets" / "20260824" / "data"
        target_dir = cache_dir if cache_dir.exists() else ds_dir
        csv_files = sorted(list(target_dir.glob("*.csv")))[:31]
        for csv_file in csv_files:
            sym = csv_file.stem.replace(".NS", "")
            yf_t = f"{sym}.NS"
            df = pd.read_csv(csv_file)
            securities.append((sym, df, yf_t, sym))

    elif args.universe_source == "nse_eq":
        ds_dir = _repo_root / "data" / "research_datasets" / "20260824" / "data"
        if not ds_dir.exists():
            print(f"ERROR: Canonical dataset not found at {ds_dir}")
            return 1
        for csv_f in ds_dir.glob("*.csv"):
            sym = csv_f.stem.replace(".NS", "")
            yf_t = f"{sym}.NS"
            df = pd.read_csv(csv_f)
            securities.append((sym, df, yf_t, sym))

    if not securities:
        print("ERROR: No securities found to evaluate.")
        return 1

    print(f"\nLoaded {len(securities)} securities for historical evaluation.")

    # 2. Run historical generation & forward returns
    run_tag = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    run_id = f"backtest_{args.universe_source}_{args.frequency}_{run_tag}"
    out_dir = Path(args.output_dir) if args.output_dir else _repo_root / "data" / "backtest"

    signals_df, prices_df, manifest = run_point_in_time_backtest(
        securities=securities,
        start_date=args.start_date,
        end_date=args.end_date,
        frequency=args.frequency,
        min_bars=args.min_bars,
        min_avg_turnover_cr=args.min_turnover_cr,
        backtest_run_id=run_id,
        universe_source=args.universe_source,
        max_workers=args.max_workers,
    )

    xlsx_path = export_backtest_workbook(signals_df, prices_df, manifest, out_dir)

    print("\n" + "=" * 80)
    print("HISTORICAL BACKTEST EXPORT COMPLETED SUCCESSFULLY")
    print("=" * 80)
    print(f"Multi-Tab Excel Workbook: {xlsx_path} ({xlsx_path.stat().st_size} bytes)")
    print(f"Historical Signals & Ret: {out_dir / 'backtest_returns.csv'} ({len(signals_df)} rows)")
    print(f"Historical Prices Panel:  {out_dir / 'historical_prices.csv'} ({len(prices_df)} price rows)")
    print(f"Backtest Audit Manifest:  {out_dir / 'backtest_manifest.json'}")
    print(f"Historical Signal Dates:  {manifest['total_historical_dates_evaluated']} dates evaluated")
    print(f"High Priority Signals:    {manifest['high_priority_signals_count']}")
    print(f"Qualified Signals:        {manifest['qualified_signals_count']}")
    print(f"Watchlist Signals:        {manifest['watchlist_signals_count']}")
    print(f"Disqualified Signals:     {manifest['disqualified_signals_count']}")
    print("=" * 80)

    return 0



if __name__ == "__main__":
    sys.exit(main())
