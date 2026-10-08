import os
import json
import pandas as pd
from pathlib import Path

# Paths
INPUT_DIR = Path("c:/Users/surya/Downloads/wyckoff-stock-screener/data/validation_results/20260826")
PRICES_CSV = INPUT_DIR / "historical_prices.csv"
DIAG_OUT_DIR = Path("c:/Users/surya/Downloads/wyckoff-stock-screener/data/diagnostics/phase19")

def main():
    DIAG_OUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # 1. Load prices to check date range
    if not PRICES_CSV.exists():
        print(f"ERROR: Prices CSV not found at {PRICES_CSV}")
        return
        
    df_prices = pd.read_csv(PRICES_CSV, usecols=["Date"])
    max_date = df_prices["Date"].max()
    
    oos_cutoff = "2026-08-24"
    oos_df = df_prices[df_prices["Date"] > oos_cutoff]
    
    # 2. Write manifest.json
    manifest = {
        "phase": 19,
        "status": "stopped",
        "data_audit": {
            "earliest_date": str(df_prices["Date"].min()),
            "latest_date": str(max_date),
            "oos_cutoff": oos_cutoff,
            "oos_data_available": len(oos_df) > 0,
            "missing_period": "2026-08-25 through present"
        }
    }
    with open(DIAG_OUT_DIR / "manifest.json", "w") as f:
        json.dump(manifest, f, indent=2)
        
    # 3. Write progress.json
    progress = {
        "phase": 19,
        "status": "stopped",
        "overall_percent": 0.0,
        "current_experiment": "Audit Date Range",
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
        json.dump(progress, f, indent=2)
        
    if len(oos_df) == 0:
        print(f"OOS VALIDATION STOPPED: No out-of-sample data available (dataset ends at {max_date}).")
        print(f"To perform out-of-sample validation, new market data covering dates after {oos_cutoff} must be acquired.")
        
        # Save placeholder results
        results = {
            "status": "NOT TESTABLE",
            "message": f"Validation requires dates after {oos_cutoff}. Current dataset max date: {max_date}.",
            "baseline_profitable_oos": "NOT TESTABLE",
            "spring_edge_survives": "NOT TESTABLE",
            "sc_edge_survives": "NOT TESTABLE",
            "sos_edge_survives": "NOT TESTABLE",
            "spring_sc_bear_breadth_survives": "NOT TESTABLE",
            "neutral_regime_weakness_survives": "NOT TESTABLE",
            "composite_score_discriminates": "NOT TESTABLE",
            "lps_breakout_improves_execution": "NOT TESTABLE",
            "tail_robustness": "NOT TESTABLE",
            "survivorship_free": "FAIL"
        }
        with open(DIAG_OUT_DIR / "oos_results.json", "w") as f:
            json.dump(results, f, indent=2)
            
        # Create empty CSV placeholders
        pd.DataFrame().to_csv(DIAG_OUT_DIR / "discovery_vs_oos.csv", index=False)
        pd.DataFrame().to_csv(DIAG_OUT_DIR / "event_results.csv", index=False)
        pd.DataFrame().to_csv(DIAG_OUT_DIR / "regime_results.csv", index=False)
        pd.DataFrame().to_csv(DIAG_OUT_DIR / "tail_analysis.csv", index=False)
        pd.DataFrame().to_csv(DIAG_OUT_DIR / "cost_sensitivity.csv", index=False)
        return
        
    print("OOS data detected! Running temporal validation...")
    # (Full validation sequence runs here once fresh post-cutoff data is fetched)

if __name__ == "__main__":
    main()
