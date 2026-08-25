"""Tests for Google Sheets master workbook and candidate CSV exports in forward_testing."""

from pathlib import Path
import openpyxl
import pandas as pd
import pytest

from wyckoff_screener.forward_testing import (
    parse_candidates_csv_to_forward_signals,
    create_forward_testing_workbook,
)

CANDIDATES_PATH = Path("data/research_results/20260824/candidates.csv")


def test_create_forward_testing_workbook_all_tabs(tmp_path: Path) -> None:
    """Verify master workbook contains all 7 required tabs and reconciles counts."""
    raw_df = pd.read_csv(CANDIDATES_PATH)
    signals = parse_candidates_csv_to_forward_signals(raw_df, run_id="20260824_1530")

    xlsx_path = create_forward_testing_workbook(
        signals=signals,
        trade_results=None,
        output_dir=tmp_path,
        template_filename="SLA_Wyckoff_Forward_Testing_Template.xlsx",
    )

    assert xlsx_path.exists()
    csv_path = tmp_path / "screener_candidates.csv"
    assert csv_path.exists()

    # Verify all 7 sheets in Excel workbook
    wb = openpyxl.load_workbook(xlsx_path, read_only=True)
    expected_tabs = [
        "README", "SETTINGS", "SIGNALS", "PRICE_DATA",
        "DASHBOARD", "SCORE_ANALYSIS", "EVENT_ANALYSIS"
    ]
    for tab in expected_tabs:
        assert tab in wb.sheetnames, f"Tab {tab} missing from forward testing workbook!"

    # Verify SIGNALS sheet columns
    df_signals = pd.read_excel(xlsx_path, sheet_name="SIGNALS")
    assert len(df_signals) == 383
    expected_cols = [
        "Signal_ID", "Signal_Date", "Symbol", "Company_Name", "Priority", "Score",
        "Signal_Type", "Wyckoff_Event", "Wyckoff_Phase", "VSA_Status", "P&F_Score",
        "Entry_Price", "Current_Price", "Current_Return_%", "Days_Since_Signal",
        "Status", "+5D_Return", "+10D_Return", "+20D_Return", "+30D_Return", "+60D_Return",
        "Max_Gain_%", "Max_Drawdown_%", "Target_10%", "Target_20%", "Target_30%",
        "Stop_Loss_5%", "Result", "Notes", "TradingView_URL"
    ]
    for col in expected_cols:
        assert col in df_signals.columns, f"Column {col} missing from SIGNALS tab!"

    # Verify DASHBOARD reconciles with raw signals
    df_dash = pd.read_excel(xlsx_path, sheet_name="DASHBOARD")
    dash_dict = dict(zip(df_dash["Metric"], df_dash["Value"]))
    assert dash_dict["TOTAL SIGNALS"] == 383
    assert dash_dict["HIGH PRIORITY SIGNALS"] == 196
    assert dash_dict["QUALIFIED SIGNALS"] == 187
    assert dash_dict["OPEN SIGNALS"] == 383
