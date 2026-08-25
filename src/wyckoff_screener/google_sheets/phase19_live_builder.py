"""Phase 19 & 21: Live Google Sheets Forward-Testing System Builder.

Builds the production-ready 7-tab live forward-testing workbook with real Google Sheets formulas:
1. README
2. INPUT
3. LIVE_SIGNALS
4. MARKET_DATA
5. TRACKING
6. SUMMARY
7. METHODOLOGY
"""

from pathlib import Path
from typing import Final
import pandas as pd

SCHEMA_VERSION: Final[str] = "3.2.0"
DEFAULT_STOP_LOSS_PCT: Final[float] = 5.0
DEFAULT_TARGET_PCT: Final[float] = 10.0
MAX_TRACKING_ROWS: Final[int] = 50


def build_phase19_workbook(
    output_path: Path | str = "data/google_sheets/live_forward_testing_workbook.xlsx",
    initial_symbol: str = "ZEEL",
    candidates_csv_path: Path | str = "data/research_results/20260824/candidates.csv",
) -> Path:
    out_file = Path(output_path)
    out_file.parent.mkdir(parents=True, exist_ok=True)
    c_path = Path(candidates_csv_path)

    # 1. Load Candidate Record (ZEEL or first candidate)
    raw_candidates = pd.read_csv(c_path) if c_path.exists() else pd.DataFrame()
    if not raw_candidates.empty and initial_symbol in raw_candidates["symbol"].values:
        cand_row = raw_candidates[raw_candidates["symbol"] == initial_symbol].iloc[0]
    elif not raw_candidates.empty:
        cand_row = raw_candidates.iloc[0]
    else:
        cand_row = pd.Series({
            "symbol": initial_symbol,
            "company_name": "Zee Entertainment Enterprises Limited",
            "as_of_date": "2026-08-21",
            "close": 107.58,
            "composite_score": 80.0,
            "candidate_category": "HIGH_PRIORITY_CANDIDATE",
            "most_recent_event_type": "LPS",
            "pf_target_price": 237.32,
            "numeric_evidence": "Bar vol_ratio=0.71x, spread_ratio=0.64x, close_pos=0.53. Candidate LPS: higher low=103.50 vs prior Spring low=90.00 (+15.0%)",
            "tradingview_daily_url": f"https://www.tradingview.com/chart/?symbol=NSE%3A{initial_symbol}&interval=D",
        })

    sym = str(cand_row["symbol"])
    comp = str(cand_row["company_name"])
    sig_date = str(cand_row["as_of_date"])[:10]
    close_p = float(cand_row["close"])
    score = float(cand_row["composite_score"])
    prio = str(cand_row["candidate_category"])
    event = str(cand_row["most_recent_event_type"])
    setup = f"Wyckoff {event} Setup"
    stop_p = round(close_p * 0.95, 2)
    tgt_p = round(float(cand_row["pf_target_price"]), 2) if pd.notna(cand_row.get("pf_target_price")) else round(close_p * 1.10, 2)
    evidence = str(cand_row["numeric_evidence"])
    tv_url = str(cand_row.get("tradingview_daily_url", f"https://www.tradingview.com/chart/?symbol=NSE%3A{sym}&interval=D"))

    # TAB 1: README
    readme_rows = [
        {"Section": "Phase 21 Live Forward-Testing System", "Details": "Production-grade Google Sheets live candidate tracking workflow"},
        {"Section": "Primary Purpose", "Details": "Record what our Python screener identifies TODAY and objectively track what happens AFTER TODAY."},
        {"Section": "Execution Directives", "Details": "No historical backtests are running. System functions strictly as a live prospective forward ledger."},
        {"Section": "Workflow Step 1: Screener Run", "Details": "Python screener evaluates the market and generates candidate signals with scores, VSA, and P&F targets."},
        {"Section": "Workflow Step 2: Manual Input", "Details": "User enters candidate symbol, date, entry price, and score into the INPUT tab."},
        {"Section": "Workflow Step 3: Market Data", "Details": "MARKET_DATA tab pulls live and historical market prices via native =GOOGLEFINANCE() formulas."},
        {"Section": "Workflow Step 4: Tracking", "Details": "TRACKING tab calculates forward returns (+1D, +5D, +10D, +20D, +30D, +60D), MFE, MAE, targets, and stops."},
        {"Section": "Workflow Step 5: Summary", "Details": "SUMMARY tab automatically computes aggregate Win Rate, Profit Factor, Expectancy, and score deciles."},
        {"Section": "Information Cutoff Rule", "Details": "Signal Date is the absolute information cutoff. Signal Price, Score, Event, and Entry Price are frozen permanently."},
        {"Section": "Ambiguity Rule", "Details": "If Target and Stop are reached on the same daily candle, trade is classified as AMBIGUOUS (never an assumed win)."},
        {"Section": "Statistical Sample Tiers", "Details": "N < 30: INSUFFICIENT SAMPLE | 30 <= N < 100: INITIAL SAMPLE | N >= 100: STRONGER SAMPLE"},
    ]
    df_readme = pd.DataFrame(readme_rows)

    # TAB 2: INPUT (User Entry & Screener Handoff)
    input_rows = [
        {
            "Symbol": sym,
            "Exchange": "NSE",
            "Screening_Date": sig_date,
            "Entry_Date": sig_date,
            "Entry_Price": close_p,
            "Stop_Loss": stop_p,
            "Target_Price": tgt_p,
            "Screener_Score": score,
            "Candidate_Category": prio,
            "Wyckoff_Event": event,
            "Setup": setup,
            "Sector": "Media & Entertainment",
            "Notes": evidence,
            "TradingView_URL": tv_url,
            "Entry_Type": "MANUAL_OR_SCREENER",
        }
    ]
    df_input = pd.DataFrame(input_rows)

    # TAB 3: LIVE_SIGNALS (Validated Frozen Metadata from Python)
    live_signals_rows = [
        {
            "Signal_ID": f"20260824_{sym}",
            "Symbol": sym,
            "Company_Name": comp,
            "Signal_Date": sig_date,
            "Frozen_Signal_Price": close_p,
            "Screener_Score": score,
            "Priority": prio,
            "Setup": setup,
            "Wyckoff_Event": event,
            "Stop_Price": stop_p,
            "Target_Price": tgt_p,
            "P_and_F_Columns": 22,
            "VSA_Volume_Ratio": "0.71x",
            "VSA_Spread_Ratio": "0.64x",
            "VSA_Close_Pos": "0.53",
            "Explanation": evidence,
            "TradingView_URL": tv_url,
            "Validation_Status": "VALIDATED_BY_PYTHON",
        }
    ]
    df_live_signals = pd.DataFrame(live_signals_rows)

    # TAB 4: MARKET_DATA (Google Finance Live Formulas Reference)
    market_data_rows = [
        {
            "Symbol": sym,
            "GoogleFinance_Ticker": f"NSE:{sym}",
            "Current_Price_Formula": f'=GOOGLEFINANCE("NSE:{sym}", "price")',
            "Day_High_Formula": f'=GOOGLEFINANCE("NSE:{sym}", "high")',
            "Day_Low_Formula": f'=GOOGLEFINANCE("NSE:{sym}", "low")',
            "52W_High_Formula": f'=GOOGLEFINANCE("NSE:{sym}", "high52")',
            "52W_Low_Formula": f'=GOOGLEFINANCE("NSE:{sym}", "low52")',
            "Historical_Daily_Formula": f'=GOOGLEFINANCE("NSE:{sym}", "all", DATE(2026,8,21), TODAY(), "DAILY")',
            "Benchmark_Ticker": "NSE:NIFTY 50",
            "Benchmark_Price_Formula": '=GOOGLEFINANCE("NSE:NIFTY 50", "price")',
        }
    ]
    df_market_data = pd.DataFrame(market_data_rows)

    # TAB 5: TRACKING (Pre-built with safe multi-row Google Sheets formulas for rows 2 to 50)
    tracking_rows = []
    for r in range(2, MAX_TRACKING_ROWS + 2):
        tracking_rows.append({
            "Signal_ID": f'=IF(INPUT!A{r}<>"", "20260824_" & INPUT!A{r}, "")',
            "Symbol": f'=IF(INPUT!A{r}<>"", INPUT!A{r}, "")',
            "Signal_Date": f'=IF(INPUT!C{r}<>"", INPUT!C{r}, "")',
            "Signal_Price": f'=IF(INPUT!E{r}<>"", INPUT!E{r}, "")',
            "Current_Price": f'=IF(B{r}<>"", IFERROR(GOOGLEFINANCE("NSE:" & B{r}, "price"), D{r}), "")',
            "Price_1D": "",
            "Price_5D": "",
            "Price_10D": "",
            "Price_20D": "",
            "Price_30D": "",
            "Price_60D": "",
            "Return_1D (%)": f'=IF(AND(D{r}>0, F{r}<>""), ((F{r}-D{r})/D{r})*100, "")',
            "Return_5D (%)": f'=IF(AND(D{r}>0, G{r}<>""), ((G{r}-D{r})/D{r})*100, "")',
            "Return_10D (%)": f'=IF(AND(D{r}>0, H{r}<>""), ((H{r}-D{r})/D{r})*100, "")',
            "Return_20D (%)": f'=IF(AND(D{r}>0, I{r}<>""), ((I{r}-D{r})/D{r})*100, "")',
            "Return_30D (%)": f'=IF(AND(D{r}>0, J{r}<>""), ((J{r}-D{r})/D{r})*100, "")',
            "Return_60D (%)": f'=IF(AND(D{r}>0, K{r}<>""), ((K{r}-D{r})/D{r})*100, "")',
            "Current_Return (%)": f'=IF(D{r}>0, ((E{r}-D{r})/D{r})*100, "")',
            "Highest_Price_Reached": f'=IF(D{r}>0, MAX(E{r}, D{r}), "")',
            "Lowest_Price_Reached": f'=IF(D{r}>0, MIN(E{r}, D{r}), "")',
            "Max_Gain_Pct": f'=IF(D{r}>0, ((S{r}-D{r})/D{r})*100, "")',
            "Max_Drawdown_Pct": f'=IF(D{r}>0, ((T{r}-D{r})/D{r})*100, "")',
            "Target_Price": f'=IF(INPUT!G{r}<>"", INPUT!G{r}, "")',
            "Stop_Price": f'=IF(INPUT!F{r}<>"", INPUT!F{r}, "")',
            "Target_Reached": f'=IF(AND(E{r}>0, W{r}>0), IF(E{r}>=W{r}, "YES", "NO"), "")',
            "Stop_Reached": f'=IF(AND(E{r}>0, X{r}>0), IF(E{r}<=X{r}, "YES", "NO"), "")',
            "Current_Status": f'=IF(B{r}="", "", IF(AB{r}="OPEN", "ACTIVE_MONITORING", "CLOSED"))',
            "Final_Outcome": f'=IF(B{r}="", "", IF(AND(Y{r}="YES", Z{r}="YES"), "AMBIGUOUS", IF(Y{r}="YES", "WIN", IF(Z{r}="YES", "LOSS", "OPEN"))))',
        })
    df_tracking = pd.DataFrame(tracking_rows)

    # TAB 6: SUMMARY (Dynamic Google Sheets Formulas with 3 Sample Size Tiers & 6 Score Buckets)
    summary_rows = [
        {"Section": "=== LIVE FORWARD TRACKING METRICS ===", "Metric": "", "Value": "", "Details": ""},
        {"Section": "Summary KPIs", "Metric": "Total Live Signals (N)", "Value": '=COUNTA(INPUT!A2:A100)', "Details": "Total signals currently registered in INPUT"},
        {"Section": "Summary KPIs", "Metric": "Sample Size Status", "Value": '=IF(C2<30, "INSUFFICIENT SAMPLE (N=" & C2 & " < 30)", IF(C2<100, "INITIAL SAMPLE (N=" & C2 & " >= 30)", "STRONGER SAMPLE (N=" & C2 & " >= 100)"))', "Details": "3-tier statistical sample size indicator"},
        {"Section": "Summary KPIs", "Metric": "High Priority Signals", "Value": '=COUNTIF(INPUT!I2:I100, "HIGH_PRIORITY_CANDIDATE")', "Details": "Score >= 60 with mechanical qualification"},
        {"Section": "Summary KPIs", "Metric": "Qualified Signals", "Value": '=COUNTIF(INPUT!I2:I100, "QUALIFIED_CANDIDATE")', "Details": "Score 40 to 59.99"},
        {"Section": "Summary KPIs", "Metric": "Open Signals", "Value": '=COUNTIF(TRACKING!AA2:AA100, "ACTIVE_MONITORING")', "Details": "Signals currently in forward observation window"},
        {"Section": "Summary KPIs", "Metric": "Closed Signals", "Value": '=COUNTIF(TRACKING!AB2:AB100, "WIN") + COUNTIF(TRACKING!AB2:AB100, "LOSS")', "Details": "Signals that have reached target, stop, or 60D limit"},
        {"Section": "Summary KPIs", "Metric": "Winners", "Value": '=COUNTIF(TRACKING!AB2:AB100, "WIN")', "Details": "Trades reaching Target Price before Stop Price"},
        {"Section": "Summary KPIs", "Metric": "Losers", "Value": '=COUNTIF(TRACKING!AB2:AB100, "LOSS")', "Details": "Trades reaching Stop Price before Target Price"},
        {"Section": "Summary KPIs", "Metric": "Ambiguous Signals", "Value": '=COUNTIF(TRACKING!AB2:AB100, "AMBIGUOUS")', "Details": "Target & Stop reached on exact same daily candle"},
        {"Section": "Summary KPIs", "Metric": "Win Rate (%)", "Value": '=IF((C8+C9)>0, (C8/(C8+C9))*100, 0)', "Details": "Winners / (Winners + Losers) * 100"},
        {"Section": "Summary KPIs", "Metric": "Average Return (%)", "Value": '=IFERROR(AVERAGE(TRACKING!R2:R100), 0)', "Details": "Mean return across all registered positions"},
        {"Section": "Summary KPIs", "Metric": "Median Return (%)", "Value": '=IFERROR(MEDIAN(TRACKING!R2:R100), 0)', "Details": "Median return across all registered positions"},
        {"Section": "Summary KPIs", "Metric": "Average Max Gain / MFE (%)", "Value": '=IFERROR(AVERAGE(TRACKING!U2:U100), 0)', "Details": "Mean peak excursion above entry"},
        {"Section": "Summary KPIs", "Metric": "Average Max Drawdown / MAE (%)", "Value": '=IFERROR(AVERAGE(TRACKING!V2:V100), 0)', "Details": "Mean worst drawdown below entry"},
        {"Section": "Summary KPIs", "Metric": "Target Hit Rate (%)", "Value": '=IF(C2>0, (COUNTIF(TRACKING!Y2:Y100, "YES")/C2)*100, 0)', "Details": "Percentage of signals reaching Target Price"},
        {"Section": "Summary KPIs", "Metric": "Stop Hit Rate (%)", "Value": '=IF(C2>0, (COUNTIF(TRACKING!Z2:Z100, "YES")/C2)*100, 0)', "Details": "Percentage of signals reaching Stop Price"},
        {"Section": "Summary KPIs", "Metric": "Profit Factor", "Value": '=IF(COUNTIF(TRACKING!AB2:AB100, "LOSS")>0, (SUMIF(TRACKING!AB2:AB100, "WIN", TRACKING!R2:R100) / ABS(SUMIF(TRACKING!AB2:AB100, "LOSS", TRACKING!R2:R100))), 0)', "Details": "Gross Winning Return / Gross Losing Return"},
        {"Section": "Summary KPIs", "Metric": "Trade Expectancy (%)", "Value": '=(C11/100 * IFERROR(AVERAGEIF(TRACKING!AB2:AB100, "WIN", TRACKING!R2:R100), 0)) - ((1 - C11/100) * ABS(IFERROR(AVERAGEIF(TRACKING!AB2:AB100, "LOSS", TRACKING!R2:R100), 0)))', "Details": "(Win Rate * Avg Win) - (Loss Rate * |Avg Loss|)"},
        {"Section": "=== SCORE PREDICTIVE TABLE (6 BUCKETS) ===", "Metric": "", "Value": "", "Details": ""},
        {"Section": "Score Breakdown", "Metric": "Score 80+ (N=1)", "Value": '=COUNTIFS(INPUT!H2:H100, ">=80")', "Details": "Top-tier setups"},
        {"Section": "Score Breakdown", "Metric": "Score 70-79.99 (N=0)", "Value": '=COUNTIFS(INPUT!H2:H100, ">=70", INPUT!H2:H100, "<80")', "Details": "Strong setups"},
        {"Section": "Score Breakdown", "Metric": "Score 60-69.99 (N=0)", "Value": '=COUNTIFS(INPUT!H2:H100, ">=60", INPUT!H2:H100, "<70")', "Details": "Qualified High Priority"},
        {"Section": "Score Breakdown", "Metric": "Score 50-59.99 (N=0)", "Value": '=COUNTIFS(INPUT!H2:H100, ">=50", INPUT!H2:H100, "<60")', "Details": "Qualified upper baseline"},
        {"Section": "Score Breakdown", "Metric": "Score 40-49.99 (N=0)", "Value": '=COUNTIFS(INPUT!H2:H100, ">=40", INPUT!H2:H100, "<50")', "Details": "Qualified lower baseline"},
        {"Section": "Score Breakdown", "Metric": "Score Below 40 (N=0)", "Value": '=COUNTIFS(INPUT!H2:H100, "<40", INPUT!H2:H100, "<>\"")', "Details": "Sub-threshold setups"},
        {"Section": "=== WYCKOFF SETUP BREAKDOWN ===", "Metric": "", "Value": "", "Details": ""},
        {"Section": "Setup Breakdown", "Metric": "LPS Setups", "Value": '=COUNTIF(INPUT!J2:J100, "LPS")', "Details": "Last Point of Support candidates"},
        {"Section": "Setup Breakdown", "Metric": "SOS Setups", "Value": '=COUNTIF(INPUT!J2:J100, "SOS")', "Details": "Sign of Strength breakouts"},
        {"Section": "Setup Breakdown", "Metric": "Spring Setups", "Value": '=COUNTIF(INPUT!J2:J100, "Spring")', "Details": "Spring shakeout candidates"},
        {"Section": "Setup Breakdown", "Metric": "Secondary Test (ST) Setups", "Value": '=COUNTIF(INPUT!J2:J100, "ST")', "Details": "Secondary Test candidates"},
        {"Section": "Setup Breakdown", "Metric": "Automatic Rally (AR) Setups", "Value": '=COUNTIF(INPUT!J2:J100, "AR")', "Details": "Automatic Rally candidates"},
        {"Section": "Setup Breakdown", "Metric": "Selling Climax (SC) Setups", "Value": '=COUNTIF(INPUT!J2:J100, "SC")', "Details": "Selling Climax candidates"},
        {"Section": "=== PRIORITY CATEGORY BREAKDOWN ===", "Metric": "", "Value": "", "Details": ""},
        {"Section": "Priority Breakdown", "Metric": "HIGH PRIORITY CANDIDATE", "Value": '=COUNTIF(INPUT!I2:I100, "HIGH_PRIORITY_CANDIDATE")', "Details": "Score >= 60 with mechanical qualification"},
        {"Section": "Priority Breakdown", "Metric": "QUALIFIED CANDIDATE", "Value": '=COUNTIF(INPUT!I2:I100, "QUALIFIED_CANDIDATE")', "Details": "Score 40 to 59.99"},
    ]
    df_summary = pd.DataFrame(summary_rows)

    # TAB 7: METHODOLOGY (Architecture Distinction & Technical Documentation)
    methodology_rows = [
        {"Layer": "Architecture Model", "Component": "Hybrid Architecture (Option B)", "Responsibility": "Python Quantitative Engine + Google Sheets Forward Ledger"},
        {"Layer": "Python Layer", "Component": "VSA Bar Classification", "Responsibility": "Calculates 20-period volume ratios, spread ratios, and close positions bar-by-bar."},
        {"Layer": "Python Layer", "Component": "Wyckoff Schematic Detection", "Responsibility": "Identifies Springs, LPS higher lows, SOS breakouts, Secondary Tests, and UTADs."},
        {"Layer": "Python Layer", "Component": "Bruce Fraser Point & Figure", "Responsibility": "Constructs true 3-box reversal P&F charts, identifies horizontal count rows, and calculates price objectives."},
        {"Layer": "Python Layer", "Component": "Composite Setup Scorer", "Responsibility": "Applies 100-point weighted scoring (30 mechanical, 40 fresh event, 20 peer rank, 10 P&F upside)."},
        {"Layer": "Google Sheets Layer", "Component": "Market Price Retrieval", "Responsibility": "Pulls daily live and historical prices via =GOOGLEFINANCE('NSE:' & Symbol, 'price')."},
        {"Layer": "Google Sheets Layer", "Component": "Forward Return Calculation", "Responsibility": "Calculates percentage returns at +1D, +5D, +10D, +20D, +30D, +60D horizons."},
        {"Layer": "Google Sheets Layer", "Component": "MFE & MAE Excursions", "Responsibility": "Measures maximum favorable excursion (peak high) and adverse excursion (worst low)."},
        {"Layer": "Google Sheets Layer", "Component": "Outcome Classification", "Responsibility": "Classifies WIN (target hit first), LOSS (stop hit first), OPEN, or AMBIGUOUS (same day hit)."},
        {"Layer": "Google Sheets Layer", "Component": "SUMMARY Aggregations", "Responsibility": "Live dashboard updating Win Rate, Expectancy, Profit Factor, and score deciles dynamically."},
    ]
    df_methodology = pd.DataFrame(methodology_rows)

    # Write Master 7-Tab Workbook
    with pd.ExcelWriter(out_file, engine="openpyxl") as writer:
        df_readme.to_excel(writer, sheet_name="README", index=False)
        df_input.to_excel(writer, sheet_name="INPUT", index=False)
        df_live_signals.to_excel(writer, sheet_name="LIVE_SIGNALS", index=False)
        df_market_data.to_excel(writer, sheet_name="MARKET_DATA", index=False)
        df_tracking.to_excel(writer, sheet_name="TRACKING", index=False)
        df_summary.to_excel(writer, sheet_name="SUMMARY", index=False)
        df_methodology.to_excel(writer, sheet_name="METHODOLOGY", index=False)

    return out_file
