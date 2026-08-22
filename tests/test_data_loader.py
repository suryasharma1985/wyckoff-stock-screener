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
