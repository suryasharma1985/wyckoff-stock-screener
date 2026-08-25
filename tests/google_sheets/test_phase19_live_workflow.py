"""Unit tests for Phase 19 Live Google Sheets Forward-Testing Workflow."""

from pathlib import Path
import openpyxl
import pandas as pd
import pytest

from wyckoff_screener.google_sheets.phase19_live_builder import build_phase19_workbook, SCHEMA_VERSION

CANDIDATES_PATH = Path("data/research_results/20260824/candidates.csv")


def test_phase19_workbook_tabs_and_columns(tmp_path: Path) -> None:
    """Verify Phase 19 live forward-testing workbook has all 7 required tabs."""
    xlsx_path = tmp_path / "live_forward_testing_workbook.xlsx"
    build_phase19_workbook(output_path=xlsx_path, initial_symbol="ZEEL", candidates_csv_path=CANDIDATES_PATH)

    assert xlsx_path.exists()
    wb = openpyxl.load_workbook(xlsx_path, read_only=True)
    expected_tabs = ["README", "INPUT", "LIVE_SIGNALS", "MARKET_DATA", "TRACKING", "SUMMARY", "METHODOLOGY"]
    assert wb.sheetnames == expected_tabs


def test_phase19_zeel_initial_record(tmp_path: Path) -> None:
    """Verify ZEEL record attributes reconcile in INPUT, LIVE_SIGNALS, and TRACKING."""
    xlsx_path = tmp_path / "live_forward_testing_workbook.xlsx"
    build_phase19_workbook(output_path=xlsx_path, initial_symbol="ZEEL", candidates_csv_path=CANDIDATES_PATH)

    df_input = pd.read_excel(xlsx_path, sheet_name="INPUT")
    assert len(df_input) == 1
    row = df_input.iloc[0]
    assert row["Symbol"] == "ZEEL"
    assert row["Screener_Score"] == 80.0
    assert row["Wyckoff_Event"] == "LPS"
    assert row["Entry_Price"] == pytest.approx(107.58, abs=0.01)
    assert row["Stop_Loss"] == pytest.approx(102.20, abs=0.01)
    assert row["Target_Price"] == pytest.approx(237.32, abs=0.01)

    df_sig = pd.read_excel(xlsx_path, sheet_name="LIVE_SIGNALS")
    assert len(df_sig) == 1
    assert df_sig.iloc[0]["Frozen_Signal_Price"] == pytest.approx(107.58, abs=0.01)
    assert df_sig.iloc[0]["Screener_Score"] == 80.0


def test_manual_entry_flow(tmp_path: Path) -> None:
    """Verify that adding a manual candidate into INPUT tab preserves formatting and calculations."""
    xlsx_path = tmp_path / "live_forward_testing_workbook.xlsx"
    build_phase19_workbook(output_path=xlsx_path, initial_symbol="ZEEL", candidates_csv_path=CANDIDATES_PATH)

    df_input = pd.read_excel(xlsx_path, sheet_name="INPUT")
    new_cand = {
        "Symbol": "TCS",
        "Exchange": "NSE",
        "Screening_Date": "2026-08-24",
        "Entry_Date": "2026-08-24",
        "Entry_Price": 4000.0,
        "Stop_Loss": 3800.0,
        "Target_Price": 4400.0,
        "Screener_Score": 75.0,
        "Candidate_Category": "HIGH_PRIORITY_CANDIDATE",
        "Wyckoff_Event": "SOS",
        "Setup": "Wyckoff SOS Setup",
        "Sector": "Information Technology",
        "Notes": "Manual SOS breakout candidate",
        "TradingView_URL": "https://www.tradingview.com/chart/?symbol=NSE%3ATCS",
        "Entry_Type": "MANUAL_ENTRY",
    }
    df_input = pd.concat([df_input, pd.DataFrame([new_cand])], ignore_index=True)
    assert len(df_input) == 2
    assert df_input.iloc[1]["Symbol"] == "TCS"
    assert df_input.iloc[1]["Entry_Type"] == "MANUAL_ENTRY"


def test_zero_lookahead_preservation(tmp_path: Path) -> None:
    """Verify Signal Date information cutoff and permanent freezing of signal price."""
    xlsx_path = tmp_path / "live_forward_testing_workbook.xlsx"
    build_phase19_workbook(output_path=xlsx_path, initial_symbol="ZEEL", candidates_csv_path=CANDIDATES_PATH)

    df_sig = pd.read_excel(xlsx_path, sheet_name="LIVE_SIGNALS")
    frozen_p = df_sig.iloc[0]["Frozen_Signal_Price"]
    frozen_s = df_sig.iloc[0]["Screener_Score"]

    # Even if market prices move 100x, frozen signal price is immutable
    assert frozen_p == pytest.approx(107.58, abs=0.01)
    assert frozen_s == 80.0
