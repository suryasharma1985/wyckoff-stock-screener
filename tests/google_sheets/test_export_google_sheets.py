"""Tests for Google Sheets export and schema formatting."""

from pathlib import Path
import openpyxl
import pandas as pd
import pytest

from wyckoff_screener.google_sheets.exporter import (
    format_screener_candidates_for_signals_sheet,
    export_signals_to_google_sheets_workbook,
    SCHEMA_VERSION,
)


def test_format_screener_candidates_for_signals_sheet() -> None:
    """Verify raw candidates DataFrame is correctly mapped to SIGNALS schema."""
    raw_df = pd.DataFrame([
        {
            "symbol": "ZEEL",
            "company_name": "Zee Entertainment Enterprises Limited",
            "as_of_date": "2026-08-21",
            "candidate_category": "HIGH_PRIORITY_CANDIDATE",
            "composite_score": 80.0,
            "most_recent_event_type": "LPS",
            "close": 107.58,
            "pf_target_price": 237.32,
            "numeric_evidence": "Candidate LPS holding above support",
        }
    ])

    formatted = format_screener_candidates_for_signals_sheet(raw_df, default_stop_pct=5.0, default_target_pct=15.0)

    assert len(formatted) == 1
    row = formatted.iloc[0]
    assert row["Signal_ID"] == "ZEEL_2026-08-21"
    assert row["Symbol"] == "ZEEL"
    assert row["Signal_Date"] == "2026-08-21"
    assert row["Screener_Score"] == 80.0
    assert row["Priority"] == "HIGH_PRIORITY_CANDIDATE"
    assert row["Wyckoff_Event"] == "LPS"
    assert row["Entry_Price"] == 107.58
    assert row["Stop_Price"] == round(107.58 * 0.95, 2)
    assert row["Target_1"] == 237.32  # P&F target preserved
    assert row["Status"] == "ACTIVE"
    assert row["Outcome"] == "PENDING"


def test_export_signals_to_google_sheets_workbook_creates_all_sheets(tmp_path: Path) -> None:
    """Verify that export creates a valid 6-tab Excel workbook with complete schema."""
    signals_df = pd.DataFrame([
        {
            "Signal_ID": "RELIANCE_2024-01-31",
            "Signal_Date": "2024-01-31",
            "Symbol": "RELIANCE",
            "Company": "Reliance Industries Limited",
            "Exchange": "NSE",
            "Screener_Score": 75.0,
            "Priority": "HIGH_PRIORITY_CANDIDATE",
            "Wyckoff_Event": "Spring",
            "Entry_Type": "NEXT_DAY_OPEN",
            "Entry_Price": 2500.0,
            "Stop_Price": 2375.0,
            "Target_1": 2875.0,
            "Target_2": 3250.0,
            "Position_Size": 100,
            "Status": "ACTIVE",
            "Exit_Date": "",
            "Exit_Price": "",
            "Return_Pct": "",
            "R_Multiple": "",
            "Days_Held": "",
            "Outcome": "PENDING",
            "Notes": "Spring test evidence",
        }
    ])

    xlsx_path = export_signals_to_google_sheets_workbook(
        signals_df=signals_df,
        output_dir=tmp_path,
        filename="test_validation_workbook.xlsx",
    )

    assert xlsx_path.exists()
    assert (tmp_path / "screener_signals.csv").exists()

    wb = openpyxl.load_workbook(xlsx_path, read_only=True)
    expected_sheets = ["README", "SIGNALS", "PRICE_DATA", "TEST_RESULTS", "DASHBOARD", "SETTINGS"]
    for s in expected_sheets:
        assert s in wb.sheetnames, f"Sheet {s} missing from workbook!"
