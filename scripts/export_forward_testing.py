"""CLI Exporter for Phase 18 Google Sheets Screener Forward-Testing System.

Usage:
    python scripts/export_forward_testing.py
    python scripts/export_forward_testing.py --candidates-path data/research_results/20260824/candidates.csv
    python scripts/export_forward_testing.py --output-dir data/forward_testing --run-id 20260824_1530
"""

import argparse
from pathlib import Path
import sys
import pandas as pd

# Add src to sys.path
_repo_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_repo_root / "src"))

from wyckoff_screener.forward_testing import (
    parse_candidates_csv_to_forward_signals,
    create_forward_testing_workbook,
    SCHEMA_VERSION,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Phase 18: Export Screener Candidates into Google Sheets Forward-Testing System."
    )
    parser.add_argument(
        "--candidates-path",
        type=str,
        default="data/research_results/20260824/candidates.csv",
        help="Path to candidates.csv from production screening run.",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="data/forward_testing",
        help="Output directory for forward-testing artifacts (default: data/forward_testing).",
    )
    parser.add_argument(
        "--run-id",
        type=str,
        default="20260824_1530",
        help="Unique identifier for the screening run snapshot (default: 20260824_1530).",
    )

    args = parser.parse_args()

    candidates_file = Path(args.candidates_path)
    if not candidates_file.exists():
        print(f"ERROR: Production candidates file not found at {candidates_file}")
        return 1

    print("=" * 80)
    print("PHASE 18 — GOOGLE SHEETS SCREENER FORWARD-TESTING EXPORT")
    print(f"Candidates Source: {candidates_file}")
    print(f"Run ID:            {args.run_id}")
    print(f"Output Directory:  {args.output_dir}")
    print(f"Schema Version:    {SCHEMA_VERSION}")
    print("=" * 80)

    # 1. Load candidates
    raw_df = pd.read_csv(candidates_file)
    print(f"Loaded {len(raw_df)} candidates from production run.")
    hp_count = len(raw_df[raw_df["candidate_category"] == "HIGH_PRIORITY_CANDIDATE"])
    q_count = len(raw_df[raw_df["candidate_category"] == "QUALIFIED_CANDIDATE"])
    print(f"-> High Priority Candidates: {hp_count}")
    print(f"-> Qualified Candidates:     {q_count}")

    # 2. Parse to immutable ForwardSignals
    signals = parse_candidates_csv_to_forward_signals(raw_df, run_id=args.run_id)
    print(f"Parsed {len(signals)} immutable forward signals.")

    # 3. Create Google Sheets master workbook and CSV exports
    xlsx_path = create_forward_testing_workbook(
        signals=signals,
        trade_results=None,
        output_dir=args.output_dir,
        template_filename="SLA_Wyckoff_Forward_Testing_Template.xlsx",
    )

    out_dir = Path(args.output_dir)
    csv_path = out_dir / "screener_candidates.csv"
    xlsx_c_path = out_dir / "screener_candidates.xlsx"

    print("\n" + "=" * 80)
    print("FORWARD-TESTING EXPORTS GENERATED SUCCESSFULLY:")
    print("=" * 80)
    print(f"1. Master 7-Tab Google Sheets Template: {xlsx_path} ({xlsx_path.stat().st_size:,} bytes)")
    print(f"2. Flat Candidate CSV Export:          {csv_path} ({csv_path.stat().st_size:,} bytes)")
    print(f"3. Flat Candidate XLSX Export:         {xlsx_c_path} ({xlsx_c_path.stat().st_size:,} bytes)")
    print(f"Total Candidate Signals Exported:      {len(signals)}")
    print(f"High Priority Count:                   {hp_count}")
    print(f"Qualified Count:                       {q_count}")
    print("=" * 80)

    return 0


if __name__ == "__main__":
    sys.exit(main())
