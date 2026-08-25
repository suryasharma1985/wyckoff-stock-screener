"""Google Sheets Export Engine for Phase 18 Forward-Testing System.

Generates:
1. data/forward_testing/screener_candidates.csv (Flat clean candidate export)
2. data/forward_testing/screener_candidates.xlsx (Excel version of candidates)
3. data/forward_testing/SLA_Wyckoff_Forward_Testing_Template.xlsx (Complete 7-tab Google Sheets master workbook)
"""

from pathlib import Path
from typing import Any, Final, Optional, Sequence
import pandas as pd

from wyckoff_screener.forward_testing.models import (
    ForwardSignal,
    ForwardTradeResult,
    SCHEMA_VERSION,
    DEFAULT_TARGET_1_PCT,
    DEFAULT_TARGET_2_PCT,
    DEFAULT_TARGET_3_PCT,
    DEFAULT_STOP_LOSS_PCT,
)
from wyckoff_screener.forward_testing.evaluator import evaluate_forward_performance


def parse_candidates_csv_to_forward_signals(
    candidates_df: pd.DataFrame,
    run_id: Optional[str] = None,
) -> list[ForwardSignal]:
    """Convert candidates.csv DataFrame into a list of immutable ForwardSignal instances.

    Args:
        candidates_df: DataFrame loaded from candidates.csv.
        run_id: Optional unique run identifier (defaults to screening date + timestamp).

    Returns:
        List of ForwardSignal instances.
    """
    signals: list[ForwardSignal] = []
    if candidates_df.empty:
        return signals

    for _, row in candidates_df.iterrows():
        sym = str(row["symbol"]).strip()
        sig_dt = str(row.get("as_of_date", row.get("signal_date", "N/A")))[:10]
        r_id = run_id or f"{sig_dt.replace('-', '')}_1530"
        sig_id = f"{r_id}_{sym}"

        comp_name = str(row.get("company_name", sym))
        prio = str(row.get("candidate_category", "QUALIFIED_CANDIDATE"))
        score = float(row.get("composite_score", 0.0))
        
        event_type = str(row.get("most_recent_event_type", "LPS"))
        sig_type = event_type
        phase_candidate = "Phase C/D Candidate" if event_type in ["Spring", "LPS", "SOS"] else "Phase A/B Candidate"
        
        # VSA status summary
        vol_r = row.get("vsa_volume_ratio", "N/A")
        spr_r = row.get("vsa_spread_ratio", "N/A")
        cls_p = row.get("vsa_close_position", "N/A")
        vsa_summary = f"Vol: {vol_r}x, Spr: {spr_r}x, Pos: {cls_p}"

        # P&F score summary
        pf_tgt = row.get("pf_target_price")
        pf_cols = row.get("pf_count_columns")
        pf_summary = f"Tgt: {pf_tgt} (Cols: {pf_cols})" if pd.notna(pf_tgt) else "P&F Pending"

        close_val = float(row.get("close", 0.0))
        entry_val = close_val  # Signal-day close as authoritative entry

        broad_status = bool(row.get("is_mechanically_qualified", True))
        mech_status = bool(row.get("is_mechanically_qualified", True))
        tv_url = str(row.get("tradingview_daily_url", f"https://www.tradingview.com/chart/?symbol=NSE%3A{sym}&interval=D"))
        
        notes = str(row.get("numeric_evidence", row.get("explanation_summary", "")))

        sig = ForwardSignal(
            signal_id=sig_id,
            run_id=r_id,
            signal_date=sig_dt,
            symbol=sym,
            company_name=comp_name,
            exchange="NSE",
            priority=prio,
            score=score,
            signal_type=sig_type,
            wyckoff_event=event_type,
            wyckoff_phase=phase_candidate,
            vsa_status=vsa_summary,
            p_and_f_score=pf_summary,
            entry_price=entry_val,
            close_price=close_val,
            broad_setup_status=broad_status,
            mechanically_qualified=mech_status,
            tradingview_url=tv_url,
            screening_date=sig_dt,
            source_run_date=str(row.get("dataset_date", sig_dt)),
            notes=notes,
        )
        signals.append(sig)

    return signals


def create_forward_testing_workbook(
    signals: Sequence[ForwardSignal],
    trade_results: Optional[Sequence[ForwardTradeResult]] = None,
    output_dir: Path | str = "data/forward_testing",
    template_filename: str = "SLA_Wyckoff_Forward_Testing_Template.xlsx",
) -> Path:
    """Create the comprehensive 7-tab Google Sheets forward testing workbook and CSV exports.

    Args:
        signals: Sequence of ForwardSignal objects.
        trade_results: Optional sequence of evaluated ForwardTradeResult objects.
        output_dir: Target output directory.
        template_filename: Name of the master template workbook.

    Returns:
        Path to the generated Excel workbook.
    """
    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)
    xlsx_path = out_path / template_filename
    candidates_csv_path = out_path / "screener_candidates.csv"
    candidates_xlsx_path = out_path / "screener_candidates.xlsx"

    # 1. Build master SIGNALS DataFrame
    signals_rows = []
    results_map = {r.signal_id: r for r in (trade_results or [])}

    for sig in signals:
        res = results_map.get(sig.signal_id)
        if res is None:
            # Create default open result
            res = evaluate_forward_performance(sig, future_ohlc_df=None)
        signals_rows.append(res.to_signals_tab_row(sig))

    df_signals = pd.DataFrame(signals_rows)

    # Save candidates exports
    df_signals.to_csv(candidates_csv_path, index=False)
    df_signals.to_excel(candidates_xlsx_path, index=False)

    # 2. Build README Tab
    readme_rows = [
        {"Section": "Overview", "Details": "Phase 18 Google Sheets Forward-Testing System for Wyckoff Screener"},
        {"Section": "Purpose", "Details": "Prospective forward validation of screener candidate signals in real market time."},
        {"Section": "Workflow Step 1", "Details": "Run Python Wyckoff screener and export candidates using export_forward_testing.py."},
        {"Section": "Workflow Step 2", "Details": "Import screener_candidates.csv into the SIGNALS tab in Google Sheets."},
        {"Section": "Workflow Step 3", "Details": "Google Sheets / GOOGLEFINANCE retrieves daily prices to track post-signal returns."},
        {"Section": "Workflow Step 4", "Details": "Track +5D, +10D, +20D, +30D, +60D returns, MFE, MAE, Targets (+10%, +20%, +30%), and Stop (-5%)."},
        {"Section": "Workflow Step 5", "Details": "DASHBOARD tab aggregates live Win Rate, Profit Factor, Expectancy, and Score predictive tests."},
        {"Section": "Lookahead Protection", "Details": "Signal metadata is strictly immutable once generated; only future performance fields update."},
        {"Section": "Ambiguous Bar Rule", "Details": "If both Target 1 and Stop Loss are touched on the same candle, result is classified as AMBIGUOUS."},
    ]
    df_readme = pd.DataFrame(readme_rows)

    # 3. Build SETTINGS Tab
    settings_rows = [
        {"Parameter": "Schema_Version", "Value": SCHEMA_VERSION, "Description": "Forward testing schema version"},
        {"Parameter": "Target_1_Pct", "Value": DEFAULT_TARGET_1_PCT, "Description": "First profit target (% above entry)"},
        {"Parameter": "Target_2_Pct", "Value": DEFAULT_TARGET_2_PCT, "Description": "Second profit target (% above entry)"},
        {"Parameter": "Target_3_Pct", "Value": DEFAULT_TARGET_3_PCT, "Description": "Third profit target (% above entry)"},
        {"Parameter": "Stop_Loss_Pct", "Value": DEFAULT_STOP_LOSS_PCT, "Description": "Stop loss risk threshold (% below entry)"},
        {"Parameter": "Max_Observation_Days", "Value": 60, "Description": "Maximum forward observation window in trading days"},
        {"Parameter": "Entry_Model", "Value": "SIGNAL_DAY_CLOSE", "Description": "Immutable entry price equals signal-date closing price"},
        {"Parameter": "Ambiguity_Handling", "Value": "AMBIGUOUS", "Description": "Classification when both target and stop are reached on the same day"},
    ]
    df_settings = pd.DataFrame(settings_rows)

    # 4. Build PRICE_DATA Tab (Google Finance Helper)
    price_data_rows = [
        {"Symbol": "ZEEL", "Formula_Example": '=GOOGLEFINANCE("NSE:ZEEL", "price", DATE(2026,8,21), TODAY(), "DAILY")', "Notes": "Retrieves daily closing prices starting from signal date"},
        {"Symbol": "JINDALSAW", "Formula_Example": '=GOOGLEFINANCE("NSE:JINDALSAW", "price", DATE(2026,8,21), TODAY(), "DAILY")', "Notes": "Retrieves daily closing prices starting from signal date"},
        {"Symbol": "RELIANCE", "Formula_Example": '=GOOGLEFINANCE("NSE:RELIANCE", "all", DATE(2026,8,21), TODAY(), "DAILY")', "Notes": "Retrieves Open, High, Low, Close, Volume"},
    ]
    df_price_data = pd.DataFrame(price_data_rows)

    # 5. Build DASHBOARD Tab
    total_sig = len(df_signals)
    hp_sig = len(df_signals[df_signals["Priority"] == "HIGH_PRIORITY_CANDIDATE"])
    q_sig = len(df_signals[df_signals["Priority"] == "QUALIFIED_CANDIDATE"])
    open_sig = len(df_signals[df_signals["Status"] == "OPEN"])
    comp_sig = len(df_signals[df_signals["Status"] == "COMPLETED"])
    wins = len(df_signals[df_signals["Result"] == "WIN"])
    losses = len(df_signals[df_signals["Result"] == "LOSS"])
    ambig = len(df_signals[df_signals["Result"] == "AMBIGUOUS"])
    unavail = len(df_signals[df_signals["Status"] == "DATA_UNAVAILABLE"])

    closed_total = wins + losses
    win_rate = (wins / closed_total * 100.0) if closed_total > 0 else 0.0

    dashboard_rows = [
        {"Metric": "TOTAL SIGNALS", "Value": total_sig, "Details": "Total screener candidate signals recorded"},
        {"Metric": "HIGH PRIORITY SIGNALS", "Value": hp_sig, "Details": "Signals meeting high-priority criteria"},
        {"Metric": "QUALIFIED SIGNALS", "Value": q_sig, "Details": "Signals meeting qualified criteria"},
        {"Metric": "OPEN SIGNALS", "Value": open_sig, "Details": "Actively monitored open trades"},
        {"Metric": "COMPLETED SIGNALS", "Value": comp_sig, "Details": "Trades having reached target, stop, or time limit"},
        {"Metric": "WINS", "Value": wins, "Details": "Trades reaching Target 1 (+10%) before Stop Loss (-5%)"},
        {"Metric": "LOSSES", "Value": losses, "Details": "Trades reaching Stop Loss (-5%) before Target 1 (+10%)"},
        {"Metric": "AMBIGUOUS", "Value": ambig, "Details": "Trades touching both Target 1 and Stop Loss on same day"},
        {"Metric": "DATA UNAVAILABLE", "Value": unavail, "Details": "Signals lacking accessible price data"},
        {"Metric": "Win Rate (%)", "Value": round(win_rate, 1), "Details": "Wins / (Wins + Losses)"},
        {"Metric": "Average Return (%)", "Value": 0.0, "Details": "Mean realized return of completed signals"},
        {"Metric": "Median Return (%)", "Value": 0.0, "Details": "Median return of completed signals"},
        {"Metric": "Target 10% Hit Rate (%)", "Value": round(len(df_signals[df_signals["Target_10%"] == "YES"]) / max(total_sig, 1) * 100, 1), "Details": "Percentage of signals reaching Target 1"},
        {"Metric": "Target 20% Hit Rate (%)", "Value": round(len(df_signals[df_signals["Target_20%"] == "YES"]) / max(total_sig, 1) * 100, 1), "Details": "Percentage of signals reaching Target 2"},
        {"Metric": "Target 30% Hit Rate (%)", "Value": round(len(df_signals[df_signals["Target_30%"] == "YES"]) / max(total_sig, 1) * 100, 1), "Details": "Percentage of signals reaching Target 3"},
        {"Metric": "Stop Loss Hit Rate (%)", "Value": round(len(df_signals[df_signals["Stop_Loss_5%"] == "YES"]) / max(total_sig, 1) * 100, 1), "Details": "Percentage of signals reaching Stop Loss (-5%)"},
        {"Metric": "Expectancy (%)", "Value": 0.0, "Details": "(Win Rate * Avg Win) - (Loss Rate * |Avg Loss|)"},
    ]
    df_dashboard = pd.DataFrame(dashboard_rows)

    # 6. Build SCORE_ANALYSIS Tab
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
        sub = df_signals[(df_signals["Score"] >= low) & (df_signals["Score"] <= high)]
        count = len(sub)
        score_rows.append({
            "Score_Band": label,
            "Signal_Count": count,
            "Win_Rate (%)": 0.0,
            "Avg_20D_Return (%)": 0.0,
            "Avg_60D_Return (%)": 0.0,
            "Avg_Max_Gain (%)": 0.0,
            "Avg_Max_Drawdown (%)": 0.0,
            "Target_10%_Hit_Rate (%)": round(len(sub[sub["Target_10%"] == "YES"]) / max(count, 1) * 100, 1) if count > 0 else 0.0,
        })
    df_score_analysis = pd.DataFrame(score_rows)

    # 7. Build EVENT_ANALYSIS Tab
    events = ["Spring", "LPS", "SOS", "ST", "SC", "AR", "UTAD", "Other"]
    event_rows = []
    for ev in events:
        if ev == "Other":
            sub = df_signals[~df_signals["Wyckoff_Event"].isin(events[:-1])]
        else:
            sub = df_signals[df_signals["Wyckoff_Event"] == ev]
        count = len(sub)
        event_rows.append({
            "Wyckoff_Event": ev,
            "Signal_Count": count,
            "Win_Rate (%)": 0.0,
            "Avg_Return (%)": 0.0,
            "Median_Return (%)": 0.0,
            "Avg_Max_Gain (%)": 0.0,
            "Avg_Max_Drawdown (%)": 0.0,
            "Target_Hit_Rate (%)": round(len(sub[sub["Target_10%"] == "YES"]) / max(count, 1) * 100, 1) if count > 0 else 0.0,
        })
    df_event_analysis = pd.DataFrame(event_rows)

    # Write Master 7-Tab Workbook
    with pd.ExcelWriter(xlsx_path, engine="openpyxl") as writer:
        df_readme.to_excel(writer, sheet_name="README", index=False)
        df_settings.to_excel(writer, sheet_name="SETTINGS", index=False)
        df_signals.to_excel(writer, sheet_name="SIGNALS", index=False)
        df_price_data.to_excel(writer, sheet_name="PRICE_DATA", index=False)
        df_dashboard.to_excel(writer, sheet_name="DASHBOARD", index=False)
        df_score_analysis.to_excel(writer, sheet_name="SCORE_ANALYSIS", index=False)
        df_event_analysis.to_excel(writer, sheet_name="EVENT_ANALYSIS", index=False)

    return xlsx_path
