"""Unit tests for OHLCV data loader and validation logic."""

from pathlib import Path
import io
import pytest
import pandas as pd

from wyckoff_screener.data_loader import (
    DataValidationError,
    load_ohlcv_csv,
    validate_ohlcv_dataframe,
)

FIXTURES_DIR = Path(__file__).resolve().parent.parent / "data"
SAMPLE_CSV_PATH = FIXTURES_DIR / "sample_nse_ohlcv.csv"


def test_load_sample_csv_success():
    """Verify that sample NSE OHLCV CSV loads cleanly with expected shape and dtypes."""
    df = load_ohlcv_csv(SAMPLE_CSV_PATH)
    assert not df.empty
    assert len(df) == 10
    assert pd.api.types.is_datetime64_any_dtype(df["Date"])
    for col in ["Open", "High", "Low", "Close", "Volume"]:
        assert pd.api.types.is_numeric_dtype(df[col])


def test_load_sorts_dates_ascending():
    """Verify that unordered input dates are sorted in ascending order."""
    csv_data = io.StringIO(
        "Date,Open,High,Low,Close,Volume\n"
        "2024-01-05,100,105,98,102,5000\n"
        "2024-01-02,90,95,88,92,4000\n"
        "2024-01-03,92,97,90,96,4500\n"
    )
    df = load_ohlcv_csv(csv_data)
    dates = df["Date"].tolist()
    assert dates == sorted(dates)
    assert dates[0] == pd.Timestamp("2024-01-02")
    assert dates[-1] == pd.Timestamp("2024-01-05")


def test_reject_duplicate_dates():
    """Verify that duplicate dates are detected and rejected by default."""
    csv_data = io.StringIO(
        "Date,Open,High,Low,Close,Volume\n"
        "2024-01-02,100,105,98,102,5000\n"
        "2024-01-02,101,106,99,103,6000\n"
    )
    with pytest.raises(DataValidationError, match="Duplicate dates found"):
        load_ohlcv_csv(csv_data)


def test_missing_required_columns():
    """Verify that missing required columns raise a validation error."""
    csv_data = io.StringIO(
        "Date,Open,High,Low\n"
        "2024-01-02,100,105,98\n"
    )
    with pytest.raises(DataValidationError, match="Missing required OHLCV columns"):
        load_ohlcv_csv(csv_data)


def test_invalid_high_low_logic():
    """Verify that High < Low raises validation error."""
    csv_data = io.StringIO(
        "Date,Open,High,Low,Close,Volume\n"
        "2024-01-02,100,90,95,92,5000\n"  # High (90) < Low (95)
    )
    with pytest.raises(DataValidationError, match="High < Low"):
        load_ohlcv_csv(csv_data)


def test_invalid_high_open_or_close_logic():
    """Verify that High < Open or High < Close raises validation error."""
    # High < Close
    csv_data = io.StringIO(
        "Date,Open,High,Low,Close,Volume\n"
        "2024-01-02,100,105,98,108,5000\n"  # High (105) < Close (108)
    )
    with pytest.raises(DataValidationError, match="High < Close"):
        load_ohlcv_csv(csv_data)

    # Low > Open
    csv_data_low = io.StringIO(
        "Date,Open,High,Low,Close,Volume\n"
        "2024-01-02,95,105,98,100,5000\n"  # Low (98) > Open (95)
    )
    with pytest.raises(DataValidationError, match="Low > Open"):
        load_ohlcv_csv(csv_data_low)


def test_negative_volume_rejected():
    """Verify that negative volume values raise a validation error."""
    csv_data = io.StringIO(
        "Date,Open,High,Low,Close,Volume\n"
        "2024-01-02,100,105,98,102,-500\n"
    )
    with pytest.raises(DataValidationError, match="negative Volume"):
        load_ohlcv_csv(csv_data)


def test_nan_values_rejected():
    """Verify that null/NaN values in OHLCV columns raise a validation error."""
    csv_data = io.StringIO(
        "Date,Open,High,Low,Close,Volume\n"
        "2024-01-02,100,105,NaN,102,5000\n"
    )
    with pytest.raises(DataValidationError, match="Null/NaN values detected"):
        load_ohlcv_csv(csv_data)


def test_empty_dataframe_rejected():
    """Verify that an empty DataFrame raises a validation error."""
    empty_df = pd.DataFrame()
    with pytest.raises(DataValidationError, match="empty"):
        validate_ohlcv_dataframe(empty_df)


def test_nonexistent_file_raises():
    """Verify that attempting to load a non-existent file raises FileNotFoundError."""
    with pytest.raises(FileNotFoundError):
        load_ohlcv_csv("nonexistent_path_to_data.csv")


def test_tradingview_style_columns_success():
    """Verify that TradingView-style lowercase and 'time' column headers are normalized."""
    csv_data = io.StringIO(
        "time,open,high,low,close,Volume\n"
        "2024-02-22,1427.55,1435.1,1417.6,1426.2,5816\n"
        "2024-02-23,1430,1431.25,1416.7,1421.65,2058\n"
    )
    df = load_ohlcv_csv(csv_data)
    assert not df.empty
    assert len(df) == 2
    # Verify columns were successfully renamed to expected canonical formats
    for expected_col in ["Date", "Open", "High", "Low", "Close", "Volume"]:
        assert expected_col in df.columns
    assert df["Close"].iloc[0] == 1426.2
    assert df["Volume"].iloc[0] == 5816


def test_oneil_rs_score_calculation():
    """Verify that calculate_oneil_rs_score calculates weighted returns correctly."""
    from wyckoff_screener.data_loader import calculate_oneil_rs_score
    # Create a synthetic dataset of exactly 252 days.
    # Start at 100, increase by 10% each quarter
    # Q4: start 100, end 110 (index 0 to 62) -> ret = 10%
    # Q3: start 110, end 121 (index 62 to 125) -> ret = 10%
    # Q2: start 121, end 133.1 (index 125 to 188) -> ret = 10%
    # Q1: start 133.1, end 146.41 (index 188 to 251) -> ret = 10%
    # Expected weighted return score = (0.4 * 0.10 + 0.2 * 0.10 + 0.2 * 0.10 + 0.2 * 0.10) * 100.0 = 10.0
    prices = [100.0] * 252
    # Q4 range
    for i in range(1, 63):
        prices[i] = 100.0 + (i / 62) * 10.0
    # Q3 range
    for i in range(63, 126):
        prices[i] = 110.0 + ((i - 62) / 63) * 11.0
    # Q2 range
    for i in range(126, 189):
        prices[i] = 121.0 + ((i - 125) / 63) * 12.1
    # Q1 range
    for i in range(189, 252):
        prices[i] = 133.1 + ((i - 188) / 63) * 13.31

    df = pd.DataFrame({
        "Date": pd.date_range("2024-01-01", periods=252),
        "Open": prices,
        "High": prices,
        "Low": prices,
        "Close": prices,
        "Volume": [1000] * 252
    })

    score = calculate_oneil_rs_score(df)
    # Allow small floating point delta
    assert abs(score - 10.0) < 0.01


