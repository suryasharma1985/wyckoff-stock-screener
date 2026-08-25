"""Google Sheets Export Engine for Wyckoff Stock Screener Validation System.

Formats candidates produced by the Wyckoff screener and generates clean CSV exports
and multi-tab Excel workbooks formatted for Google Sheets import.
"""

from pathlib import Path
from typing import Any, Final, Optional, Sequence
import pandas as pd

SCHEMA_VERSION: Final[str] = "1.0.0"


def format_screener_candidates_for_signals_sheet(
    candidates_df: pd.DataFrame,
    default_stop_pct: float = 5.0,
    default_target_pct: float = 15.0,
) -> pd.DataFrame:
    """Format raw screener candidates DataFrame into the standardized SIGNALS sheet schema.

    Args:
        candidates_df: DataFrame from candidates.csv (e.g. from data/research_results/).
        default_stop_pct: Default stop loss percentage from entry (default 5.0%).
        default_target_pct: Default target percentage from entry if P&F unavailable (default 15.0%).

    Returns:
        pd.DataFrame formatted with exact SIGNALS sheet columns.
    """
    if candidates_df.empty:
        return pd.DataFrame(columns=[
            "Signal_ID", "Signal_Date", "Symbol", "Company", "Exchange",
            "Screener_Score", "Priority", "Wyckoff_Event", "Entry_Type",
            "Entry_Price", "Stop_Price", "Target_1", "Target_2",
            "Position_Size", "Status", "Exit_Date", "Exit_Price",
            "Return_Pct", "R_Multiple", "Days_Held", "Outcome", "Notes",
        ])

    df = candidates_df.copy()
    sig_date = df["as_of_date"].astype(str) if "as_of_date" in df.columns else df.get("signal_date", "N/A").astype(str)
    symbols = df["symbol"].astype(str)
    
    close_p = df["close"].fillna(0.0) if "close" in df.columns else df.get("latest_close", pd.Series([0.0]*len(df)))
    entry_p = close_p  # Signal Close as placeholder until T+1 Open is observed
    
    stop_p = entry_p * (1.0 - (default_stop_pct / 100.0))
    
    # Target 1: P&F target if available and higher than entry, else +15%
    pf_tgt = df.get("pf_target_price", pd.Series([None]*len(df)))
    t1_list = []
    t2_list = []
    for tgt, ep in zip(pf_tgt, entry_p):
        if pd.notna(tgt) and float(tgt) > ep:
            t1_list.append(round(float(tgt), 2))
            t2_list.append(round(float(tgt) * 1.15, 2))
        else:
            t1_list.append(round(ep * (1.0 + (default_target_pct / 100.0)), 2))
            t2_list.append(round(ep * 1.30, 2))

    signals_tab = pd.DataFrame()
    signals_tab["Signal_ID"] = symbols + "_" + sig_date
    signals_tab["Signal_Date"] = sig_date
    signals_tab["Symbol"] = symbols
    signals_tab["Company"] = df.get("company_name", symbols)
    signals_tab["Exchange"] = "NSE"
    signals_tab["Screener_Score"] = df.get("composite_score", 0.0)
    signals_tab["Priority"] = df.get("candidate_category", "QUALIFIED_CANDIDATE")
    signals_tab["Wyckoff_Event"] = df.get("most_recent_event_type", "LPS")
    signals_tab["Entry_Type"] = "NEXT_DAY_OPEN"
    signals_tab["Entry_Price"] = [round(x, 2) for x in entry_p]
    signals_tab["Stop_Price"] = [round(x, 2) for x in stop_p]
    signals_tab["Target_1"] = t1_list
    signals_tab["Target_2"] = t2_list
    signals_tab["Position_Size"] = 100
    signals_tab["Status"] = "ACTIVE"
    signals_tab["Exit_Date"] = ""
    signals_tab["Exit_Price"] = ""
    signals_tab["Return_Pct"] = ""
    signals_tab["R_Multiple"] = ""
    signals_tab["Days_Held"] = ""
    signals_tab["Outcome"] = "PENDING"
    signals_tab["Notes"] = df.get("numeric_evidence", df.get("explanation_summary", ""))

    return signals_tab


def generate_dashboard_dataframe(results_df: pd.DataFrame) -> pd.DataFrame:
    """Generate research metrics summary for DASHBOARD sheet."""
    if results_df.empty:
        return pd.DataFrame([{"Metric": "Total Signals Tested", "Value": 0}])

    wins = results_df[results_df["Outcome"] == "WIN"]
    losses = results_df[results_df["Outcome"] == "LOSS"]
    total = len(results_df)

    win_rate = (len(wins) / total * 100.0) if total > 0 else 0.0
    rets = results_df["Net_Return_Pct"].dropna()
    avg_ret = rets.mean() if not rets.empty else 0.0
    med_ret = rets.median() if not rets.empty else 0.0

    avg_win = wins["Net_Return_Pct"].mean() if not wins.empty else 0.0
    avg_loss = losses["Net_Return_Pct"].mean() if not losses.empty else 0.0

    win_sum = wins["Net_Return_Pct"].sum() if not wins.empty else 0.0
    loss_sum = abs(losses["Net_Return_Pct"].sum()) if not losses.empty else 1.0
    profit_factor = (win_sum / loss_sum) if loss_sum > 0 else 0.0

    mfe = results_df["MFE_Pct"].dropna().mean() if "MFE_Pct" in results_df.columns else 0.0
    mae = results_df["MAE_Pct"].dropna().mean() if "MAE_Pct" in results_df.columns else 0.0

    t_hit_rate = (results_df["Target_Hit"].sum() / total * 100.0) if "Target_Hit" in results_df.columns and total > 0 else 0.0
    s_hit_rate = (results_df["Stop_Hit"].sum() / total * 100.0) if "Stop_Hit" in results_df.columns and total > 0 else 0.0

    dashboard_data = [
        {"Metric": "Total Signals Tested", "Value": total, "Note": "Evaluated trade count"},
        {"Metric": "Total Wins", "Value": len(wins), "Note": "Trades with net return > 0"},
        {"Metric": "Total Losses", "Value": len(losses), "Note": "Trades with net return < 0"},
        {"Metric": "Win Rate (%)", "Value": round(win_rate, 1), "Note": "Percentage of winning trades"},
        {"Metric": "Average Net Return (%)", "Value": round(avg_ret, 2), "Note": "Mean return across all trades (0.40% friction deducted)"},
        {"Metric": "Median Net Return (%)", "Value": round(med_ret, 2), "Note": "Robust median return"},
        {"Metric": "Average Winner (%)", "Value": round(avg_win, 2), "Note": "Mean gain on winning trades"},
        {"Metric": "Average Loser (%)", "Value": round(avg_loss, 2), "Note": "Mean loss on losing trades"},
        {"Metric": "Profit Factor", "Value": round(profit_factor, 2), "Note": "Gross wins / Gross losses"},
        {"Metric": "Average MFE (%)", "Value": round(mfe, 2), "Note": "Average Maximum Favorable Excursion"},
        {"Metric": "Average MAE (%)", "Value": round(mae, 2), "Note": "Average Maximum Adverse Excursion"},
        {"Metric": "Target Hit Rate (%)", "Value": round(t_hit_rate, 1), "Note": "Percentage of trades hitting Target 1"},
        {"Metric": "Stop Hit Rate (%)", "Value": round(s_hit_rate, 1), "Note": "Percentage of trades hitting Stop Loss"},
    ]

    return pd.DataFrame(dashboard_data)


def export_signals_to_google_sheets_workbook(
    signals_df: pd.DataFrame,
    test_results_df: Optional[pd.DataFrame] = None,
    output_dir: Path | str = "data/google_sheets",
    filename: str = "phase18_google_sheets_template.xlsx",
) -> Path:
    """Export complete 6-tab Google Sheets validation workbook and CSV templates.

    Args:
        signals_df: DataFrame formatted with SIGNALS sheet schema.
        test_results_df: Optional DataFrame of evaluated outcomes for TEST_RESULTS sheet.
        output_dir: Target directory path.
        filename: Target Excel filename.

    Returns:
        Path to the generated Excel workbook.
    """
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    xlsx_path = out_dir / filename
    csv_path = out_dir / "screener_signals.csv"

    # Save flat CSV for direct copy/paste
    signals_df.to_csv(csv_path, index=False)

    # 1. SETTINGS Sheet
    settings_data = [
        {"Parameter": "Schema_Version", "Value": SCHEMA_VERSION, "Description": "Screener validation schema version"},
        {"Parameter": "Default_Stop_Pct", "Value": 5.0, "Description": "Default initial risk stop distance (% below entry)"},
        {"Parameter": "Default_Target_Pct", "Value": 15.0, "Description": "Default profit target distance (% above entry)"},
        {"Parameter": "Max_Holding_Days", "Value": 60, "Description": "Maximum holding duration before time-based exit"},
        {"Parameter": "Friction_Round_Trip_Pct", "Value": 0.40, "Description": "0.10% brokerage + 0.10% slippage each way (0.40% total)"},
        {"Parameter": "Same_Day_Ambiguity_Handling", "Value": "CONSERVATIVE", "Description": "Treatment if both High >= Target and Low <= Stop occur on same day"},
        {"Parameter": "Entry_Model", "Value": "NEXT_DAY_OPEN", "Description": "Executable entry is Next Trading Day Open (T+1 Open)"},
    ]
    df_settings = pd.DataFrame(settings_data)

    # 2. README Sheet
    readme_data = [
        {"Section": "System Overview", "Details": "Phase 18 Google Sheets Stock Screener Validation & Forward Testing Ledger"},
        {"Section": "Workflow Step 1", "Details": "Paste candidates from screener_signals.csv into SIGNALS sheet."},
        {"Section": "Workflow Step 2", "Details": "PRICE_DATA retrieves historical daily OHLC via GOOGLEFINANCE or Apps Script."},
        {"Section": "Workflow Step 3", "Details": "TEST_RESULTS records realized exits, MFE, MAE, R-multiples, and win/loss outcomes."},
        {"Section": "Workflow Step 4", "Details": "DASHBOARD displays live aggregated win rate, profit factor, score deciles, and event stats."},
        {"Section": "Entry Definition", "Details": "Entry is strictly Date T+1 Open (next market morning opening price)."},
        {"Section": "Ambiguity Rule", "Details": "If both target and stop are triggered on the same day, CONSERVATIVE mode records a stop exit."},
        {"Section": "Lookahead Protection", "Details": "Signal criteria use ONLY data <= Signal_Date; performance uses data STRICTLY > Signal_Date."},
    ]
    df_readme = pd.DataFrame(readme_data)

    # 3. PRICE_DATA Sheet (Formula Helper / Template)
    price_data_template = [
        {"Symbol": "RELIANCE", "Formula_Example": '=GOOGLEFINANCE("NSE:RELIANCE", "all", DATE(2024,1,1), DATE(2024,6,30), "DAILY")', "Notes": "Returns Date, Open, High, Low, Close, Volume"},
        {"Symbol": "TCS", "Formula_Example": '=GOOGLEFINANCE("NSE:TCS", "all", DATE(2024,1,1), DATE(2024,6,30), "DAILY")', "Notes": "Daily candle history for post-signal evaluation"},
    ]
    df_price_data = pd.DataFrame(price_data_template)

    # 4. TEST_RESULTS Sheet
    if test_results_df is not None and not test_results_df.empty:
        df_results = test_results_df
    else:
        df_results = pd.DataFrame(columns=[
            "Signal_ID", "Symbol", "Signal_Date", "Entry_Date", "Entry_Price",
            "Stop_Price", "Target_Price", "Risk_Per_Share", "Initial_Risk_Pct",
            "Exit_Date", "Exit_Price", "Exit_Reason", "Holding_Days",
            "Net_Return_Pct", "R_Multiple", "Outcome", "MFE_Pct", "MAE_Pct",
            "5D_Return", "10D_Return", "20D_Return", "30D_Return", "60D_Return",
            "Target_Hit", "Stop_Hit", "Target_Before_Stop", "Stop_Before_Target",
            "Ambiguous_Same_Day", "Days_To_Target", "Days_To_Stop",
        ])

    # 5. DASHBOARD Sheet
    df_dashboard = generate_dashboard_dataframe(df_results)

    # Write multi-tab workbook
    with pd.ExcelWriter(xlsx_path, engine="openpyxl") as writer:
        df_readme.to_excel(writer, sheet_name="README", index=False)
        signals_df.to_excel(writer, sheet_name="SIGNALS", index=False)
        df_price_data.to_excel(writer, sheet_name="PRICE_DATA", index=False)
        df_results.to_excel(writer, sheet_name="TEST_RESULTS", index=False)
        df_dashboard.to_excel(writer, sheet_name="DASHBOARD", index=False)
        df_settings.to_excel(writer, sheet_name="SETTINGS", index=False)

    return xlsx_path
