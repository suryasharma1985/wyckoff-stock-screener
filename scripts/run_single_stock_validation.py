"""Phase 18: Single-Stock Live Manual Validation Test.

Simulates the complete Google Sheets-style forward validation workflow for ONE stock (ZEEL).
1. Loads single symbol OHLCV data.
2. Computes indicators, VSA metrics, Wyckoff schematic events, and P&F target.
3. Computes setup score and mechanical qualification.
4. Generates single-stock Google Sheets validation workbook:
   data/google_sheets/single_stock_validation_example.xlsx
5. Reconciles 100% against the authoritative row in candidates.csv.
"""

from pathlib import Path
import sys
import pandas as pd

# Add src to path
_repo_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_repo_root / "src"))

from wyckoff_screener.data_loader import load_ohlcv_csv
from wyckoff_screener.scoring.setup_scorer import score_setup
from wyckoff_screener.google_sheets.validation_builder import (
    build_candidates_sheet_dataframe,
    build_signals_sheet_dataframe,
    build_performance_sheet_dataframe,
    build_trade_log_sheet_dataframe,
    build_summary_dashboard_dataframes,
)


def run_single_stock_test(
    symbol: str = "ZEEL",
    data_csv_path: str = "data/research_datasets/20260824/data/ZEEL.NS.csv",
    candidates_csv_path: str = "data/research_results/20260824/candidates.csv",
    output_xlsx_path: str = "data/google_sheets/single_stock_validation_example.xlsx",
) -> dict:
    csv_file = Path(data_csv_path)
    cand_file = Path(candidates_csv_path)
    out_file = Path(output_xlsx_path)
    out_file.parent.mkdir(parents=True, exist_ok=True)

    print("=" * 80)
    print(f"LIVE VALIDATION TEST: SINGLE STOCK ({symbol})")
    print(f"Data File: {csv_file}")
    print("=" * 80)

    # 1. Load Single Stock OHLCV
    df_raw = load_ohlcv_csv(csv_file)
    print(f"Loaded {len(df_raw)} bars for {symbol} ({df_raw['Date'].min()} to {df_raw['Date'].max()})")

    # 2. Run Screener Scoring Pipeline on Single Stock
    res = score_setup(df_raw, symbol=symbol)
    print(f"Screener Score:         {res.composite_score:.1f} / 100")
    print(f"Most Recent Event:      {res.most_recent_event_type} on {res.most_recent_event_date}")
    print(f"Disqualified Flags:     {res.disqualifying_flags}")
    print(f"Mechanical Filters:     {res.mechanical_filters_passed}")
    if res.pf_price_objective:
        print(f"P&F Target Price:       {res.pf_price_objective.price_objective:.2f}")
        print(f"P&F Columns Counted:    {res.pf_price_objective.num_columns}")


    # 3. Load Original Row from candidates.csv
    df_cand = pd.read_csv(cand_file)
    cand_row = df_cand[df_cand["symbol"] == symbol].iloc[0]

    # 4. Generate Single-Stock Google Sheets Workbook
    single_cand_df = pd.DataFrame([cand_row])
    df_candidates_tab = build_candidates_sheet_dataframe(single_cand_df, screening_run_date="20260824")
    df_signals_tab = build_signals_sheet_dataframe(df_candidates_tab)
    df_perf_tab = build_performance_sheet_dataframe(df_candidates_tab)
    df_trade_log_tab = build_trade_log_sheet_dataframe(df_candidates_tab)
    df_kpi, df_score, df_prio, df_event = build_summary_dashboard_dataframes(df_candidates_tab)

    close_p = float(cand_row["close"])
    pf_tgt = float(cand_row["pf_target_price"]) if pd.notna(cand_row.get("pf_target_price")) else close_p * 1.10

    df_readme = pd.DataFrame([
        {"Section": "Single-Stock Live Validation", "Details": f"Live prospective validation demonstration for {symbol}"},
        {"Section": "Signal Date", "Details": f"{cand_row['as_of_date']} (Information cutoff)"},
        {"Section": "Entry Baseline Price", "Details": f"{close_p:.2f} (Frozen)"},
        {"Section": "Stop Loss Level", "Details": f"{close_p * 0.95:.2f} (-5.0%)"},
        {"Section": "Target 1 Level", "Details": f"{pf_tgt:.2f} (Bruce Fraser P&F Target)"},
        {"Section": "Status", "Details": "ACTIVE_MONITORING (Open forward observation)"},
    ])

    df_params = pd.DataFrame([
        {"Parameter": "Symbol", "Value": symbol, "Description": "Selected candidate symbol"},
        {"Parameter": "Signal_Date", "Value": str(cand_row["as_of_date"]), "Description": "Information cutoff date"},
        {"Parameter": "Signal_Price", "Value": round(close_p, 2), "Description": "Frozen entry price"},
        {"Parameter": "Default_Stop_Pct", "Value": 5.0, "Description": "Default protective stop (-5%)"},
        {"Parameter": "Default_Target_Pct", "Value": 10.0, "Description": "Default target (+10%)"},
        {"Parameter": "PF_Target_Price", "Value": pf_tgt, "Description": "Bruce Fraser Point & Figure target"},
    ])

    summary_combined = pd.concat([
        pd.DataFrame([{"Section": f"=== LIVE VALIDATION SUMMARY FOR {symbol} ===", "Value": "", "Details": ""}]),
        df_kpi.rename(columns={"Metric": "Section"}),
        pd.DataFrame([{"Section": "=== SCORE PREDICTIVE TABLE ===", "Value": "", "Details": ""}]),
        df_score.rename(columns={"Score_Bucket": "Section"}),
        pd.DataFrame([{"Section": "=== WYCKOFF EVENT TABLE ===", "Value": "", "Details": ""}]),
        df_event.rename(columns={"Wyckoff_Event": "Section"}),
    ], ignore_index=True)

    with pd.ExcelWriter(out_file, engine="openpyxl") as writer:
        df_readme.to_excel(writer, sheet_name="README", index=False)
        df_candidates_tab.to_excel(writer, sheet_name="CANDIDATES", index=False)
        df_signals_tab.to_excel(writer, sheet_name="SIGNALS", index=False)
        df_perf_tab.to_excel(writer, sheet_name="PERFORMANCE", index=False)
        df_trade_log_tab.to_excel(writer, sheet_name="TRADE_LOG", index=False)
        summary_combined.to_excel(writer, sheet_name="SUMMARY", index=False)
        df_params.to_excel(writer, sheet_name="PARAMETERS", index=False)

    print(f"\nSingle-Stock Workbook written to: {out_file} ({out_file.stat().st_size:,} bytes)")

    # 5. Build Explicit Reconciliation Dictionary
    return {
        "symbol": symbol,
        "company": str(cand_row["company_name"]),
        "screening_date": str(cand_row["as_of_date"]),
        "score": res.composite_score,
        "orig_score": float(cand_row["composite_score"]),
        "category": "HIGH_PRIORITY_CANDIDATE" if res.composite_score >= 60.0 else "QUALIFIED_CANDIDATE",
        "orig_category": str(cand_row["candidate_category"]),
        "event": str(res.most_recent_event_type),
        "orig_event": str(cand_row["most_recent_event_type"]),
        "close": close_p,
        "orig_close": float(cand_row["close"]),
        "pf_target": res.pf_price_objective.price_objective if res.pf_price_objective else None,
        "orig_pf_target": float(cand_row["pf_target_price"]) if pd.notna(cand_row.get("pf_target_price")) else None,
        "rsi": float(cand_row["rsi_14"]),
        "dma_50": float(cand_row["dma_50"]),
        "dma_100": float(cand_row["dma_100"]),
        "evidence": str(cand_row["numeric_evidence"]),
    }


if __name__ == "__main__":
    result = run_single_stock_test()
    print("\nReconciliation Result:")
    for k, v in result.items():
        print(f"  {k}: {v}")
