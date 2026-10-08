import os
import sys
import json
import pandas as pd
from pathlib import Path

INPUT_DIR = Path("c:/Users/surya/Downloads/wyckoff-stock-screener/data/validation_results/20260826")
RETURNS_CSV = INPUT_DIR / "backtest_returns.csv"
PRICES_CSV = INPUT_DIR / "historical_prices.csv"
DIAG_OUT_DIR = Path("c:/Users/surya/Downloads/wyckoff-stock-screener/data/diagnostics/phase18")

def run_oos_validation():
    DIAG_OUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # 1. Load prices to check date range
    if not PRICES_CSV.exists():
        print(f"ERROR: Prices CSV not found at {PRICES_CSV}")
        return
        
    df_prices = pd.read_csv(PRICES_CSV, usecols=["Date"])
    max_date = df_prices["Date"].max()
    
    # Check if we have any data after 2026-08-24
    oos_cutoff = "2026-08-24"
    oos_df = df_prices[df_prices["Date"] > oos_cutoff]
    
    # Write empty/pending progress
    prog = {
        "phase": 18,
        "status": "stopped",
        "overall_percent": 0.0,
        "current_experiment": "Checking Out-of-Sample Date Range",
        "stocks_processed": 0,
        "stocks_total": 0,
        "checkpoints_processed": 0,
        "checkpoints_total": 0,
        "signals_processed": 0,
        "trades_processed": 0,
        "elapsed_seconds": 0,
        "estimated_remaining_seconds": None,
        "errors": 0
    }
    with open(DIAG_OUT_DIR / "progress.json", "w") as f:
        json.dump(prog, f, indent=2)
        
    if len(oos_df) == 0:
        print(f"OOS VALIDATION STOPPED: No out-of-sample data available (dataset ends at {max_date}).")
        print(f"To perform out-of-sample validation, new market data covering dates after {oos_cutoff} must be acquired.")
        
        # Save placeholder results indicating validation is pending
        results = {
            "status": "pending_data",
            "message": f"Validation requires dates after {oos_cutoff}. Current dataset max date: {max_date}.",
            "baseline_profitable_oos": "NOT TESTABLE YET",
            "spring_edge_survives": "NOT TESTABLE YET",
            "sc_edge_survives": "NOT TESTABLE YET",
            "sos_edge_survives": "NOT TESTABLE YET",
            "spring_sc_bear_breadth_survives": "NOT TESTABLE YET",
            "neutral_regime_weakness_survives": "NOT TESTABLE YET",
            "composite_score_discriminates": "NOT TESTABLE YET",
            "lps_breakout_improves_execution": "NOT TESTABLE YET",
            "tail_robustness": "NOT TESTABLE YET",
            "survivorship_free": "FAIL"
        }
        with open(DIAG_OUT_DIR / "phase18_results.json", "w") as f:
            json.dump(results, f, indent=2)
        return
        
    print("Out-of-sample data detected! Running validation...")
    # (OOS validation logic would execute here once the new dataset is loaded)

if __name__ == "__main__":
    run_oos_validation()
