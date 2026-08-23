"""Data loading and validation module for NSE OHLCV series.

Conforms to AGENTS.md conventions:
- Explicit type annotations
- Module-level constants for default columns and parameters
- Strict validation rules with informative error messages
"""

from pathlib import Path
from typing import Final, Sequence, Union
import io
import pandas as pd

# Default expected column names matching Yahoo Finance historical export
DEFAULT_DATE_COL: Final[str] = "Date"
DEFAULT_OPEN_COL: Final[str] = "Open"
DEFAULT_HIGH_COL: Final[str] = "High"
DEFAULT_LOW_COL: Final[str] = "Low"
DEFAULT_CLOSE_COL: Final[str] = "Close"
DEFAULT_VOLUME_COL: Final[str] = "Volume"

REQUIRED_OHLCV_COLUMNS: Final[tuple[str, ...]] = (
    DEFAULT_DATE_COL,
    DEFAULT_OPEN_COL,
    DEFAULT_HIGH_COL,
    DEFAULT_LOW_COL,
    DEFAULT_CLOSE_COL,
    DEFAULT_VOLUME_COL,
)


class DataValidationError(ValueError):
    """Raised when OHLCV data fails schema, integrity, or logic validation."""


def validate_ohlcv_dataframe(
    df: pd.DataFrame,
    date_col: str = DEFAULT_DATE_COL,
    open_col: str = DEFAULT_OPEN_COL,
    high_col: str = DEFAULT_HIGH_COL,
    low_col: str = DEFAULT_LOW_COL,
    close_col: str = DEFAULT_CLOSE_COL,
    volume_col: str = DEFAULT_VOLUME_COL,
    reject_duplicates: bool = True,
) -> pd.DataFrame:
    """Validate and sanitize an OHLCV DataFrame.

    Ensures:
    1. All required columns are present.
    2. Date column is parsed as datetime and sorted ascending.
    3. No duplicate dates (if reject_duplicates is True).
    4. Price and volume columns are strictly numeric.
    5. No missing/NaN values in OHLCV fields.
    6. High/Low/Open/Close logical consistency (High >= Low, High >= Open, High >= Close, Low <= Open, Low <= Close).
    7. Volume is non-negative.

    Args:
        df: Input DataFrame containing raw OHLCV data.
        date_col: Name of the Date column.
        open_col: Name of the Open price column.
        high_col: Name of the High price column.
        low_col: Name of the Low price column.
        close_col: Name of the Close price column.
        volume_col: Name of the Volume column.
        reject_duplicates: Whether to raise an error if duplicate dates are present.

    Returns:
        Validated and cleaned pd.DataFrame sorted ascending by Date with a clean RangeIndex.

    Raises:
        DataValidationError: If any validation check fails.
    """
    if df.empty:
        raise DataValidationError("OHLCV DataFrame is empty.")

    # 1. Verify required columns
    required_cols: Sequence[str] = [date_col, open_col, high_col, low_col, close_col, volume_col]
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise DataValidationError(f"Missing required OHLCV columns: {missing_cols}")

    cleaned = df.copy()

    # 2. Parse Date
    try:
        cleaned[date_col] = pd.to_datetime(cleaned[date_col])
    except Exception as exc:
        raise DataValidationError(f"Failed to parse '{date_col}' column as datetime: {exc}") from exc

    # 3. Check for duplicate dates (deterministic handling)
    # A. Identical duplicates: drop exact duplicate rows keeping first occurrence
    cleaned = cleaned.drop_duplicates(subset=required_cols, keep="first").copy()

    # B. Conflicting duplicates: different OHLCV values on the same date -> reject
    duplicate_mask = cleaned[date_col].duplicated(keep=False)
    if reject_duplicates and duplicate_mask.any():
        duplicate_dates = cleaned.loc[duplicate_mask, date_col].dt.strftime("%Y-%m-%d").unique().tolist()
        raise DataValidationError(
            f"Duplicate dates found in OHLCV data (conflicting records): {duplicate_dates} (reason: CONFLICTING_DUPLICATE_DATES)"
        )

    # 4. Convert and validate numeric dtypes
    numeric_cols = [open_col, high_col, low_col, close_col, volume_col]
    for col in numeric_cols:
        cleaned[col] = pd.to_numeric(cleaned[col], errors="coerce")

    # 5. Check for NaNs
    nan_counts = cleaned[required_cols].isna().sum()
    cols_with_nans = nan_counts[nan_counts > 0]
    if not cols_with_nans.empty:
        raise DataValidationError(f"Null/NaN values detected in columns: {cols_with_nans.to_dict()}")

    # 6. Check price logic: High >= Low, High >= Open, High >= Close, Low <= Open, Low <= Close
    invalid_high_low = cleaned[cleaned[high_col] < cleaned[low_col]]
    if not invalid_high_low.empty:
        raise DataValidationError(
            f"Found {len(invalid_high_low)} bars where High < Low (e.g. date: {invalid_high_low.iloc[0][date_col]})"
        )

    invalid_high_open = cleaned[cleaned[high_col] < cleaned[open_col]]
    if not invalid_high_open.empty:
        raise DataValidationError(
            f"Found {len(invalid_high_open)} bars where High < Open (e.g. date: {invalid_high_open.iloc[0][date_col]})"
        )

    invalid_high_close = cleaned[cleaned[high_col] < cleaned[close_col]]
    if not invalid_high_close.empty:
        raise DataValidationError(
            f"Found {len(invalid_high_close)} bars where High < Close (e.g. date: {invalid_high_close.iloc[0][date_col]})"
        )

    invalid_low_open = cleaned[cleaned[low_col] > cleaned[open_col]]
    if not invalid_low_open.empty:
        raise DataValidationError(
            f"Found {len(invalid_low_open)} bars where Low > Open (e.g. date: {invalid_low_open.iloc[0][date_col]})"
        )

    invalid_low_close = cleaned[cleaned[low_col] > cleaned[close_col]]
    if not invalid_low_close.empty:
        raise DataValidationError(
            f"Found {len(invalid_low_close)} bars where Low > Close (e.g. date: {invalid_low_close.iloc[0][date_col]})"
        )

    # 7. Check positive prices
    for p_col in [open_col, high_col, low_col, close_col]:
        non_positive = cleaned[cleaned[p_col] <= 0]
        if not non_positive.empty:
            raise DataValidationError(
                f"Found {len(non_positive)} bars with non-positive {p_col} price (e.g. date: {non_positive.iloc[0][date_col]})"
            )

    # 8. Check Volume non-negative
    invalid_volume = cleaned[cleaned[volume_col] < 0]
    if not invalid_volume.empty:
        raise DataValidationError(
            f"Found {len(invalid_volume)} bars with negative Volume (e.g. date: {invalid_volume.iloc[0][date_col]})"
        )

    # 9. Sort ascending by date and enforce canonical column order
    cleaned = cleaned.sort_values(by=date_col, ascending=True).reset_index(drop=True)
    canonical_cols = [date_col, open_col, high_col, low_col, close_col, volume_col]
    cleaned = cleaned[canonical_cols]

    return cleaned


def load_ohlcv_csv(
    filepath_or_buffer: Union[str, Path, io.StringIO, io.BytesIO],
    date_col: str = DEFAULT_DATE_COL,
    open_col: str = DEFAULT_OPEN_COL,
    high_col: str = DEFAULT_HIGH_COL,
    low_col: str = DEFAULT_LOW_COL,
    close_col: str = DEFAULT_CLOSE_COL,
    volume_col: str = DEFAULT_VOLUME_COL,
    reject_duplicates: bool = True,
) -> pd.DataFrame:
    """Load an NSE-style OHLCV CSV file and return a validated DataFrame.

    Args:
        filepath_or_buffer: Path to CSV or file-like buffer.
        date_col: Date column header name.
        open_col: Open column header name.
        high_col: High column header name.
        low_col: Low column header name.
        close_col: Close column header name.
        volume_col: Volume column header name.
        reject_duplicates: Whether to reject duplicate dates.

    Returns:
        Validated pd.DataFrame sorted ascending by Date.

    Raises:
        FileNotFoundError: If filepath does not exist.
        DataValidationError: If data validation fails.
    """
    if isinstance(filepath_or_buffer, (str, Path)):
        path = Path(filepath_or_buffer)
        if not path.is_file():
            raise FileNotFoundError(f"OHLCV file not found: {path}")

    try:
        raw_df = pd.read_csv(filepath_or_buffer)
    except Exception as exc:
        raise DataValidationError(f"Could not read CSV data: {exc}") from exc

    return validate_ohlcv_dataframe(
        raw_df,
        date_col=date_col,
        open_col=open_col,
        high_col=high_col,
        low_col=low_col,
        close_col=close_col,
        volume_col=volume_col,
        reject_duplicates=reject_duplicates,
    )
