"""Automated tests for Google Sheets & Excel multi-tab workbook export."""

from pathlib import Path
import openpyxl
import pandas as pd
import pytest

from wyckoff_screener.backtest.engine import export_backtest_workbook


def test_export_backtest_workbook_creates_all_tabs(tmp_path: Path) -> None:
    """Verify that export_backtest_workbook produces an 8-tab XLSX file matching specifications."""
    signals_df = pd.DataFrame([
        {
            "signal_date": "2024-01-31",
            "symbol": "ANANTRAJ",
            "composite_score": 72.5,
            "candidate_category": "HIGH_PRIORITY_CANDIDATE",
            "most_recent_event_type": "Spring",
            "entry_date": "2024-02-01",
            "entry_price": 300.0,
            "exit_price_20d": 330.0,
            "fwd_ret_20d": 10.0,
            "fwd_net_ret_20d": 9.6,
            "exit_price_60d": 360.0,
            "fwd_ret_60d": 20.0,
            "fwd_net_ret_60d": 19.6,
            "mfe_pct": 25.0,
            "mae_pct": -3.0,
            "max_drawdown_pct": -8.0,
        },
        {
            "signal_date": "2024-01-31",
            "symbol": "APOLLO",
            "composite_score": 45.0,
            "candidate_category": "QUALIFIED_CANDIDATE",
            "most_recent_event_type": "SOS",
            "entry_date": "2024-02-01",
            "entry_price": 100.0,
            "exit_price_20d": 105.0,
            "fwd_ret_20d": 5.0,
            "fwd_net_ret_20d": 4.6,
            "exit_price_60d": 115.0,
            "fwd_ret_60d": 15.0,
            "fwd_net_ret_60d": 14.6,
            "mfe_pct": 18.0,
            "mae_pct": -4.0,
            "max_drawdown_pct": -10.0,
        },
    ])

    prices_df = pd.DataFrame([
        {"Date": "2024-01-31", "Symbol": "ANANTRAJ", "Trading_Day_Num": 1, "Open": 298.0, "High": 302.0, "Low": 295.0, "Close": 300.0, "Volume": 500000},
        {"Date": "2024-02-01", "Symbol": "ANANTRAJ", "Trading_Day_Num": 2, "Open": 300.0, "High": 308.0, "Low": 299.0, "Close": 306.0, "Volume": 600000},
    ])

    manifest = {
        "backtest_run_id": "test_export_001",
        "start_date": "2024-01-01",
        "end_date": "2024-06-30",
        "frequency": "monthly",
        "entry_model": "next_trading_day_open",
        "survivorship_bias_disclosure": "Survivorship-biased historical research",
    }

    xlsx_path = export_backtest_workbook(signals_df, prices_df, manifest, tmp_path)
    assert xlsx_path.exists()

    # Verify workbook tabs
    wb = openpyxl.load_workbook(xlsx_path, read_only=True)
    expected_sheets = [

        "README",
        "SIGNALS",
        "TRADES",
        "MONTHLY_SUMMARY",
        "SCORE_ANALYSIS",
        "WYCKOFF_ANALYSIS",
        "EQUITY_CURVE",
        "PARAMETERS",
        "SUMMARY",
        "YEAR_ANALYSIS",
        "BENCHMARK",
        "PORTFOLIO",
        "DATA_DICTIONARY",
    ]
    for s in expected_sheets:
        assert s in wb.sheetnames, f"Sheet {s} missing from exported XLSX!"


    # Verify CSV files
    assert (tmp_path / "historical_signals.csv").exists()
    assert (tmp_path / "backtest_returns.csv").exists()
    assert (tmp_path / "historical_prices.csv").exists()
    assert (tmp_path / "backtest_manifest.json").exists()
