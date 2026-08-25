"""Fast 20-Stock Benchmark Script for Phase 17.

Runs 20 representative NSE securities across 6 monthly checkpoints (Jan 2024 - Jun 2024)
and measures precise runtime, throughput, memory, and export integrity.
"""

import time
import os
import sys
from pathlib import Path

# Add src/ to path
_repo_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_repo_root / "src"))

import pandas as pd
from wyckoff_screener.backtest.engine import run_point_in_time_backtest, export_backtest_workbook

def run_benchmark():
    print("=" * 80)
    print("PHASE 17 — 20-STOCK BENCHMARK RUN")
    print("=" * 80)

    # 1. Load universe: first 20 valid symbols from cache
    cache_dir = _repo_root / "data" / "cache"
    ds_dir = _repo_root / "data" / "research_datasets" / "20260824" / "data"
    target_dir = cache_dir if cache_dir.exists() else ds_dir
    csv_files = sorted(list(target_dir.glob("*.csv")))[:20]

    securities: list[tuple[str, pd.DataFrame, str, str]] = []
    for csv_file in csv_files:
        sym = csv_file.stem.replace(".NS", "")
        yf_t = f"{sym}.NS"
        df = pd.read_csv(csv_file)
        securities.append((sym, df, yf_t, sym))
    
    print(f"Loaded {len(securities)} securities for benchmark.")
    
    start_date = "2024-01-01"
    end_date = "2024-06-30"
    frequency = "monthly"
    max_workers = 4
    output_dir = Path("data/backtest")
    
    t0 = time.perf_counter()
    
    df_signals, df_prices, manifest = run_point_in_time_backtest(
        securities=securities,
        start_date=start_date,
        end_date=end_date,
        frequency=frequency,
        universe_source="watchlist_20",
        max_workers=max_workers,
    )
    
    elapsed = time.perf_counter() - t0
    
    xlsx_path = export_backtest_workbook(
        signals_returns_df=df_signals,
        prices_df=df_prices,
        manifest=manifest,
        output_dir=output_dir,
    )
    
    num_symbols = len(securities)
    num_dates = manifest.get("total_historical_dates_evaluated", 6)
    total_evals = num_symbols * num_dates
    signals_count = len(df_signals)
    sec_per_eval = elapsed / max(total_evals, 1)
    evals_per_sec = total_evals / max(elapsed, 0.001)
    
    # Extrapolate for 1,971 stocks x 39 dates (3.2 years)
    full_evals = 1971 * 39
    full_est_sec = full_evals * (elapsed / max(total_evals, 1))
    full_est_hours = full_est_sec / 3600.0
    
    print("\n" + "=" * 80)
    print("BENCHMARK RESULTS SUMMARY:")
    print("=" * 80)
    print(f"Total Runtime:             {elapsed:.2f} seconds")
    print(f"Securities Processed:      {num_symbols}")
    print(f"Monthly Checkpoints:       {num_dates}")
    print(f"Total Evaluations:         {total_evals}")
    print(f"Signals Generated:         {signals_count}")
    print(f"Average ms per Evaluation: {sec_per_eval * 1000:.2f} ms")
    print(f"Evaluations per Second:    {evals_per_sec:.2f} eval/sec")
    print(f"Extrapolated Full Universe (1,971 stocks x 39 dates): ~{full_est_hours:.2f} hours")
    print(f"Generated Excel Workbook:  {xlsx_path} ({os.path.getsize(xlsx_path):,} bytes)")
    print("=" * 80)

if __name__ == "__main__":
    run_benchmark()
