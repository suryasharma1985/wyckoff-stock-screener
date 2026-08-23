"""NSE symbol universe loader and validation for batch screening."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
import os
from pathlib import Path
import re
from typing import Any, Final, Optional, Sequence, Union
import pandas as pd

DEFAULT_ELIGIBLE_SERIES: Final[tuple[str, ...]] = ("EQ",)
YAHOO_NSE_SUFFIX: Final[str] = ".NS"

# Valid NSE ticker regex: alphanumeric with optional hyphens/ampersands (e.g. M&M, BAJAJ-AUTO)
VALID_SYMBOL_REGEX: Final[re.Pattern] = re.compile(r"^[A-Z0-9&_\-]+$")


@dataclass
class SymbolRecord:
    """Represents a validated NSE symbol record."""

    symbol: str
    company_name: str
    series: str
    exchange: str
    yfinance_ticker: str
    source_row_index: int


@dataclass
class UniverseValidationReport:
    """Structured report produced by universe ingestion and validation."""

    universe_source: str
    retrieval_date: str
    methodology_note: str
    total_rows_ingested: int
    accepted_count: int
    rejected_count: int
    accepted_symbols: list[SymbolRecord] = field(default_factory=list)
    rejected_rows: list[dict[str, Any]] = field(default_factory=list)
    duplicate_symbols: list[str] = field(default_factory=list)
    missing_fields_rows: list[dict[str, Any]] = field(default_factory=list)
    eligible_series_used: tuple[str, ...] = DEFAULT_ELIGIBLE_SERIES

    def get_tickers_list(self) -> list[str]:
        """Return list of validated yfinance tickers (.NS suffix)."""
        return [rec.yfinance_ticker for rec in self.accepted_symbols]

    def to_dict(self) -> dict[str, Any]:
        """Convert report summary to dictionary."""
        return {
            "universe_source": self.universe_source,
            "retrieval_date": self.retrieval_date,
            "methodology_note": self.methodology_note,
            "total_rows_ingested": self.total_rows_ingested,
            "accepted_count": self.accepted_count,
            "rejected_count": self.rejected_count,
            "duplicate_count": len(self.duplicate_symbols),
            "missing_fields_count": len(self.missing_fields_rows),
            "eligible_series_used": list(self.eligible_series_used),
        }


def format_yfinance_nse_ticker(symbol: str) -> str:
    """Format an NSE symbol for Yahoo Finance by appending .NS if not present.

    Args:
        symbol: Raw NSE symbol (e.g. 'ANANTRAJ' or 'ANANTRAJ.NS').

    Returns:
        Formatted ticker with .NS suffix (e.g. 'ANANTRAJ.NS').
    """
    clean_sym = symbol.strip().upper()
    if clean_sym.endswith(YAHOO_NSE_SUFFIX):
        return clean_sym
    return f"{clean_sym}{YAHOO_NSE_SUFFIX}"


def load_nse_universe_csv(
    csv_path: Union[str, Path],
    eligible_series: Sequence[str] = DEFAULT_ELIGIBLE_SERIES,
    source_name: Optional[str] = None,
) -> UniverseValidationReport:
    """Load and validate an NSE equity universe CSV.

    Expected CSV columns (case-insensitive):
      - Symbol / SYMBOL
      - Company Name / NAME OF COMPANY / company_name
      - Series / SERIES
      - Exchange / EXCHANGE (defaults to 'NSE' if missing)

    Guiding Principles:
      - 'EQ' is the default eligible series.
      - Alternative series (e.g. 'BE' Trade-for-Trade / Book Entry) are not equivalent
        and must be explicitly selected by the caller via eligible_series.
      - Duplicates and malformed symbols are rejected and recorded with structured errors.
      - User-provided symbols are never silently modified or truncated.
      - Explicit note that current universe screening has survivorship bias and is
        distinct from point-in-time historical backtesting.

    Args:
        csv_path: Path to the universe CSV file.
        eligible_series: Sequence of allowed series codes (default ('EQ',)).
        source_name: Optional custom description of the universe source.

    Returns:
        UniverseValidationReport with detailed counts and records.
    """
    path = Path(csv_path)
    if not path.exists():
        raise FileNotFoundError(f"Universe CSV not found at: {path}")

    df_raw = pd.read_csv(path)
    if df_raw.empty:
        raise ValueError(f"Universe CSV is empty: {path}")

    # Standardize column names (lowercase and strip whitespace)
    col_mapping: dict[str, str] = {}
    for col in df_raw.columns:
        norm = col.strip().lower().replace(" ", "_")
        if norm in ("symbol", "ticker", "security_symbol"):
            col_mapping[col] = "symbol"
        elif norm in ("company_name", "name_of_company", "security_name", "company"):
            col_mapping[col] = "company_name"
        elif norm in ("series", "equity_series", "security_series"):
            col_mapping[col] = "series"
        elif norm in ("exchange", "market"):
            col_mapping[col] = "exchange"

    df = df_raw.rename(columns=col_mapping)

    # Required column checks
    required = ["symbol", "series"]
    missing = [req for req in required if req not in df.columns]
    if missing:
        raise ValueError(f"Universe CSV missing mandatory columns: {missing}. Available: {list(df_raw.columns)}")

    eligible_series_set = {s.strip().upper() for s in eligible_series}
    retrieval_date = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    universe_src = source_name or str(path.name)

    methodology_note = (
        "SURVIVORSHIP BIAS NOTICE: This universe reflects the current/provided constituent list. "
        "It is valid for forward screening and monitoring, but represents a survivorship-biased snapshot "
        "if backtested historically. For bias-free historical testing, point-in-time constituents must be used."
    )

    accepted_records: list[SymbolRecord] = []
    rejected_records: list[dict[str, Any]] = []
    missing_fields_records: list[dict[str, Any]] = []
    duplicate_symbols: list[str] = []
    seen_symbols: set[str] = set()

    for idx, row in df.iterrows():
        raw_sym = row.get("symbol")
        raw_company = row.get("company_name", "")
        raw_series = row.get("series")
        raw_exchange = row.get("exchange", "NSE")

        # 1. Missing symbol or series
        if pd.isna(raw_sym) or not str(raw_sym).strip() or pd.isna(raw_series) or not str(raw_series).strip():
            err = {
                "row_index": idx,
                "raw_symbol": str(raw_sym),
                "reason": "Missing required field (symbol or series is NaN/empty).",
            }
            missing_fields_records.append(err)
            rejected_records.append(err)
            continue

        clean_sym = str(raw_sym).strip().upper()
        clean_series = str(raw_series).strip().upper()
        clean_company = str(raw_company).strip() if pd.notna(raw_company) else clean_sym
        clean_exchange = str(raw_exchange).strip().upper() if pd.notna(raw_exchange) else "NSE"

        # 2. Check eligible series
        if clean_series not in eligible_series_set:
            rejected_records.append({
                "row_index": idx,
                "raw_symbol": clean_sym,
                "series": clean_series,
                "reason": f"Series '{clean_series}' is not in eligible series {tuple(eligible_series_set)}.",
            })
            continue

        # 3. Check symbol syntax
        base_sym_for_regex = clean_sym[:-3] if clean_sym.endswith(YAHOO_NSE_SUFFIX) else clean_sym
        if not VALID_SYMBOL_REGEX.match(base_sym_for_regex):
            rejected_records.append({
                "row_index": idx,
                "raw_symbol": clean_sym,
                "reason": f"Symbol contains invalid characters. Must match {VALID_SYMBOL_REGEX.pattern}.",
            })
            continue

        # 4. Duplicate symbol check
        if clean_sym in seen_symbols:
            duplicate_symbols.append(clean_sym)
            rejected_records.append({
                "row_index": idx,
                "raw_symbol": clean_sym,
                "reason": "Duplicate symbol encountered in universe file.",
            })
            continue

        seen_symbols.add(clean_sym)
        yfinance_ticker = format_yfinance_nse_ticker(clean_sym)

        accepted_records.append(
            SymbolRecord(
                symbol=clean_sym,
                company_name=clean_company,
                series=clean_series,
                exchange=clean_exchange,
                yfinance_ticker=yfinance_ticker,
                source_row_index=int(idx),
            )
        )

    return UniverseValidationReport(
        universe_source=universe_src,
        retrieval_date=retrieval_date,
        methodology_note=methodology_note,
        total_rows_ingested=len(df),
        accepted_count=len(accepted_records),
        rejected_count=len(rejected_records),
        accepted_symbols=accepted_records,
        rejected_rows=rejected_records,
        duplicate_symbols=duplicate_symbols,
        missing_fields_rows=missing_fields_records,
        eligible_series_used=tuple(eligible_series),
    )
