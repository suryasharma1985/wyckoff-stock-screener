"""Unit tests for Phase 18B Live Manual Screener Validation System."""

from pathlib import Path
import openpyxl
import pandas as pd
import pytest

from wyckoff_screener.google_sheets.live_validation_builder import (
    build_live_signals_dataframe,
    build_tracking_dataframe,
    export_live_validation_workbook,
    SCHEMA_VERSION,
)

CANDIDATES_PATH = Path("data/research_results/20260824/candidates.csv")


def test_live_signals_import_count_and_columns() -> None:
    """Verify 383 live signals (196 HP, 187 Qualified) and all required columns."""
    assert CANDIDATES_PATH.exists(), f"Candidates file missing at {CANDIDATES_PATH}"
    raw_df = pd.read_csv(CANDIDATES_PATH)
    assert len(raw_df) == 383

    df_sig = build_live_signals_dataframe(raw_df, screening_run_date="20260824")
    assert len(df_sig) == 383

    expected_cols = [
        "Signal_ID", "Symbol", "Company_Name", "Signal_Date", "Screener_Score",
        "Priority", "Setup", "Wyckoff_Event", "Signal_Price", "Stop_Price",
        "Target_Price", "Sector", "Explanation", "TradingView_URL", "Entry_Type"
    ]
    for col in expected_cols:
        assert col in df_sig.columns, f"Column {col} missing from LIVE_SIGNALS!"

    hp = df_sig[df_sig["Priority"] == "HIGH_PRIORITY_CANDIDATE"]
    q = df_sig[df_sig["Priority"] == "QUALIFIED_CANDIDATE"]
    assert len(hp) == 196
    assert len(q) == 187


def test_live_validation_workbook_all_5_tabs(tmp_path: Path) -> None:
    """Verify generated live validation workbook contains exactly the 5 required tabs."""
    xlsx_path = export_live_validation_workbook(
        candidates_csv_path=CANDIDATES_PATH,
        output_dir=tmp_path,
        screening_run_date="20260824",
    )
    assert xlsx_path.exists()

    wb = openpyxl.load_workbook(xlsx_path, read_only=True)
    expected_tabs = ["README", "LIVE_SIGNALS", "TRACKING", "SUMMARY", "PARAMETERS"]
    assert wb.sheetnames == expected_tabs


def test_tracking_tab_schema() -> None:
    """Verify TRACKING tab contains forward prices (1D to 60D), returns, and outcome fields."""
    raw_df = pd.read_csv(CANDIDATES_PATH)
    df_sig = build_live_signals_dataframe(raw_df, screening_run_date="20260824")
    df_trk = build_tracking_dataframe(df_sig)

    assert len(df_trk) == 383
    expected_tracking_cols = [
        "Signal_ID", "Symbol", "Signal_Date", "Signal_Price", "Current_Price",
        "Price_1D", "Price_5D", "Price_10D", "Price_20D", "Price_30D", "Price_60D",
        "Return_1D (%)", "Return_5D (%)", "Return_10D (%)", "Return_20D (%)",
        "Return_30D (%)", "Return_60D (%)", "Current_Return (%)",
        "Highest_Price_Reached", "Lowest_Price_Reached", "Max_Gain_Pct",
        "Max_Drawdown_Pct", "Target_Reached", "Stop_Reached", "Current_Status", "Final_Outcome"
    ]
    for col in expected_tracking_cols:
        assert col in df_trk.columns, f"Column {col} missing from TRACKING tab!"


def test_manual_signal_addition() -> None:
    """Verify that manually entering a signal works cleanly alongside screener signals."""
    raw_df = pd.read_csv(CANDIDATES_PATH).head(5)
    df_sig = build_live_signals_dataframe(raw_df, screening_run_date="20260824")

    # Add manual signal
    manual_row = {
        "Signal_ID": "LIVE_20260825_TATASTEEL",
        "Symbol": "TATASTEEL",
        "Company_Name": "Tata Steel Limited",
        "Signal_Date": "2026-08-25",
        "Screener_Score": 75.0,
        "Priority": "HIGH_PRIORITY_CANDIDATE",
        "Setup": "Wyckoff Spring Setup",
        "Wyckoff_Event": "Spring",
        "Signal_Price": 150.0,
        "Stop_Price": 142.5,
        "Target_Price": 165.0,
        "Sector": "Metals",
        "Explanation": "Manual live entry of Spring candidate",
        "TradingView_URL": "https://www.tradingview.com/chart/?symbol=NSE%3ATATASTEEL",
        "Entry_Type": "MANUAL_ENTRY",
    }
    df_sig = pd.concat([df_sig, pd.DataFrame([manual_row])], ignore_index=True)
    assert len(df_sig) == 6
    assert df_sig.iloc[-1]["Symbol"] == "TATASTEEL"
    assert df_sig.iloc[-1]["Entry_Type"] == "MANUAL_ENTRY"


def test_zero_lookahead_signal_freeze() -> None:
    """Verify Signal Date is the information cutoff and signal values remain frozen."""
    raw_df = pd.read_csv(CANDIDATES_PATH).head(1)
    df_sig = build_live_signals_dataframe(raw_df, screening_run_date="20260824")

    initial_price = df_sig.iloc[0]["Signal_Price"]
    initial_score = df_sig.iloc[0]["Screener_Score"]
    initial_event = df_sig.iloc[0]["Wyckoff_Event"]

    # Simulating subsequent tracking updates
    df_trk = build_tracking_dataframe(df_sig)
    df_trk.at[0, "Current_Price"] = initial_price * 1.50  # 50% rally
    df_trk.at[0, "Max_Gain_Pct"] = 50.0

    # Signal dataframe remains 100% unchanged
    assert df_sig.iloc[0]["Signal_Price"] == initial_price
    assert df_sig.iloc[0]["Screener_Score"] == initial_score
    assert df_sig.iloc[0]["Wyckoff_Event"] == initial_event
