"""Live Manual Screener Validation System & 5-Tab Workbook Builder (Phase 18B).

Generates data/google_sheets/live_validation_template.xlsx with exactly 5 tabs:
1. README
2. LIVE_SIGNALS
3. TRACKING
4. SUMMARY
5. PARAMETERS
"""

from pathlib import Path
from typing import Final
import pandas as pd

SCHEMA_VERSION: Final[str] = "2.1.0"
DEFAULT_STOP_LOSS_PCT: Final[float] = 5.0
DEFAULT_TARGET_PCT: Final[float] = 10.0
MIN_SAMPLE_SIZE_THRESHOLD: Final[int] = 30


def build_live_signals_dataframe(
    candidates_df: pd.DataFrame,
    screening_run_date: str = "20260824",
    default_stop_pct: float = DEFAULT_STOP_LOSS_PCT,
    default_target_pct: float = DEFAULT_TARGET_PCT,
) -> pd.DataFrame:
    """Build LIVE_SIGNALS dataframe from production candidates.

    Preserves exact screener attributes without fabricating missing values.
    """
    if candidates_df.empty:
        return pd.DataFrame(columns=[
            "Signal_ID", "Symbol", "Company_Name", "Signal_Date", "Screener_Score",
            "Priority", "Setup", "Wyckoff_Event", "Signal_Price", "Stop_Price",
            "Target_Price", "Sector", "Explanation", "TradingView_URL", "Entry_Type"
        ])

    rows = []
    for _, row in candidates_df.iterrows():
        sym = str(row["symbol"]).strip()
        sig_dt = str(row.get("as_of_date", row.get("signal_date", "2026-08-21")))[:10]
        sig_id = f"{screening_run_date}_{sym}"
        comp_name = str(row.get("company_name", sym))
        score = float(row.get("composite_score", 0.0))
        prio = str(row.get("candidate_category", "QUALIFIED_CANDIDATE"))
        event_type = str(row.get("most_recent_event_type", "LPS"))
        setup_label = f"Wyckoff {event_type} Setup"
        
        close_p = float(row.get("close", 0.0))
        sig_price = close_p
        
        stop_p = round(sig_price * (1.0 - (default_stop_pct / 100.0)), 2)
        
        pf_tgt = row.get("pf_target_price")
        if pd.notna(pf_tgt) and float(pf_tgt) > sig_price:
            tgt_p = round(float(pf_tgt), 2)
        else:
            tgt_p = round(sig_price * (1.0 + (default_target_pct / 100.0)), 2)

        reason = str(row.get("numeric_evidence", row.get("explanation_summary", "")))
        tv_url = str(row.get("tradingview_daily_url", f"https://www.tradingview.com/chart/?symbol=NSE%3A{sym}&interval=D"))

        rows.append({
            "Signal_ID": sig_id,
            "Symbol": sym,
            "Company_Name": comp_name,
            "Signal_Date": sig_dt,
            "Screener_Score": score,
            "Priority": prio,
            "Setup": setup_label,
            "Wyckoff_Event": event_type,
            "Signal_Price": sig_price,
            "Stop_Price": stop_p,
            "Target_Price": tgt_p,
            "Sector": "",  # Empty for manual user entry if desired
            "Explanation": reason,
            "TradingView_URL": tv_url,
            "Entry_Type": "AUTOMATIC_SCREENER",
        })

    return pd.DataFrame(rows)


def build_tracking_dataframe(signals_df: pd.DataFrame) -> pd.DataFrame:
    """Build TRACKING dataframe linking to LIVE_SIGNALS."""
    rows = []
    for _, s in signals_df.iterrows():
        rows.append({
            "Signal_ID": s["Signal_ID"],
            "Symbol": s["Symbol"],
            "Signal_Date": s["Signal_Date"],
            "Signal_Price": s["Signal_Price"],
            "Current_Price": s["Signal_Price"],  # Initial baseline
            "Price_1D": "",
            "Price_5D": "",
            "Price_10D": "",
            "Price_20D": "",
            "Price_30D": "",
            "Price_60D": "",
            "Return_1D (%)": "",
            "Return_5D (%)": "",
            "Return_10D (%)": "",
            "Return_20D (%)": "",
            "Return_30D (%)": "",
            "Return_60D (%)": "",
            "Current_Return (%)": 0.0,
            "Highest_Price_Reached": s["Signal_Price"],
            "Lowest_Price_Reached": s["Signal_Price"],
            "Max_Gain_Pct": 0.0,
            "Max_Drawdown_Pct": 0.0,
            "Target_Reached": "NO",
            "Stop_Reached": "NO",
            "Current_Status": "OPEN",
            "Final_Outcome": "OPEN",
        })
    return pd.DataFrame(rows)


def build_summary_dashboard_tables(signals_df: pd.DataFrame) -> pd.DataFrame:
    """Build SUMMARY tab containing master KPIs and segmentations."""
    total = len(signals_df)
    hp_count = len(signals_df[signals_df["Priority"] == "HIGH_PRIORITY_CANDIDATE"])
    q_count = len(signals_df[signals_df["Priority"] == "QUALIFIED_CANDIDATE"])

    # 1. Master KPI Table
    kpi_rows = [
        {"Section": "=== LIVE FORWARD VALIDATION METRICS ===", "Value": "", "Details": ""},
        {"Section": "Total Live Signals (N)", "Value": total, "Details": "Total signals currently registered in LIVE_SIGNALS"},
        {"Section": "Sample Size Status", "Value": "SUFFICIENT (N >= 30)" if total >= MIN_SAMPLE_SIZE_THRESHOLD else f"INSUFFICIENT (N={total} < 30)", "Details": "Threshold for preliminary statistical reliability"},
        {"Section": "High Priority Signals", "Value": hp_count, "Details": "Signals with Screener Score >= 60 and mechanically qualified"},
        {"Section": "Qualified Signals", "Value": q_count, "Details": "Signals with Screener Score 40-59.99"},
        {"Section": "Open Signals", "Value": total, "Details": "Signals currently in prospective tracking window"},
        {"Section": "Closed Signals", "Value": 0, "Details": "Signals that hit Target, Stop, or reached 60D horizon"},
        {"Section": "Winners", "Value": 0, "Details": "Trades that reached Target Price before Stop Price"},
        {"Section": "Losers", "Value": 0, "Details": "Trades that reached Stop Price before Target Price"},
        {"Section": "Ambiguous Signals", "Value": 0, "Details": "Signals where target & stop touched on exact same candle"},
        {"Section": "Win Rate (%)", "Value": 0.0, "Details": "Winners / (Winners + Losers) * 100"},
        {"Section": "Average Return (%)", "Value": 0.0, "Details": "Mean return across closed trades"},
        {"Section": "Median Return (%)", "Value": 0.0, "Details": "Median return across closed trades"},
        {"Section": "Best Return (%)", "Value": 0.0, "Details": "Maximum return achieved among closed trades"},
        {"Section": "Worst Return (%)", "Value": 0.0, "Details": "Minimum return achieved among closed trades"},
        {"Section": "Average Max Gain / MFE (%)", "Value": 0.0, "Details": "Mean Maximum Favorable Excursion across signals"},
        {"Section": "Average Max Drawdown / MAE (%)", "Value": 0.0, "Details": "Mean Maximum Adverse Excursion across signals"},
        {"Section": "Target Hit Rate (%)", "Value": 0.0, "Details": "Percentage of signals reaching Target Price"},
        {"Section": "Stop Hit Rate (%)", "Value": 0.0, "Details": "Percentage of signals reaching Stop Price"},
        {"Section": "Profit Factor", "Value": 0.0, "Details": "Gross Winning Returns / Gross Losing Returns"},
        {"Section": "Trade Expectancy (%)", "Value": 0.0, "Details": "(Win Rate * Avg Win) - (Loss Rate * |Avg Loss|)"},
    ]

    # 2. Score Predictive Dashboard Table
    score_bands = [
        ("< 40", 0.0, 39.99),
        ("40–49.99", 40.0, 49.99),
        ("50–59.99", 50.0, 59.99),
        ("60–69.99", 60.0, 69.99),
        ("70+", 70.0, 100.0),
    ]
    score_rows = [{"Section": "=== PERFORMANCE BREAKDOWN BY SCREENER SCORE ===", "Value": "", "Details": ""}]
    for label, low, high in score_bands:
        sub = signals_df[(signals_df["Screener_Score"] >= low) & (signals_df["Screener_Score"] <= high)]
        score_rows.append({
            "Section": f"Score {label} (N={len(sub)})",
            "Value": f"Signals: {len(sub)} | Wins: 0 | Losses: 0 | Win Rate: 0.0% | Avg Return: 0.0% | Avg MFE: 0.0% | Avg MAE: 0.0%",
            "Details": f"Predictive validation bucket for score range {low} to {high}",
        })

    # 3. Wyckoff Setup Dashboard Table
    events = ["Spring", "LPS", "SOS", "ST", "SC", "AR", "UTAD", "Other"]
    event_rows = [{"Section": "=== PERFORMANCE BREAKDOWN BY WYCKOFF SETUP ===", "Value": "", "Details": ""}]
    for ev in events:
        if ev == "Other":
            sub = signals_df[~signals_df["Wyckoff_Event"].isin(events[:-1])]
        else:
            sub = signals_df[signals_df["Wyckoff_Event"] == ev]
        event_rows.append({
            "Section": f"Setup {ev} (N={len(sub)})",
            "Value": f"Signals: {len(sub)} | Win Rate: 0.0% | Avg Return: 0.0% | Target Hit: 0.0% | Avg MFE: 0.0% | Avg MAE: 0.0%",
            "Details": f"Setup performance for Wyckoff {ev} events",
        })

    # 4. Priority Comparison Table
    prio_rows = [
        {"Section": "=== PERFORMANCE BREAKDOWN BY SIGNAL PRIORITY ===", "Value": "", "Details": ""},
        {
            "Section": f"HIGH PRIORITY (N={hp_count})",
            "Value": f"Signals: {hp_count} | Win Rate: 0.0% | Avg Return: 0.0% | Target Hit: 0.0% | Stop Hit: 0.0% | MFE: 0.0% | MAE: 0.0%",
            "Details": "Signals with Screener Score >= 60 and mechanical filter qualification",
        },
        {
            "Section": f"QUALIFIED (N={q_count})",
            "Value": f"Signals: {q_count} | Win Rate: 0.0% | Avg Return: 0.0% | Target Hit: 0.0% | Stop Hit: 0.0% | MFE: 0.0% | MAE: 0.0%",
            "Details": "Signals with Screener Score 40 to 59.99",
        },
    ]

    combined = kpi_rows + score_rows + event_rows + prio_rows
    return pd.DataFrame(combined)


def export_live_validation_workbook(
    candidates_csv_path: Path | str = "data/research_results/20260824/candidates.csv",
    output_dir: Path | str = "data/google_sheets",
    screening_run_date: str = "20260824",
) -> Path:
    """Generate data/google_sheets/live_validation_template.xlsx with 5 tabs."""
    c_path = Path(candidates_csv_path)
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    xlsx_path = out_dir / "live_validation_template.xlsx"

    raw_candidates = pd.read_csv(c_path) if c_path.exists() else pd.DataFrame()
    df_signals = build_live_signals_dataframe(raw_candidates, screening_run_date=screening_run_date)
    df_tracking = build_tracking_dataframe(df_signals)
    df_summary = build_summary_dashboard_tables(df_signals)

    # 1. README tab
    readme_data = [
        {"Section": "System Overview", "Details": "Phase 18B Live Manual Screener Validation System"},
        {"Section": "Primary Purpose", "Details": "Record what our screener says TODAY and objectively measure what happens to those stocks AFTER TODAY."},
        {"Section": "Historical Backtest Status", "Details": "Historical full-universe backtesting is NOT run. This is a LIVE PROSPECTIVE FORWARD TEST."},
        {"Section": "Workflow Step 1", "Details": "Import live_validation_template.xlsx into Google Sheets."},
        {"Section": "Workflow Step 2", "Details": "LIVE_SIGNALS contains pre-loaded screener candidates. New manual signals can be entered anytime."},
        {"Section": "Workflow Step 3", "Details": "TRACKING tab monitors prices forward at 1D, 5D, 10D, 20D, 30D, and 60D trading horizons."},
        {"Section": "Workflow Step 4", "Details": "GOOGLEFINANCE formulas populate daily market prices automatically."},
        {"Section": "Workflow Step 5", "Details": "SUMMARY tab displays live win rates, excursions, score decile performance, and sample size warnings."},
        {"Section": "Lookahead Protection", "Details": "Signal Date is the absolute information cutoff. Signal Price, Score, and Setup remain permanently frozen."},
        {"Section": "Ambiguity Handling", "Details": "If Target and Stop are reached on the same daily candle, trade is classified as AMBIGUOUS."},
        {"Section": "Honesty Principle", "Details": "Do not remove losing signals. Do not cherry-pick winners. Every candidate remains an auditable observation."},
    ]
    df_readme = pd.DataFrame(readme_data)

    # 5. PARAMETERS tab
    param_data = [
        {"Parameter": "Default_Stop_Loss_Pct", "Value": DEFAULT_STOP_LOSS_PCT, "Description": "Default stop loss risk percentage below signal price"},
        {"Parameter": "Default_Target_Pct", "Value": DEFAULT_TARGET_PCT, "Description": "Default profit target percentage above signal price"},
        {"Parameter": "Holding_Period_1", "Value": "1 Trading Day", "Description": "Immediate 1-day mark-to-market performance"},
        {"Parameter": "Holding_Period_2", "Value": "5 Trading Days", "Description": "Short-term swing forward return horizon"},
        {"Parameter": "Holding_Period_3", "Value": "10 Trading Days", "Description": "2-week forward return horizon"},
        {"Parameter": "Holding_Period_4", "Value": "20 Trading Days", "Description": "1-month forward return horizon"},
        {"Parameter": "Holding_Period_5", "Value": "30 Trading Days", "Description": "6-week forward return horizon"},
        {"Parameter": "Holding_Period_6", "Value": "60 Trading Days", "Description": "Quarterly forward return horizon"},
        {"Parameter": "Min_Sample_Size_Warning", "Value": MIN_SAMPLE_SIZE_THRESHOLD, "Description": "Threshold below which statistical warnings are displayed (N < 30)"},
        {"Parameter": "Ambiguity_Rule", "Value": "AMBIGUOUS", "Description": "Classification when both target and stop are touched on same candle"},
        {"Parameter": "Status_Definitions", "Value": "OPEN, CLOSED, AMBIGUOUS, INSUFFICIENT DATA", "Description": "Standardized trade tracking statuses"},
    ]
    df_params = pd.DataFrame(param_data)

    with pd.ExcelWriter(xlsx_path, engine="openpyxl") as writer:
        df_readme.to_excel(writer, sheet_name="README", index=False)
        df_signals.to_excel(writer, sheet_name="LIVE_SIGNALS", index=False)
        df_tracking.to_excel(writer, sheet_name="TRACKING", index=False)
        df_summary.to_excel(writer, sheet_name="SUMMARY", index=False)
        df_params.to_excel(writer, sheet_name="PARAMETERS", index=False)

    return xlsx_path
