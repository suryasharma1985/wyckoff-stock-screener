"""Command-line interface for Phase 11 Live / Paper Forward Validation."""

import argparse
from datetime import datetime, timezone
import json
import logging
from pathlib import Path
import sys
import tempfile
from typing import Optional
import numpy as np
import pandas as pd

from wyckoff_screener.forward.ledger import (
    DEFAULT_FORWARD_BASE_DIR,
    DuplicateScreeningDateError,
    ForwardLedger,
)
from wyckoff_screener.forward.models import (
    FORWARD_ENGINE_VERSION,
    ForwardCandidateRecord,
    HorizonStatus,
)
from wyckoff_screener.forward.tracker import update_all_forward_outcomes
from wyckoff_screener.research.screening_engine import (
    DEFAULT_HIGH_PRIORITY_THRESHOLD,
    DEFAULT_QUALIFIED_THRESHOLD,
    DEFAULT_WATCHLIST_THRESHOLD,
    run_research_screening,
)
from wyckoff_screener.scanning.broad_filter import DEFAULT_MIN_AVG_TURNOVER_CR

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def _locate_latest_dataset() -> Path:
    """Locate the most recent canonical research dataset."""
    base_ds = Path("data/research_datasets")
    if base_ds.exists():
        subdirs = sorted([d for d in base_ds.iterdir() if d.is_dir() and (d / "symbols.csv").exists()])
        if subdirs:
            return subdirs[-1]
    raise FileNotFoundError("No valid Phase 9B research datasets found in data/research_datasets.")


def handle_screen(args: argparse.Namespace) -> None:
    """Execute prospective screening at date T and freeze immutable candidate snapshot."""
    target_date_str = str(args.date).strip()
    try:
        # Validate date format YYYY-MM-DD
        datetime.strptime(target_date_str, "%Y-%m-%d")
    except ValueError:
        print(f"ERROR: Invalid date format '{target_date_str}'. Expected YYYY-MM-DD.", file=sys.stderr)
        sys.exit(1)

    ds_dir = Path(args.dataset_dir) if args.dataset_dir else _locate_latest_dataset()
    ledger = ForwardLedger(base_dir=args.forward_dir)

    # Check duplicate protection early
    if ledger.snapshot_exists(target_date_str) and not args.overwrite:
        print(
            f"ERROR: Immutable snapshot already exists for {target_date_str} at {ledger.get_snapshot_path(target_date_str)}.\n"
            f"To deliberately re-screen and overwrite, pass the --overwrite flag.",
            file=sys.stderr,
        )
        sys.exit(1)

    print("=" * 90)
    print("WYCKOFF & VSA FORWARD VALIDATION — PROSPECTIVE SCREENING")
    print(f"Screening Date (T): {target_date_str}")
    print(f"Source Dataset:     {ds_dir}")
    print(f"Forward Base Dir:   {args.forward_dir}")
    print("=" * 90)

    # Prepare point-in-time sliced dataset (only bars <= target_date)
    symbols_csv = ds_dir / "symbols.csv"
    data_dir = ds_dir / "data"

    if not symbols_csv.exists() or not data_dir.exists():
        print(f"ERROR: Required dataset structure missing in {ds_dir}", file=sys.stderr)
        sys.exit(1)

    with tempfile.TemporaryDirectory(prefix=f"wyckoff_fwd_pit_{target_date_str}_") as tmp_dir_str:
        tmp_dir = Path(tmp_dir_str)
        tmp_data_dir = tmp_dir / "data"
        tmp_data_dir.mkdir(parents=True, exist_ok=True)

        # Copy symbols.csv
        df_symbols = pd.read_csv(symbols_csv)
        df_symbols.to_csv(tmp_dir / "symbols.csv", index=False)

        # Copy and slice each security's OHLCV strictly <= target_date
        sliced_count = 0
        for _, row in df_symbols.iterrows():
            sym = str(row.get("symbol", "")).strip().upper()
            yf_ticker = str(row.get("yfinance_ticker", f"{sym}.NS")).strip().upper()
            if not yf_ticker.endswith(".NS"):
                yf_ticker = f"{yf_ticker}.NS"
            csv_path = data_dir / f"{yf_ticker}.csv"
            if csv_path.exists():
                df_bar = pd.read_csv(csv_path)
                df_bar["Date_str"] = pd.to_datetime(df_bar["Date"]).dt.strftime("%Y-%m-%d")
                df_pit = df_bar[df_bar["Date_str"] <= target_date_str].drop(columns=["Date_str"])
                if len(df_pit) >= 50:  # Minimum bars for indicator calculation
                    df_pit.to_csv(tmp_data_dir / f"{yf_ticker}.csv", index=False)
                    sliced_count += 1

        print(f"Point-in-time dataset prepared: {sliced_count} securities with data <= {target_date_str}")

        # Run frozen research screening engine on the strictly isolated dataset
        screening_res = run_research_screening(
            dataset_dir=tmp_dir,
            output_base_dir=tmp_dir / "screening_out",
            custom_date_tag=target_date_str.replace("-", ""),
            min_avg_turnover_cr=args.min_turnover_cr,
            high_priority_score_threshold=args.high_priority_threshold,
            qualified_score_threshold=args.qualified_threshold,
            watchlist_score_threshold=args.watchlist_threshold,
            max_workers=4,
        )

    # Convert results into immutable ForwardCandidateRecord items
    forward_records: list[ForwardCandidateRecord] = []
    for cand in screening_res.candidates_df.to_dict(orient="records"):
        pass

    for cand_obj in screening_res.manifest.candidate_records if hasattr(screening_res.manifest, "candidate_records") else []:
        pass

    # Reconstruct from successful candidate result objects
    # Note: run_research_screening produces all_results_df
    # We load candidate records directly from screening_engine
    all_cand_records: list[ForwardCandidateRecord] = []
    for _, row in screening_res.all_results_df.iterrows():
        sym = str(row["symbol"]).strip().upper()
        ref_price = float(row.get("filter_values_close", row.get("close", 0.0)))
        if ref_price == 0.0 and "filter_values" in row:
            try:
                fv = json.loads(str(row["filter_values"]).replace("'", '"'))
                ref_price = float(fv.get("close", 0.0))
            except Exception:
                ref_price = 0.0

        cand_id = row.get("candidate_id")
        if not cand_id or pd.isna(cand_id):
            cand_id = f"{sym}_{target_date_str}_{ref_price:.4f}_{FORWARD_ENGINE_VERSION}"
            cand_id = cand_id[:16]

        rec = ForwardCandidateRecord(
            candidate_id=str(cand_id),
            screening_date=target_date_str,
            symbol=sym,
            yfinance_ticker=str(row.get("yfinance_ticker", f"{sym}.NS")),
            company_name=str(row.get("company_name", sym)),
            reference_close_price=ref_price,
            data_bars=int(row.get("data_bars", 0)),
            candidate_category=str(row.get("candidate_category", "NO_SETUP")),
            composite_score=float(row.get("composite_score", 0.0)),
            is_mechanically_qualified=bool(row.get("is_mechanically_qualified", False)),
            is_disqualified=bool(row.get("is_disqualified", False)),
            disqualifying_flags=str(row.get("disqualifying_flags", "None")),
            weekly_uptrend=bool(row.get("weekly_uptrend", False)),
            dma_50_above_100=bool(row.get("dma_50_above_100", False)),
            rsi_in_band=bool(row.get("rsi_in_band", False)),
            atr_contracting=bool(row.get("atr_contracting", False)),
            vcp_bbw_contracting=bool(row.get("vcp_bbw_contracting", False)),
            vsa_volume_ratio=float(row.get("vsa_volume_ratio", 1.0)),
            vsa_spread_ratio=float(row.get("vsa_spread_ratio", 1.0)),
            vsa_close_position=float(row.get("vsa_close_position", 0.5)),
            is_stopping_volume=bool(row.get("is_stopping_volume", False)),
            is_no_demand=bool(row.get("is_no_demand", False)),
            is_no_supply=bool(row.get("is_no_supply", False)),
            is_effort_vs_result=bool(row.get("is_effort_vs_result", False)),
            most_recent_event_type=str(row.get("most_recent_event_type", "None")),
            most_recent_event_date=str(row.get("most_recent_event_date", "None")),
            possible_LPS=bool(row.get("possible_LPS", False)),
            possible_SOS=bool(row.get("possible_SOS", False)),
            possible_Spring=bool(row.get("possible_Spring", False)),
            is_UTAD_warning=bool(row.get("is_UTAD_warning", False)),
            numeric_evidence=str(row.get("numeric_evidence", "None")),
            pf_target_price=float(row["pf_target_price"]) if pd.notna(row.get("pf_target_price")) else None,
            pf_upside_pct=float(row["pf_upside_pct"]) if pd.notna(row.get("pf_upside_pct")) else None,
            pf_count_columns=int(row["pf_count_columns"]) if pd.notna(row.get("pf_count_columns")) else None,
            pf_is_stale_anchor=bool(row.get("pf_is_stale_anchor", False)),
            explanation_summary=str(row.get("explanation_summary", "")),
            tradingview_daily_url=str(row.get("tradingview_daily_url", "")),
            tradingview_weekly_url=str(row.get("tradingview_weekly_url", "")),
            tradingview_75m_url=str(row.get("tradingview_75m_url", "")),
            engine_version=FORWARD_ENGINE_VERSION,
            created_at_utc=datetime.now(timezone.utc).isoformat(),
        )
        all_cand_records.append(rec)

    # Save to immutable snapshot and sync ledger
    manifest = ledger.save_screening_snapshot(
        screening_date=target_date_str,
        candidate_records=all_cand_records,
        source_description=f"Phase 11 Forward Screening on {ds_dir.name} (<= {target_date_str})",
        overwrite=args.overwrite,
    )

    print("\n" + "=" * 90)
    print("PROSPECTIVE SCREENING SNAPSHOT FROZEN")
    print(f"Snapshot ID:      {manifest.snapshot_id}")
    print(f"Total Candidates: {manifest.total_candidates}")
    print(f"Category Counts:  {manifest.category_counts}")
    print(f"Snapshot Path:    {ledger.get_snapshot_path(target_date_str)}")
    print("=" * 90)


def handle_update(args: argparse.Namespace) -> None:
    """Scan forward ledger and update matured outcomes from latest market data."""
    ds_dir = Path(args.dataset_dir) if args.dataset_dir else _locate_latest_dataset()
    data_dir = ds_dir / "data"
    ledger = ForwardLedger(base_dir=args.forward_dir)

    print("=" * 90)
    print("WYCKOFF & VSA FORWARD VALIDATION — OUTCOME TRACKER UPDATE")
    print(f"Data Directory:   {data_dir}")
    print(f"Forward Base Dir: {args.forward_dir}")
    print("=" * 90)

    total_proc, total_matured = update_all_forward_outcomes(ledger=ledger, data_dir=data_dir)

    print("\n" + "=" * 90)
    print("FORWARD OUTCOME TRACKING UPDATE COMPLETED")
    print(f"Total Candidates Processed: {total_proc}")
    print(f"Total Matured Horizons:     {total_matured}")
    print(f"Outcomes Ledger Path:       {ledger.outcomes_csv_path}")
    print("=" * 90)


def handle_report(args: argparse.Namespace) -> None:
    """Generate and display cumulative forward validation report."""
    ledger = ForwardLedger(base_dir=args.forward_dir)
    outcomes_df = ledger.load_outcomes_dataframe()

    if outcomes_df.empty:
        print("No forward validation records found in ledger. Run 'screen' first.")
        return

    print("=" * 90)
    print("WYCKOFF & VSA PROSPECTIVE FORWARD VALIDATION REPORT")
    print(f"Ledger Path: {ledger.outcomes_csv_path}")
    print(f"Total Candidate Records: {len(outcomes_df)}")
    print("=" * 90)

    # Status distribution
    print("\n--- Horizon Maturity Status ---")
    for h in [10, 20, 60]:
        col_status = f"status_{h}d"
        if col_status in outcomes_df.columns:
            matured = (outcomes_df[col_status] == HorizonStatus.MATURED.value).sum()
            pending = (outcomes_df[col_status] == HorizonStatus.PENDING.value).sum()
            print(f"{h}-Day Horizon:  {matured:4d} Matured | {pending:4d} Pending (Total {matured + pending})")

    # Category performance for matured records
    for h in [10, 20, 60]:
        ret_col = f"fwd_ret_{h}d"
        mfe_col = f"mfe_{h}d"
        mae_col = f"mae_{h}d"
        status_col = f"status_{h}d"

        if status_col not in outcomes_df.columns or ret_col not in outcomes_df.columns:
            continue

        matured_df = outcomes_df[outcomes_df[status_col] == HorizonStatus.MATURED.value]
        if matured_df.empty:
            print(f"\n--- {h}-Day Realized Performance (No Matured Records Yet) ---")
            continue

        print(f"\n--- {h}-Day Realized Performance ({len(matured_df)} Matured Observations) ---")
        print(f"{'Category':25s} | {'N':4s} | {'Mean Ret':8s} | {'Med Ret':8s} | {'Win %':7s} | {'Mean MFE':8s} | {'Mean MAE':8s}")
        print("-" * 85)

        # Baseline
        r = matured_df[ret_col].dropna()
        mfe = matured_df[mfe_col].dropna()
        mae = matured_df[mae_col].dropna()
        if len(r) > 0:
            win = (r > 0).mean() * 100.0
            print(f"{'UNIVERSE BASELINE':25s} | {len(r):4d} | {r.mean():+7.2f}% | {r.median():+7.2f}% | {win:6.2f}% | {mfe.mean():+7.2f}% | {mae.mean():+7.2f}%")

        for cat, grp in matured_df.groupby("candidate_category"):
            r_cat = grp[ret_col].dropna()
            mfe_cat = grp[mfe_col].dropna()
            mae_cat = grp[mae_col].dropna()
            if len(r_cat) > 0:
                win_cat = (r_cat > 0).mean() * 100.0
                print(f"{cat:25s} | {len(r_cat):4d} | {r_cat.mean():+7.2f}% | {r_cat.median():+7.2f}% | {win_cat:6.2f}% | {mfe_cat.mean():+7.2f}% | {mae_cat.mean():+7.2f}%")

    print("\n" + "=" * 90)


def main() -> None:
    """Main CLI entrypoint for Phase 11 Forward Validation."""
    parser = argparse.ArgumentParser(
        description="Wyckoff & VSA Prospective Forward Validation CLI (Phase 11)"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # screen subcommand
    p_screen = subparsers.add_parser("screen", help="Run prospective screening and freeze snapshot at date T")
    p_screen.add_argument("--date", type=str, required=True, help="Screening date (YYYY-MM-DD)")
    p_screen.add_argument("--dataset-dir", type=str, default=None, help="Source research dataset directory")
    p_screen.add_argument("--forward-dir", type=str, default=DEFAULT_FORWARD_BASE_DIR, help="Forward validation base directory")
    p_screen.add_argument("--overwrite", action="store_true", help="Deliberately overwrite an existing screening snapshot")
    p_screen.add_argument("--min-turnover-cr", type=float, default=DEFAULT_MIN_AVG_TURNOVER_CR, help="Turnover filter in Cr")
    p_screen.add_argument("--high-priority-threshold", type=float, default=DEFAULT_HIGH_PRIORITY_THRESHOLD, help="High priority score")
    p_screen.add_argument("--qualified-threshold", type=float, default=DEFAULT_QUALIFIED_THRESHOLD, help="Qualified score")
    p_screen.add_argument("--watchlist-threshold", type=float, default=DEFAULT_WATCHLIST_THRESHOLD, help="Watchlist score")

    # update subcommand
    p_update = subparsers.add_parser("update", help="Update forward outcomes for open candidates from market data")
    p_update.add_argument("--dataset-dir", type=str, default=None, help="Source research dataset directory")
    p_update.add_argument("--forward-dir", type=str, default=DEFAULT_FORWARD_BASE_DIR, help="Forward validation base directory")

    # report subcommand
    p_report = subparsers.add_parser("report", help="Print cumulative forward validation report")
    p_report.add_argument("--forward-dir", type=str, default=DEFAULT_FORWARD_BASE_DIR, help="Forward validation base directory")

    args = parser.parse_args()

    if args.command == "screen":
        handle_screen(args)
    elif args.command == "update":
        handle_update(args)
    elif args.command == "report":
        handle_report(args)


if __name__ == "__main__":
    main()
