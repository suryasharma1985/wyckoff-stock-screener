"""Research universe builder, eligibility evaluator, and reproducible snapshot engine.

Guiding Principles:
- Strict separation between Universe Eligibility, Research Eligibility, and Setup Qualification.
- Research eligibility evaluates data availability, history, quality, and liquidity without checking Wyckoff setups.
- Emits reproducible, auditable dated snapshots under data/universe_snapshots/<YYYYMMDD>/.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
from typing import Any, Final, Optional, Sequence, Union
import numpy as np
import pandas as pd

from wyckoff_screener.data.batch_downloader import BatchMarketDataDownloader
from wyckoff_screener.universe.models import (
    ExclusionReason,
    UniverseBuildReport,
    UniverseSecurityRecord,
)
from wyckoff_screener.universe.nse_symbols import (
    DEFAULT_ELIGIBLE_SERIES,
    VALID_SYMBOL_REGEX,
    YAHOO_NSE_SUFFIX,
    format_yfinance_nse_ticker,
)
from wyckoff_screener.universe.sources import (
    LocalCsvUniverseSource,
    RawUniverseData,
    UniverseSource,
    get_universe_source,
)

DEFAULT_MIN_BARS: Final[int] = 60
DEFAULT_MAX_ZERO_VOLUME_PCT: Final[float] = 10.0
DEFAULT_MIN_AVG_TURNOVER_CR: Final[float] = 1.0


@dataclass
class ResearchUniverseBuildResult:
    """Outcome of building a broad research universe."""

    report: UniverseBuildReport
    eligible_records: list[UniverseSecurityRecord] = field(default_factory=list)
    excluded_records: list[UniverseSecurityRecord] = field(default_factory=list)
    all_records: list[UniverseSecurityRecord] = field(default_factory=list)

    def get_eligible_tickers(self) -> list[str]:
        """Return list of yfinance tickers for all research-eligible securities."""
        return [rec.yfinance_ticker for rec in self.eligible_records]


def build_research_universe(
    source: Union[UniverseSource, str],
    output_base_dir: Union[str, Path] = "data/universe_snapshots",
    downloader: Optional[BatchMarketDataDownloader] = None,
    eligible_series: Sequence[str] = DEFAULT_ELIGIBLE_SERIES,
    min_bars: int = DEFAULT_MIN_BARS,
    max_zero_volume_pct: float = DEFAULT_MAX_ZERO_VOLUME_PCT,
    min_avg_turnover_cr: float = DEFAULT_MIN_AVG_TURNOVER_CR,
    custom_date_tag: Optional[str] = None,
    evaluate_data_layer: bool = True,
    preloaded_ohlcv_dict: Optional[dict[str, pd.DataFrame]] = None,
) -> ResearchUniverseBuildResult:
    """Construct, validate, and snapshot the Broad NSE EQ Research Universe.

    Lifecycle:
      1. Fetch raw constituent records from UniverseSource.
      2. Normalize schema and validate symbol syntax & series eligibility.
      3. Evaluate data availability, history sufficiency, quality, and liquidity.
      4. Compute deterministic research eligibility (excluding any setup qualification).
      5. Write reproducible snapshot (source.csv, eligible.csv, excluded.csv, universe_report.json).

    Args:
        source: UniverseSource instance or registered source string ('sample', 'nse_eq', 'custom_csv').
        output_base_dir: Base directory for snapshot storage.
        downloader: Optional BatchMarketDataDownloader instance.
        eligible_series: Allowed equity series (default ('EQ',)).
        min_bars: Minimum historical bars required (default 60).
        max_zero_volume_pct: Maximum allowed zero-volume session percentage (default 10.0%).
        min_avg_turnover_cr: Minimum 20-day rolling avg daily turnover in Crores (default 1.0 Cr).
        custom_date_tag: Optional custom snapshot subfolder name (defaults to YYYYMMDD).
        evaluate_data_layer: If True, evaluates OHLCV data quality & liquidity.
        preloaded_ohlcv_dict: Optional dictionary mapping ticker -> DataFrame (useful for testing/fast mock).

    Returns:
        ResearchUniverseBuildResult containing records and detailed audit report.
    """
    # 1. Resolve source
    universe_src: UniverseSource
    if isinstance(source, str):
        universe_src = get_universe_source(source)
    else:
        universe_src = source

    raw_data: RawUniverseData = universe_src.fetch_raw_records()
    build_time = datetime.now(timezone.utc)
    date_tag = custom_date_tag or build_time.strftime("%Y%m%d")
    snapshot_dir = Path(output_base_dir) / date_tag
    snapshot_dir.mkdir(parents=True, exist_ok=True)

    if not raw_data.fetch_success or raw_data.dataframe.empty:
        # Structured source failure without fabricating fake records
        report = UniverseBuildReport(
            source_name=universe_src.source_name,
            source_date=raw_data.source_date,
            snapshot_dir=str(snapshot_dir),
            total_source_records=0,
            valid_symbol_count=0,
            eq_series_count=0,
            rejected_non_eq_count=0,
            duplicate_count=0,
            missing_fields_count=0,
            data_fetch_attempted=0,
            data_success_count=0,
            data_failure_count=0,
            insufficient_history_count=0,
            data_quality_failure_count=0,
            liquidity_failure_count=0,
            final_research_eligible_count=0,
            final_excluded_count=0,
            rejections_by_reason={"SOURCE_FETCH_FAILED": 1},
        )
        report_path = snapshot_dir / "universe_report.json"
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(report.to_dict(), f, indent=2)
        return ResearchUniverseBuildResult(report=report)

    df_raw = raw_data.dataframe.copy()
    # Save raw source snapshot
    raw_source_path = snapshot_dir / "source.csv"
    df_raw.to_csv(raw_source_path, index=False)

    # 2. Normalize column headers
    col_mapping: dict[str, str] = {}
    for col in df_raw.columns:
        norm = str(col).strip().lower().replace(" ", "_")
        if norm in ("symbol", "ticker", "security_symbol"):
            col_mapping[col] = "symbol"
        elif norm in ("company_name", "name_of_company", "security_name", "company"):
            col_mapping[col] = "company_name"
        elif norm in ("series", "equity_series", "security_series"):
            col_mapping[col] = "series"
        elif norm in ("exchange", "market"):
            col_mapping[col] = "exchange"

    df = df_raw.rename(columns=col_mapping)
    eligible_series_set = {s.strip().upper() for s in eligible_series}

    all_records: list[UniverseSecurityRecord] = []
    seen_symbols: set[str] = set()

    total_source = len(df)
    valid_symbol_count = 0
    eq_series_count = 0
    rejected_non_eq_count = 0
    duplicate_count = 0
    missing_fields_count = 0

    rejections_by_reason: dict[str, int] = {}

    def _record_rejection(reason: ExclusionReason, detail: str, record: UniverseSecurityRecord) -> None:
        record.primary_exclusion_reason = reason.value
        record.exclusion_details.append(detail)
        record.is_research_eligible = False
        rejections_by_reason[reason.value] = rejections_by_reason.get(reason.value, 0) + 1

    # Ingestion and Symbol/Series Validation
    for idx, row in df.iterrows():
        raw_sym = row.get("symbol")
        raw_company = row.get("company_name", "")
        raw_series = row.get("series")
        raw_exchange = row.get("exchange", "NSE")

        # Missing required field
        if pd.isna(raw_sym) or not str(raw_sym).strip() or pd.isna(raw_series) or not str(raw_series).strip():
            missing_fields_count += 1
            rec = UniverseSecurityRecord(
                symbol=str(raw_sym) if pd.notna(raw_sym) else f"MISSING_{idx}",
                company_name=str(raw_company) if pd.notna(raw_company) else "",
                series=str(raw_series) if pd.notna(raw_series) else "",
                exchange=str(raw_exchange) if pd.notna(raw_exchange) else "NSE",
                yfinance_ticker="",
                source_date=raw_data.source_date,
                universe_source=universe_src.source_name,
                is_valid_symbol=False,
                is_eligible_series=False,
            )
            _record_rejection(
                ExclusionReason.MISSING_REQUIRED_FIELDS,
                f"Row {idx} is missing mandatory symbol or series field.",
                rec,
            )
            all_records.append(rec)
            continue

        clean_sym = str(raw_sym).strip().upper()
        clean_series = str(raw_series).strip().upper()
        clean_company = str(raw_company).strip() if pd.notna(raw_company) else clean_sym
        clean_exchange = str(raw_exchange).strip().upper() if pd.notna(raw_exchange) else "NSE"
        yfinance_ticker = format_yfinance_nse_ticker(clean_sym)

        # Check symbol syntax
        base_sym = clean_sym[:-3] if clean_sym.endswith(YAHOO_NSE_SUFFIX) else clean_sym
        is_valid_sym = bool(VALID_SYMBOL_REGEX.match(base_sym))
        is_eq = clean_series in eligible_series_set
        is_dup = clean_sym in seen_symbols

        rec = UniverseSecurityRecord(
            symbol=clean_sym,
            company_name=clean_company,
            series=clean_series,
            exchange=clean_exchange,
            yfinance_ticker=yfinance_ticker,
            source_date=raw_data.source_date,
            universe_source=universe_src.source_name,
            is_valid_symbol=is_valid_sym,
            is_eligible_series=is_eq,
            is_duplicate=is_dup,
        )

        if not is_valid_sym:
            _record_rejection(
                ExclusionReason.INVALID_SYMBOL,
                f"Symbol '{clean_sym}' violates format regex {VALID_SYMBOL_REGEX.pattern}.",
                rec,
            )
        elif not is_eq:
            rejected_non_eq_count += 1
            _record_rejection(
                ExclusionReason.NON_EQ_SERIES,
                f"Series '{clean_series}' is not in eligible series {tuple(eligible_series_set)}.",
                rec,
            )
        elif is_dup:
            duplicate_count += 1
            _record_rejection(
                ExclusionReason.DUPLICATE_SYMBOL,
                f"Duplicate symbol '{clean_sym}' encountered in universe source.",
                rec,
            )
        else:
            valid_symbol_count += 1
            eq_series_count += 1
            seen_symbols.add(clean_sym)

        all_records.append(rec)

    # 3. Evaluate Data Availability, History, Quality, and Liquidity
    data_fetch_attempted = 0
    data_success_count = 0
    data_failure_count = 0
    insufficient_history_count = 0
    data_quality_failure_count = 0
    liquidity_failure_count = 0

    if evaluate_data_layer:
        market_downloader = downloader or BatchMarketDataDownloader(cache_dir="data/cache")

        # Only evaluate records that passed universe-level gates (valid symbol, EQ series, non-duplicate)
        for rec in all_records:
            if not (rec.is_valid_symbol and rec.is_eligible_series and not rec.is_duplicate):
                continue

            data_fetch_attempted += 1
            df_ohlcv: Optional[pd.DataFrame] = None

            if preloaded_ohlcv_dict and rec.yfinance_ticker in preloaded_ohlcv_dict:
                df_ohlcv = preloaded_ohlcv_dict[rec.yfinance_ticker]
            else:
                try:
                    df_ohlcv = market_downloader.get_ticker_data(rec.yfinance_ticker)
                except Exception as exc:
                    rec.has_data_available = False
                    data_failure_count += 1
                    _record_rejection(
                        ExclusionReason.DATA_DOWNLOAD_FAILED,
                        f"Data download error for {rec.yfinance_ticker}: {exc}",
                        rec,
                    )
                    continue

            if df_ohlcv is None or df_ohlcv.empty:
                rec.has_data_available = False
                data_failure_count += 1
                _record_rejection(
                    ExclusionReason.EMPTY_DATA,
                    f"No price/volume data returned for {rec.yfinance_ticker}.",
                    rec,
                )
                continue

            # Check required OHLCV columns
            required_cols = {"Date", "Open", "High", "Low", "Close", "Volume"}
            missing_cols = required_cols - set(df_ohlcv.columns)
            if missing_cols:
                rec.has_data_available = False
                data_failure_count += 1
                _record_rejection(
                    ExclusionReason.MISSING_REQUIRED_COLUMNS,
                    f"Missing required columns {missing_cols} in OHLCV DataFrame.",
                    rec,
                )
                continue

            rec.has_data_available = True
            rec.data_bars_count = len(df_ohlcv)

            # Check history threshold
            if len(df_ohlcv) < min_bars:
                rec.has_sufficient_history = False
                insufficient_history_count += 1
                _record_rejection(
                    ExclusionReason.INSUFFICIENT_HISTORY,
                    f"Available bars ({len(df_ohlcv)}) is below minimum requirement ({min_bars}).",
                    rec,
                )
                continue

            rec.has_sufficient_history = True

            # Check data quality
            zero_vol_rate = float((df_ohlcv["Volume"] == 0).sum() / len(df_ohlcv) * 100.0)
            rec.zero_volume_pct = round(zero_vol_rate, 2)

            quality_errors: list[str] = []
            if zero_vol_rate >= max_zero_volume_pct:
                quality_errors.append(
                    f"Zero-volume session percentage ({zero_vol_rate:.1f}%) exceeds maximum ({max_zero_volume_pct}%)."
                )

            # Check price validity (non-positive prices)
            for p_col in ["Open", "High", "Low", "Close"]:
                if p_col in df_ohlcv.columns and (df_ohlcv[p_col] <= 0).any():
                    quality_errors.append(f"Non-positive prices found in {p_col} series.")

            # Check impossible OHLC candle logic
            invalid_hl = (df_ohlcv["High"] < df_ohlcv["Low"]).sum()
            invalid_ho = (df_ohlcv["High"] < df_ohlcv["Open"]).sum()
            invalid_hc = (df_ohlcv["High"] < df_ohlcv["Close"]).sum()
            invalid_lo = (df_ohlcv["Low"] > df_ohlcv["Open"]).sum()
            invalid_lc = (df_ohlcv["Low"] > df_ohlcv["Close"]).sum()

            total_impossible = invalid_hl + invalid_ho + invalid_hc + invalid_lo + invalid_lc
            if total_impossible > 0:
                quality_errors.append(
                    f"Impossible candle geometry found ({invalid_hl} High<Low, {invalid_ho} High<Open, "
                    f"{invalid_hc} High<Close, {invalid_lo} Low>Open, {invalid_lc} Low>Close)."
                )

            if quality_errors:
                rec.has_acceptable_data_quality = False
                data_quality_failure_count += 1
                _record_rejection(
                    ExclusionReason.DATA_QUALITY_FAILURE,
                    " | ".join(quality_errors),
                    rec,
                )
                continue

            rec.has_acceptable_data_quality = True
            data_success_count += 1

            # Check Liquidity
            tail_20 = df_ohlcv.tail(20)
            avg_20_turnover = float((tail_20["Close"] * tail_20["Volume"] / 10_000_000.0).mean())
            rec.avg_20_daily_turnover_cr = round(avg_20_turnover, 2)

            if avg_20_turnover < min_avg_turnover_cr:
                rec.passes_liquidity = False
                liquidity_failure_count += 1
                _record_rejection(
                    ExclusionReason.LIQUIDITY_FAILURE,
                    f"20-day avg daily turnover (₹{avg_20_turnover:.2f} Cr) is below minimum (₹{min_avg_turnover_cr:.2f} Cr).",
                    rec,
                )
                continue

            rec.passes_liquidity = True
            rec.evaluate_research_eligibility()
    else:
        for rec in all_records:
            if rec.is_valid_symbol and rec.is_eligible_series and not rec.is_duplicate:
                rec.is_research_eligible = True
    eligible_records = [r for r in all_records if r.is_research_eligible]
    excluded_records = [r for r in all_records if not r.is_research_eligible]

    # Save eligible and excluded CSV snapshots
    df_eligible = pd.DataFrame([r.to_dict() for r in eligible_records])
    df_excluded = pd.DataFrame([r.to_dict() for r in excluded_records])

    eligible_csv_path = snapshot_dir / "eligible.csv"
    excluded_csv_path = snapshot_dir / "excluded.csv"

    df_eligible.to_csv(eligible_csv_path, index=False)
    df_excluded.to_csv(excluded_csv_path, index=False)

    # 5. Build Audit Report
    report = UniverseBuildReport(
        source_name=universe_src.source_name,
        source_date=raw_data.source_date,
        snapshot_dir=str(snapshot_dir),
        total_source_records=total_source,
        valid_symbol_count=valid_symbol_count,
        eq_series_count=eq_series_count,
        rejected_non_eq_count=rejected_non_eq_count,
        duplicate_count=duplicate_count,
        missing_fields_count=missing_fields_count,
        data_fetch_attempted=data_fetch_attempted,
        data_success_count=data_success_count,
        data_failure_count=data_failure_count,
        insufficient_history_count=insufficient_history_count,
        data_quality_failure_count=data_quality_failure_count,
        liquidity_failure_count=liquidity_failure_count,
        final_research_eligible_count=len(eligible_records),
        final_excluded_count=len(excluded_records),
        rejections_by_reason=rejections_by_reason,
    )

    report_json_path = snapshot_dir / "universe_report.json"
    with open(report_json_path, "w", encoding="utf-8") as f:
        json.dump(report.to_dict(), f, indent=2)

    return ResearchUniverseBuildResult(
        report=report,
        eligible_records=eligible_records,
        excluded_records=excluded_records,
        all_records=all_records,
    )
