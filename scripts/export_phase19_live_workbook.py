"""CLI Exporter for Phase 19 Live Google Sheets Forward-Testing System.

Generates:
    data/google_sheets/live_forward_testing_workbook.xlsx (7 tabs: README, INPUT, LIVE_SIGNALS, MARKET_DATA, TRACKING, SUMMARY, METHODOLOGY)
"""

import argparse
from pathlib import Path
import sys

# Add src to path
_repo_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_repo_root / "src"))

from wyckoff_screener.google_sheets.phase19_live_builder import build_phase19_workbook, SCHEMA_VERSION


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Phase 19: Export Production Candidate (ZEEL) to Live Google Sheets Forward-Testing Template."
    )
    parser.add_argument(
        "--symbol",
        type=str,
        default="ZEEL",
        help="Initial demonstration candidate symbol (default: ZEEL).",
    )
    parser.add_argument(
        "--output-path",
        type=str,
        default="data/google_sheets/live_forward_testing_workbook.xlsx",
        help="Output workbook path (default: data/google_sheets/live_forward_testing_workbook.xlsx).",
    )
    parser.add_argument(
        "--candidates-path",
        type=str,
        default="data/research_results/20260824/candidates.csv",
        help="Path to candidates.csv.",
    )

    args = parser.parse_args()

    print("=" * 80)
    print("PHASE 19 — LIVE GOOGLE SHEETS FORWARD-TESTING SYSTEM BUILDER")
    print(f"Demonstration Symbol: {args.symbol}")
    print(f"Output File:          {args.output_path}")
    print(f"Schema Version:       {SCHEMA_VERSION}")
    print("=" * 80)

    out_file = build_phase19_workbook(
        output_path=args.output_path,
        initial_symbol=args.symbol,
        candidates_csv_path=args.candidates_path,
    )

    print("\n" + "=" * 80)
    print("LIVE FORWARD-TESTING WORKBOOK GENERATED SUCCESSFULLY:")
    print("=" * 80)
    print(f"1. Master 7-Tab Workbook: {out_file} ({out_file.stat().st_size:,} bytes)")
    print("Tabs Included: README, INPUT, LIVE_SIGNALS, MARKET_DATA, TRACKING, SUMMARY, METHODOLOGY")
    print("=" * 80)

    return 0


if __name__ == "__main__":
    sys.exit(main())
