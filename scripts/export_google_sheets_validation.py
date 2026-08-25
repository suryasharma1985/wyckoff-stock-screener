"""CLI Exporter for Phase 18 Google Sheets Forward-Validation System.

Usage:
    python scripts/export_google_sheets_validation.py
    python scripts/export_google_sheets_validation.py --candidates-path data/research_results/20260824/candidates.csv
    python scripts/export_google_sheets_validation.py --output-dir data/google_sheets
"""

import argparse
from pathlib import Path
import sys
import pandas as pd

# Add src to path
_repo_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_repo_root / "src"))

from wyckoff_screener.google_sheets.validation_builder import export_validation_package, SCHEMA_VERSION


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Phase 18: Export Production Candidates to Google Sheets Forward-Validation System."
    )
    parser.add_argument(
        "--candidates-path",
        type=str,
        default="data/research_results/20260824/candidates.csv",
        help="Path to production candidates.csv.",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="data/google_sheets",
        help="Output directory (default: data/google_sheets).",
    )
    parser.add_argument(
        "--screening-date",
        type=str,
        default="20260824",
        help="Screening run date identifier (default: 20260824).",
    )

    args = parser.parse_args()

    c_path = Path(args.candidates_path)
    if not c_path.exists():
        print(f"ERROR: Candidates file not found at {c_path}")
        return 1

    print("=" * 80)
    print("PHASE 18 — GOOGLE SHEETS FORWARD-VALIDATION SYSTEM EXPORTER")
    print(f"Source Candidates: {c_path}")
    print(f"Output Directory:  {args.output_dir}")
    print(f"Screening Run Date:{args.screening_date}")
    print(f"Schema Version:    {SCHEMA_VERSION}")
    print("=" * 80)

    raw_df = pd.read_csv(c_path)
    print(f"Loaded {len(raw_df)} production candidates.")
    hp_count = len(raw_df[raw_df["candidate_category"] == "HIGH_PRIORITY_CANDIDATE"])
    q_count = len(raw_df[raw_df["candidate_category"] == "QUALIFIED_CANDIDATE"])
    print(f"-> High Priority: {hp_count}")
    print(f"-> Qualified:     {q_count}")

    # Generate 8-tab workbook and CSV
    xlsx_path, csv_path = export_validation_package(
        candidates_csv_path=c_path,
        output_dir=args.output_dir,
        screening_run_date=args.screening_date,
    )

    # Generate README_GOOGLE_SHEETS.md
    readme_md_path = Path(args.output_dir) / "README_GOOGLE_SHEETS.md"
    readme_content = f"""# Google Sheets Screener Forward-Validation System

## Quick Start:
1. Open Google Sheets (https://sheets.google.com).
2. Go to **File -> Import -> Upload**.
3. Select `{xlsx_path.name}` or import `{csv_path.name}` into the **CANDIDATES** tab.
4. Select **"Replace spreadsheet"** (for XLSX) or **"Insert new sheet"** (for CSV).
5. All {len(raw_df)} production candidate signals are pre-loaded with immutable screening dates and entry prices.

## Workbook Tabs:
1. **README**: Instructions, lookahead rules, ambiguity rules, and survivorship warnings.
2. **CANDIDATES**: Master candidate table (Columns A through V: Candidate_ID, Screening_Date, Symbol, Score, Entry_Price, Targets, Stops, TradingView_URL).
3. **PRICE_DATA**: `=GOOGLEFINANCE()` reference formulas for daily candle history and NIFTY 50 benchmark tracking.
4. **SIGNALS**: Execution tracking distinguishing screening signals from trade entries/exits.
5. **PERFORMANCE**: Forward returns (+1D, +3D, +5D, +10D, +20D, +30D, +60D, +1M, +3M), MFE, MAE, and NIFTY Alpha.
6. **TRADE_LOG**: Historical log of completed/open trades with outcome classifications.
7. **SUMMARY**: Executive KPIs, Score Predictive Dashboard, Priority Comparison, and Wyckoff Event Dashboard.
8. **CONFIG**: User-editable targets (+10%, +20%, +30%), stop loss (-5%), max holding days (60), and ambiguity rules.
"""
    readme_md_path.write_text(readme_content, encoding="utf-8")

    print("\n" + "=" * 80)
    print("VALIDATION ARTIFACTS GENERATED SUCCESSFULLY:")
    print("=" * 80)
    print(f"1. Master 8-Tab Workbook: {xlsx_path} ({xlsx_path.stat().st_size:,} bytes)")
    print(f"2. Candidate Import CSV:  {csv_path} ({csv_path.stat().st_size:,} bytes)")
    print(f"3. In-Folder Readme:      {readme_md_path}")
    print(f"Total Candidates Exported:{len(raw_df)}")
    print(f"High Priority Count:      {hp_count}")
    print(f"Qualified Count:          {q_count}")
    print("=" * 80)

    return 0


if __name__ == "__main__":
    sys.exit(main())
