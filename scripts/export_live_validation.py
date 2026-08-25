"""CLI Runner for Phase 18B Live Manual Screener Validation System.

Generates:
    data/google_sheets/live_validation_template.xlsx (5 tabs: README, LIVE_SIGNALS, TRACKING, SUMMARY, PARAMETERS)
"""

import argparse
from pathlib import Path
import sys
import pandas as pd

# Add src to path
_repo_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_repo_root / "src"))

from wyckoff_screener.google_sheets.live_validation_builder import export_live_validation_workbook, SCHEMA_VERSION


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Phase 18B: Export Production Candidates to Live Manual Validation Template."
    )
    parser.add_argument(
        "--candidates-path",
        type=str,
        default="data/research_results/20260824/candidates.csv",
        help="Path to candidates.csv.",
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
    print("PHASE 18B — LIVE MANUAL SCREENER VALIDATION SYSTEM EXPORTER")
    print(f"Source Candidates: {c_path}")
    print(f"Output Directory:  {args.output_dir}")
    print(f"Screening Run Date:{args.screening_date}")
    print(f"Schema Version:    {SCHEMA_VERSION}")
    print("=" * 80)

    raw_df = pd.read_csv(c_path)
    print(f"Loaded {len(raw_df)} production candidate signals.")
    hp_count = len(raw_df[raw_df["candidate_category"] == "HIGH_PRIORITY_CANDIDATE"])
    q_count = len(raw_df[raw_df["candidate_category"] == "QUALIFIED_CANDIDATE"])
    print(f"-> High Priority Signals: {hp_count}")
    print(f"-> Qualified Signals:     {q_count}")

    xlsx_path = export_live_validation_workbook(
        candidates_csv_path=c_path,
        output_dir=args.output_dir,
        screening_run_date=args.screening_date,
    )

    print("\n" + "=" * 80)
    print("LIVE VALIDATION TEMPLATE GENERATED SUCCESSFULLY:")
    print("=" * 80)
    print(f"1. Master 5-Tab Workbook: {xlsx_path} ({xlsx_path.stat().st_size:,} bytes)")
    print(f"Total Live Signals Exported: {len(raw_df)}")
    print(f"High Priority Count:         {hp_count}")
    print(f"Qualified Count:             {q_count}")
    print("=" * 80)

    return 0


if __name__ == "__main__":
    sys.exit(main())
