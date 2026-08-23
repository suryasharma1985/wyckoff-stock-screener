"""Unit tests for NSE symbol universe ingestion and validation."""

import tempfile
from pathlib import Path
import pandas as pd
import pytest

from wyckoff_screener.universe.nse_symbols import (
    DEFAULT_ELIGIBLE_SERIES,
    format_yfinance_nse_ticker,
    load_nse_universe_csv,
)


def _create_temp_universe_csv(content: str) -> Path:
    """Helper to create a temporary CSV file with given content."""
    temp_dir = tempfile.mkdtemp()
    file_path = Path(temp_dir) / "universe.csv"
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)
    return file_path


def test_default_eq_eligibility():
    """Verify that 'EQ' is the default eligible series and non-EQ rows are rejected by default."""
    csv_content = """Symbol,Company Name,Series,Exchange
ANANTRAJ,Anant Raj Limited,EQ,NSE
SAMPLEBE,Sample TFT Stock,BE,NSE
SAMPLEGB,Sample Govt Bond,GB,NSE
"""
    path = _create_temp_universe_csv(csv_content)
    report = load_nse_universe_csv(path)

    assert report.total_rows_ingested == 3
    assert report.accepted_count == 1
    assert report.rejected_count == 2
    assert report.accepted_symbols[0].symbol == "ANANTRAJ"
    assert report.accepted_symbols[0].series == "EQ"
    assert report.accepted_symbols[0].yfinance_ticker == "ANANTRAJ.NS"
    assert report.eligible_series_used == ("EQ",)


def test_configurable_alternative_series():
    """Verify that caller can explicitly opt into alternative series like 'BE'."""
    csv_content = """Symbol,Company Name,Series,Exchange
ANANTRAJ,Anant Raj Limited,EQ,NSE
SAMPLEBE,Sample TFT Stock,BE,NSE
"""
    path = _create_temp_universe_csv(csv_content)
    report = load_nse_universe_csv(path, eligible_series=["EQ", "BE"])

    assert report.accepted_count == 2
    assert {s.symbol for s in report.accepted_symbols} == {"ANANTRAJ", "SAMPLEBE"}


def test_duplicate_symbols_rejected_with_structured_record():
    """Verify that duplicate ticker symbols are rejected with structured error details."""
    csv_content = """Symbol,Company Name,Series,Exchange
HINDCOPPER,Hindustan Copper,EQ,NSE
HINDCOPPER,Hindustan Copper Duplicate,EQ,NSE
"""
    path = _create_temp_universe_csv(csv_content)
    report = load_nse_universe_csv(path)

    assert report.accepted_count == 1
    assert report.rejected_count == 1
    assert "HINDCOPPER" in report.duplicate_symbols
    assert any("Duplicate" in r["reason"] for r in report.rejected_rows)


def test_malformed_and_missing_symbols_rejected():
    """Verify malformed symbols (e.g. invalid special characters or empty rows) are rejected."""
    csv_content = """Symbol,Company Name,Series,Exchange
VALID_ONE,Valid Company,EQ,NSE
INVALID$$$$,Bad Char Company,EQ,NSE
,Empty Symbol Company,EQ,NSE
"""
    path = _create_temp_universe_csv(csv_content)
    report = load_nse_universe_csv(path)

    assert report.accepted_count == 1
    assert report.accepted_symbols[0].symbol == "VALID_ONE"
    assert report.rejected_count == 2


def test_format_yfinance_nse_ticker_preserves_clean_symbols():
    """Verify ticker formatting appends .NS only when absent and preserves existing suffix."""
    assert format_yfinance_nse_ticker("ANANTRAJ") == "ANANTRAJ.NS"
    assert format_yfinance_nse_ticker("APOLLO.NS") == "APOLLO.NS"
    assert format_yfinance_nse_ticker("M&M") == "M&M.NS"
    assert format_yfinance_nse_ticker("BAJAJ-AUTO") == "BAJAJ-AUTO.NS"


def test_survivorship_bias_notice_present_in_report():
    """Verify validation report contains explicit survivorship bias methodology disclaimer."""
    csv_content = "Symbol,Series\nRELIANCE,EQ\n"
    path = _create_temp_universe_csv(csv_content)
    report = load_nse_universe_csv(path)

    assert "SURVIVORSHIP BIAS NOTICE" in report.methodology_note
