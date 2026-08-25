"""CLI Script to Export Screener Candidates into Google Sheets Validation Workbook.

Usage:
    python scripts/export_google_sheets.py
    python scripts/export_google_sheets.py --candidates-path data/research_results/20260824/candidates.csv
    python scripts/export_google_sheets.py --top-n 20 --output-dir data/google_sheets
"""

import argparse
from pathlib import Path
import sys
import pandas as pd

# Add src to path
_repo_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_repo_root / "src"))

from wyckoff_screener.google_sheets.exporter import (
    format_screener_candidates_for_signals_sheet,
    export_signals_to_google_sheets_workbook,
    SCHEMA_VERSION,
)
from wyckoff_screener.google_sheets.evaluator import evaluate_trade_outcome


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Export Wyckoff Screener Candidates into Google Sheets Validation Template."
    )
    parser.add_argument(
        "--candidates-path",
        type=str,
        default="data/research_results/20260824/candidates.csv",
        help="Path to candidates.csv produced by production screener run.",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="data/google_sheets",
        help="Output directory for Google Sheets artifacts (default: data/google_sheets).",
    )
    parser.add_argument(
        "--top-n",
        type=int,
        default=None,
        help="Limit export to top N candidates ranked by composite score.",
    )
    parser.add_argument(
        "--default-stop-pct",
        type=float,
        default=5.0,
        help="Default stop loss percentage below entry price (default: 5.0).",
    )
    parser.add_argument(
        "--default-target-pct",
        type=float,
        default=15.0,
        help="Default target percentage above entry price (default: 15.0).",
    )

    args = parser.parse_args()

    candidates_file = Path(args.candidates_path)
    if not candidates_file.exists():
        print(f"ERROR: Candidates file not found at {candidates_file}")
        return 1

    print("=" * 80)
    print("WYCKOFF SCREENER -> GOOGLE SHEETS VALIDATION EXPORT")
    print(f"Source Candidates: {candidates_file}")
    print(f"Schema Version:    {SCHEMA_VERSION}")
    print(f"Output Directory:  {args.output_dir}")
    print(f"Stop / Target:     -{args.default_stop_pct}% / +{args.default_target_pct}%")
    print("=" * 80)

    df_raw = pd.read_csv(candidates_file)
    print(f"Loaded {len(df_raw)} raw candidates.")

    # Filter top N if requested
    if args.top_n and args.top_n < len(df_raw):
        df_raw = df_raw.head(args.top_n)
        print(f"Filtered to top {args.top_n} candidates.")

    # Format into SIGNALS schema
    signals_df = format_screener_candidates_for_signals_sheet(
        df_raw,
        default_stop_pct=args.default_stop_pct,
        default_target_pct=args.default_target_pct,
    )

    # Evaluate outcomes on historical data if available in data/cache or dataset
    results_list = []
    cache_dir = _repo_root / "data" / "cache"
    ds_dir = _repo_root / "data" / "research_datasets" / "20260824" / "data"

    for _, sig in signals_df.iterrows():
        sym = str(sig["Symbol"])
        sig_dt = str(sig["Signal_Date"])
        ep = float(sig["Entry_Price"])
        sp = float(sig["Stop_Price"])
        tp = float(sig["Target_1"])

        csv_p = cache_dir / f"{sym}.NS.csv"
        if not csv_p.exists():
            csv_p = ds_dir / f"{sym}.NS.csv"

        if csv_p.exists():
            stock_df = pd.read_csv(csv_p)
            stock_df["Date"] = pd.to_datetime(stock_df["Date"])
            # Future bars strictly AFTER signal date (zero lookahead bias)
            post_df = stock_df[stock_df["Date"] > pd.to_datetime(sig_dt)].sort_values(by="Date").reset_index(drop=True)
            outcome = evaluate_trade_outcome(
                symbol=sym,
                signal_date=sig_dt,
                post_signal_df=post_df,
                entry_price=ep,
                stop_price=sp,
                target_price=tp,
            )
            results_list.append(outcome.to_dict())
        else:
            # Pending live forward evaluation
            outcome = evaluate_trade_outcome(
                symbol=sym,
                signal_date=sig_dt,
                post_signal_df=pd.DataFrame(),
                entry_price=ep,
                stop_price=sp,
                target_price=tp,
            )
            results_list.append(outcome.to_dict())

    test_results_df = pd.DataFrame(results_list)

    # Export multi-tab workbook and CSV
    xlsx_path = export_signals_to_google_sheets_workbook(
        signals_df=signals_df,
        test_results_df=test_results_df,
        output_dir=args.output_dir,
    )

    print("\n" + "=" * 80)
    print("GOOGLE SHEETS EXPORT COMPLETED SUCCESSFULLY")
    print(f"1. Excel Workbook: {xlsx_path} (Ready for Google Sheets upload)")
    print(f"2. Raw CSV:        {Path(args.output_dir) / 'screener_signals.csv'}")
    print(f"3. Signals Ready:  {len(signals_df)} rows")
    print("=" * 80)

    return 0


if __name__ == "__main__":
    sys.exit(main())
