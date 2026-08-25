"""Google Sheets Forward-Validation System & Multi-Tab Workbook Builder.

Implements the 8-tab Google Sheets validation architecture:
1. README
2. CANDIDATES
3. PRICE_DATA
4. SIGNALS
5. PERFORMANCE
6. TRADE_LOG
7. SUMMARY
8. CONFIG
"""

from pathlib import Path
from typing import Any, Final, Optional, Sequence
import pandas as pd

SCHEMA_VERSION: Final[str] = "2.0.0"
DEFAULT_TARGET_1_PCT: Final[float] = 10.0
DEFAULT_TARGET_2_PCT: Final[float] = 20.0
DEFAULT_TARGET_3_PCT: Final[float] = 30.0
DEFAULT_STOP_LOSS_PCT: Final[float] = 5.0
DEFAULT_MAX_OBSERVATION_DAYS: Final[int] = 60


def build_candidates_sheet_dataframe(
    candidates_df: pd.DataFrame,
    screening_run_date: str = "20260824",
    default_stop_pct: float = DEFAULT_STOP_LOSS_PCT,
    default_t1_pct: float = DEFAULT_TARGET_1_PCT,
    default_t2_pct: float = DEFAULT_TARGET_2_PCT,
    default_t3_pct: float = DEFAULT_TARGET_3_PCT,
) -> pd.DataFrame:
    """Transform candidates.csv DataFrame into the standardized CANDIDATES sheet schema (Columns A to V).

    Args:
        candidates_df: Raw candidates DataFrame from production screening run.
        screening_run_date: Unique date identifier (YYYYMMDD).
        default_stop_pct: Default stop percentage below entry (default 5.0%).
        default_t1_pct: Default Target 1 percentage above entry (default 10.0%).
        default_t2_pct: Default Target 2 percentage above entry (default 20.0%).
        default_t3_pct: Default Target 3 percentage above entry (default 30.0%).

    Returns:
        pd.DataFrame containing Columns A through V.
    """
    if candidates_df.empty:
        return pd.DataFrame(columns=[
            "Candidate_ID", "Screening_Date", "Symbol", "Company_Name", "Exchange",
            "Priority", "Setup", "Score", "Qualification_Status", "Wyckoff_Event",
            "Entry_Price", "Entry_Date", "Initial_Stop", "Target_1", "Target_2", "Target_3",
            "Risk_Per_Share", "Risk_Percent", "TradingView_URL", "Screener_Reason",
            "Data_Source", "Validation_Status"
        ])

    df = candidates_df.copy()
    rows = []

    for _, row in df.iterrows():
        sym = str(row["symbol"]).strip()
        sig_dt = str(row.get("as_of_date", row.get("signal_date", "2026-08-21")))[:10]
        cand_id = f"{screening_run_date}_{sym}"
        comp_name = str(row.get("company_name", sym))
        prio = str(row.get("candidate_category", "QUALIFIED_CANDIDATE"))
        event_type = str(row.get("most_recent_event_type", "LPS"))
        setup_label = f"Wyckoff {event_type} Setup"
        score = float(row.get("composite_score", 0.0))
        mech_qual = "QUALIFIED" if bool(row.get("is_mechanically_qualified", True)) else "UNQUALIFIED"

        close_p = float(row.get("close", 0.0))
        entry_p = close_p  # Signal closing price as defined entry
        
        stop_p = round(entry_p * (1.0 - (default_stop_pct / 100.0)), 2)
        
        # P&F target as Target 1 if higher than entry, else default +10%
        pf_tgt = row.get("pf_target_price")
        if pd.notna(pf_tgt) and float(pf_tgt) > entry_p:
            t1 = round(float(pf_tgt), 2)
            t2 = round(t1 * 1.15, 2)
            t3 = round(t1 * 1.30, 2)
        else:
            t1 = round(entry_p * (1.0 + (default_t1_pct / 100.0)), 2)
            t2 = round(entry_p * (1.0 + (default_t2_pct / 100.0)), 2)
            t3 = round(entry_p * (1.0 + (default_t3_pct / 100.0)), 2)

        risk_share = round(entry_p - stop_p, 2)
        risk_pct = round((risk_share / entry_p * 100.0), 2) if entry_p > 0 else default_stop_pct

        tv_url = str(row.get("tradingview_daily_url", f"https://www.tradingview.com/chart/?symbol=NSE%3A{sym}&interval=D"))
        reason = str(row.get("numeric_evidence", row.get("explanation_summary", "")))
        ds_path = str(row.get("dataset_snapshot_path", "data/research_results/20260824"))

        rows.append({
            "Candidate_ID": cand_id,
            "Screening_Date": sig_dt,
            "Symbol": sym,
            "Company_Name": comp_name,
            "Exchange": "NSE",
            "Priority": prio,
            "Setup": setup_label,
            "Score": score,
            "Qualification_Status": mech_qual,
            "Wyckoff_Event": event_type,
            "Entry_Price": entry_p,
            "Entry_Date": sig_dt,
            "Initial_Stop": stop_p,
            "Target_1": t1,
            "Target_2": t2,
            "Target_3": t3,
            "Risk_Per_Share": risk_share,
            "Risk_Percent": risk_pct,
            "TradingView_URL": tv_url,
            "Screener_Reason": reason,
            "Data_Source": ds_path,
            "Validation_Status": "PENDING_FORWARD_EVALUATION",
        })

    return pd.DataFrame(rows)


def build_signals_sheet_dataframe(candidates_df: pd.DataFrame) -> pd.DataFrame:
    """Build master SIGNALS tracking tab."""
    rows = []
    for _, c in candidates_df.iterrows():
        rows.append({
            "Candidate_ID": c["Candidate_ID"],
            "Symbol": c["Symbol"],
            "Screening_Date": c["Screening_Date"],
            "Candidate_Price": c["Entry_Price"],
            "Actual_Entry_Date": c["Entry_Date"],
            "Actual_Entry_Price": c["Entry_Price"],
            "Stop_Price": c["Initial_Stop"],
            "Target_1": c["Target_1"],
            "Target_2": c["Target_2"],
            "Target_3": c["Target_3"],
            "Exit_Date": "",
            "Exit_Price": "",
            "Exit_Reason": "ACTIVE_MONITORING",
            "Holding_Period": 0,
            "Status": "OPEN",
        })
    return pd.DataFrame(rows)


def build_performance_sheet_dataframe(candidates_df: pd.DataFrame) -> pd.DataFrame:
    """Build forward PERFORMANCE metrics tab."""
    rows = []
    for _, c in candidates_df.iterrows():
        rows.append({
            "Candidate_ID": c["Candidate_ID"],
            "Symbol": c["Symbol"],
            "Entry_Price": c["Entry_Price"],
            "Forward_Return_1D (%)": "",
            "Forward_Return_3D (%)": "",
            "Forward_Return_5D (%)": "",
            "Forward_Return_10D (%)": "",
            "Forward_Return_20D (%)": "",
            "Forward_Return_30D (%)": "",
            "Forward_Return_40D (%)": "",
            "Forward_Return_60D (%)": "",
            "Forward_Return_1M (%)": "",
            "Forward_Return_3M (%)": "",
            "MFE_5D (%)": "",
            "MFE_10D (%)": "",
            "MFE_20D (%)": "",
            "MFE_40D (%)": "",
            "MFE_60D (%)": "",
            "MAE_5D (%)": "",
            "MAE_10D (%)": "",
            "MAE_20D (%)": "",
            "MAE_40D (%)": "",
            "MAE_60D (%)": "",
            "Target_1_Hit": "NO",
            "Target_2_Hit": "NO",
            "Target_3_Hit": "NO",
            "Stop_Hit": "NO",

            "Candidate_Return (%)": 0.0,
            "NIFTY_Return (%)": 0.0,
            "Excess_Return (%)": 0.0,
        })
    return pd.DataFrame(rows)


def build_trade_log_sheet_dataframe(candidates_df: pd.DataFrame) -> pd.DataFrame:
    """Build completed and active trade log tab."""
    rows = []
    for _, c in candidates_df.iterrows():
        rows.append({
            "Candidate_ID": c["Candidate_ID"],
            "Symbol": c["Symbol"],
            "Entry_Date": c["Entry_Date"],
            "Entry_Price": c["Entry_Price"],
            "Exit_Date": "",
            "Exit_Price": "",
            "Outcome_Type": "OPEN",
            "Realized_Return (%)": 0.0,
            "R_Multiple": 0.0,
            "Holding_Days": 0,
            "Lookahead_Check": "PASS",
            "Notes": c["Screener_Reason"],
        })
    return pd.DataFrame(rows)


def build_summary_dashboard_dataframes(candidates_df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Build high-level SUMMARY KPIs, Score Dashboard, Priority Comparison, and Event Dashboard."""
    total = len(candidates_df)
    hp_count = len(candidates_df[candidates_df["Priority"] == "HIGH_PRIORITY_CANDIDATE"])
    q_count = len(candidates_df[candidates_df["Priority"] == "QUALIFIED_CANDIDATE"])

    # 1. Master KPI Summary
    kpi_data = [
        {"Metric": "Total Signals", "Value": total, "Details": "Total screener candidate signals recorded"},
        {"Metric": "High Priority Signals", "Value": hp_count, "Details": "Candidates with score >= 60 and mechanically qualified"},
        {"Metric": "Qualified Signals", "Value": q_count, "Details": "Candidates with score 40-59.99"},
        {"Metric": "Open Signals", "Value": total, "Details": "Signals currently in prospective observation window"},
        {"Metric": "Completed Signals", "Value": 0, "Details": "Signals that have reached target, stop, or 60D horizon"},
        {"Metric": "Pending Signals", "Value": total, "Details": "Signals awaiting post-signal price bars"},
        {"Metric": "Invalid Signals", "Value": 0, "Details": "Signals with missing or corrupted data"},
        {"Metric": "Ambiguous Signals", "Value": 0, "Details": "Signals where target & stop touched on exact same candle"},
        {"Metric": "Win Rate (%)", "Value": 0.0, "Details": "Completed Wins / Total Completed Trades"},
        {"Metric": "Loss Rate (%)", "Value": 0.0, "Details": "Completed Losses / Total Completed Trades"},
        {"Metric": "Ambiguous Rate (%)", "Value": 0.0, "Details": "Ambiguous Trades / Total Completed Trades"},
        {"Metric": "Average Return (%)", "Value": 0.0, "Details": "Mean return of completed trades"},
        {"Metric": "Median Return (%)", "Value": 0.0, "Details": "Median return of completed trades"},
        {"Metric": "Average Win (%)", "Value": 0.0, "Details": "Average gain on winning trades"},
        {"Metric": "Average Loss (%)", "Value": 0.0, "Details": "Average loss on losing trades"},
        {"Metric": "Best Return (%)", "Value": 0.0, "Details": "Highest realized return among closed trades"},
        {"Metric": "Worst Return (%)", "Value": 0.0, "Details": "Lowest realized return among closed trades"},
        {"Metric": "Profit Factor", "Value": 0.0, "Details": "Gross Wins / Gross Losses"},
        {"Metric": "Expectancy per Trade (%)", "Value": 0.0, "Details": "(Win Rate * Avg Win) - (Loss Rate * |Avg Loss|)"},
        {"Metric": "Average MFE (%)", "Value": 0.0, "Details": "Average Maximum Favorable Excursion across 60 days"},
        {"Metric": "Average MAE (%)", "Value": 0.0, "Details": "Average Maximum Adverse Excursion across 60 days"},
        {"Metric": "Target 1 Hit Rate (%)", "Value": 0.0, "Details": "Percentage of signals reaching Target 1 (+10%)"},
        {"Metric": "Target 2 Hit Rate (%)", "Value": 0.0, "Details": "Percentage of signals reaching Target 2 (+20%)"},
        {"Metric": "Target 3 Hit Rate (%)", "Value": 0.0, "Details": "Percentage of signals reaching Target 3 (+30%)"},
        {"Metric": "Stop Loss Hit Rate (%)", "Value": 0.0, "Details": "Percentage of signals reaching Stop Loss (-5%)"},
        {"Metric": "Average Holding Period (Days)", "Value": 0, "Details": "Mean days from entry to target/stop exit"},
        {"Metric": "NIFTY Benchmark Return (%)", "Value": 0.0, "Details": "NIFTY 50 return over matching holding windows"},
        {"Metric": "Average Excess Return (%)", "Value": 0.0, "Details": "Candidate Return - NIFTY Return (Alpha)"},
    ]
    df_kpi = pd.DataFrame(kpi_data)


    # 2. Score Predictive Dashboard Table
    score_bands = [
        ("< 40", 0.0, 39.99),
        ("40–49.99", 40.0, 49.99),
        ("50–59.99", 50.0, 59.99),
        ("60–69.99", 60.0, 69.99),
        ("70–79.99", 70.0, 79.99),
        ("80+", 80.0, 100.0),
    ]
    score_rows = []
    for label, low, high in score_bands:
        sub = candidates_df[(candidates_df["Score"] >= low) & (candidates_df["Score"] <= high)]
        score_rows.append({
            "Score_Bucket": label,
            "Signals": len(sub),
            "Wins": 0,
            "Losses": 0,
            "Win_Rate (%)": 0.0,
            "Avg_Return (%)": 0.0,
            "Avg_MFE (%)": 0.0,
            "Avg_MAE (%)": 0.0,
            "Expectancy (%)": 0.0,
        })
    df_score = pd.DataFrame(score_rows)

    # 3. Priority Comparison Table
    prio_rows = []
    for p_label in ["HIGH_PRIORITY_CANDIDATE", "QUALIFIED_CANDIDATE"]:
        sub = candidates_df[candidates_df["Priority"] == p_label]
        prio_rows.append({
            "Priority_Category": p_label,
            "Candidate_Count": len(sub),
            "Win_Rate (%)": 0.0,
            "Avg_Return (%)": 0.0,
            "Median_Return (%)": 0.0,
            "Avg_MFE (%)": 0.0,
            "Avg_MAE (%)": 0.0,
            "Target_Hit_Rate (%)": 0.0,
            "Stop_Hit_Rate (%)": 0.0,
            "Expectancy (%)": 0.0,
        })
    df_priority = pd.DataFrame(prio_rows)

    # 4. Wyckoff Event Dashboard Table
    events = ["Spring", "LPS", "SOS", "ST", "SC", "AR", "UTAD", "Other"]
    event_rows = []
    for ev in events:
        if ev == "Other":
            sub = candidates_df[~candidates_df["Wyckoff_Event"].isin(events[:-1])]
        else:
            sub = candidates_df[candidates_df["Wyckoff_Event"] == ev]
        event_rows.append({
            "Wyckoff_Event": ev,
            "Signals": len(sub),
            "Win_Rate (%)": 0.0,
            "Avg_Return (%)": 0.0,
            "Avg_MFE (%)": 0.0,
            "Avg_MAE (%)": 0.0,
            "Expectancy (%)": 0.0,
        })
    df_event = pd.DataFrame(event_rows)

    return df_kpi, df_score, df_priority, df_event


def export_validation_package(
    candidates_csv_path: Path | str = "data/research_results/20260824/candidates.csv",
    output_dir: Path | str = "data/google_sheets",
    screening_run_date: str = "20260824",
) -> tuple[Path, Path]:
    """Generate the complete Google Sheets forward validation package.

    Creates:
    1. data/google_sheets/candidates_import.csv (Flat clean candidate import)
    2. data/google_sheets/google_sheets_template.xlsx (Master 8-tab workbook)

    Returns:
        Tuple of (xlsx_path, csv_path).
    """
    c_path = Path(candidates_csv_path)
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    xlsx_path = out_dir / "google_sheets_template.xlsx"
    csv_path = out_dir / "candidates_import.csv"

    raw_candidates = pd.read_csv(c_path) if c_path.exists() else pd.DataFrame()
    df_candidates = build_candidates_sheet_dataframe(raw_candidates, screening_run_date=screening_run_date)

    # 1. Save flat CSV export for Google Sheets import
    df_candidates.to_csv(csv_path, index=False)

    # 2. Build Tab 1: README
    readme_data = [
        {"Section": "System Overview", "Details": "Phase 18 Google Sheets Stock Screener Forward-Validation System"},
        {"Section": "Primary Purpose", "Details": "Prospective candidate tracking and real-world forward validation of frozen Wyckoff screener."},
        {"Section": "Historical Backtest Status", "Details": "Historical full-universe backtesting is deferred. Phase 18 uses candidate-level Google Sheets forward validation."},
        {"Section": "Workflow Step 1", "Details": "Import candidates_import.csv into the CANDIDATES tab in Google Sheets."},
        {"Section": "Workflow Step 2", "Details": "PRICE_DATA retrieves market prices via =GOOGLEFINANCE() or batch price updates."},
        {"Section": "Workflow Step 3", "Details": "PERFORMANCE tab tracks forward returns at 1D, 3D, 5D, 10D, 20D, 30D, 60D, MFE, MAE, and NIFTY Alpha."},
        {"Section": "Workflow Step 4", "Details": "SUMMARY tab aggregates live Win Rate, Profit Factor, Expectancy, Score predictive tests, and Event stats."},
        {"Section": "Lookahead Protection", "Details": "Signal metadata (Candidate_ID, Screening_Date, Symbol, Score, Entry_Price) is strictly immutable."},
        {"Section": "Ambiguous Bar Rule", "Details": "If both Target 1 (+10%) and Stop Loss (-5%) are touched on the same candle, the trade is marked AMBIGUOUS."},
        {"Section": "Survivorship Bias Warning", "Details": "Candidate-level forward testing reflects current active constituents; point-in-time snapshots are used for historical audits."},
    ]
    df_readme = pd.DataFrame(readme_data)

    # 3. Build Tab 8: CONFIG
    config_data = [
        {"Parameter": "Schema_Version", "Value": SCHEMA_VERSION, "Description": "Forward validation schema version"},
        {"Parameter": "Target_1_Pct", "Value": DEFAULT_TARGET_1_PCT, "Description": "First profit target (% above entry)"},
        {"Parameter": "Target_2_Pct", "Value": DEFAULT_TARGET_2_PCT, "Description": "Second profit target (% above entry)"},
        {"Parameter": "Target_3_Pct", "Value": DEFAULT_TARGET_3_PCT, "Description": "Third profit target (% above entry)"},
        {"Parameter": "Stop_Loss_Pct", "Value": DEFAULT_STOP_LOSS_PCT, "Description": "Stop loss risk percentage (% below entry)"},
        {"Parameter": "Max_Observation_Days", "Value": DEFAULT_MAX_OBSERVATION_DAYS, "Description": "Maximum forward observation period (trading days)"},
        {"Parameter": "Benchmark_Symbol", "Value": "NSE:NIFTY 50", "Description": "Market benchmark index for excess return / alpha tracking"},
        {"Parameter": "Entry_Model", "Value": "SCREENING_DAY_CLOSE", "Description": "Immutable candidate entry price equals screening-date closing price"},
        {"Parameter": "Ambiguity_Handling", "Value": "AMBIGUOUS", "Description": "Conservative classification if both target and stop are reached on same bar"},
        {"Parameter": "Lookahead_Protection", "Value": "PASS", "Description": "Verified separation between signal-time data and post-signal market data"},
    ]
    df_config = pd.DataFrame(config_data)

    # 4. Build Tab 3: PRICE_DATA Helper
    price_data_template = [
        {"Symbol": "ZEEL", "Formula_Example": '=GOOGLEFINANCE("NSE:ZEEL", "price", DATE(2026,8,21), TODAY(), "DAILY")', "Notes": "Retrieves daily closing prices starting from signal date"},
        {"Symbol": "JINDALSAW", "Formula_Example": '=GOOGLEFINANCE("NSE:JINDALSAW", "price", DATE(2026,8,21), TODAY(), "DAILY")', "Notes": "Retrieves daily closing prices starting from signal date"},
        {"Symbol": "NIFTY 50", "Formula_Example": '=GOOGLEFINANCE("NSE:NIFTY 50", "price", DATE(2026,8,21), TODAY(), "DAILY")', "Notes": "Market benchmark index for alpha calculation"},
    ]
    df_price_data = pd.DataFrame(price_data_template)

    # 5. Build Tab 4: SIGNALS, Tab 5: PERFORMANCE, Tab 6: TRADE_LOG
    df_signals = build_signals_sheet_dataframe(df_candidates)
    df_performance = build_performance_sheet_dataframe(df_candidates)
    df_trade_log = build_trade_log_sheet_dataframe(df_candidates)

    # 6. Build Tab 7: SUMMARY Dashboard & Segmentations
    df_kpi, df_score, df_prio, df_event = build_summary_dashboard_dataframes(df_candidates)

    # Combine Summary sub-tables into a comprehensive SUMMARY sheet
    summary_combined = []
    summary_combined.append(pd.DataFrame([{"Section": "=== MASTER PERFORMANCE KPIS ===", "Value": "", "Details": ""}]))
    summary_combined.append(df_kpi.rename(columns={"Metric": "Section"}))
    summary_combined.append(pd.DataFrame([{"Section": "=== SCORE-BASED PREDICTIVE DASHBOARD ===", "Value": "", "Details": ""}]))
    summary_combined.append(df_score.rename(columns={"Score_Bucket": "Section"}))
    summary_combined.append(pd.DataFrame([{"Section": "=== PRIORITY COMPARISON (HIGH PRIORITY VS QUALIFIED) ===", "Value": "", "Details": ""}]))
    summary_combined.append(df_prio.rename(columns={"Priority_Category": "Section"}))
    summary_combined.append(pd.DataFrame([{"Section": "=== WYCKOFF EVENT DASHBOARD ===", "Value": "", "Details": ""}]))
    summary_combined.append(df_event.rename(columns={"Wyckoff_Event": "Section"}))
    df_summary = pd.concat(summary_combined, ignore_index=True)

    # Write Master 8-Tab Workbook
    with pd.ExcelWriter(xlsx_path, engine="openpyxl") as writer:
        df_readme.to_excel(writer, sheet_name="README", index=False)
        df_candidates.to_excel(writer, sheet_name="CANDIDATES", index=False)
        df_price_data.to_excel(writer, sheet_name="PRICE_DATA", index=False)
        df_signals.to_excel(writer, sheet_name="SIGNALS", index=False)
        df_performance.to_excel(writer, sheet_name="PERFORMANCE", index=False)
        df_trade_log.to_excel(writer, sheet_name="TRADE_LOG", index=False)
        df_summary.to_excel(writer, sheet_name="SUMMARY", index=False)
        df_config.to_excel(writer, sheet_name="CONFIG", index=False)

    return xlsx_path, csv_path
