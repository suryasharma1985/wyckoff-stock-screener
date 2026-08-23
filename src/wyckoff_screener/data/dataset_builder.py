"""Broad NSE EQ Research Dataset builder, cache orchestrator, and manifest engine.

Guiding Principles:
- Dataset Construction Only: Materializes validated canonical OHLCV datasets for all research-eligible securities.
- Strict point-in-time chronological discipline.
- TradingView URLs attached purely as an optional human visual review layer.
- Complete per-symbol failure isolation with structured manifest and failures.csv.
"""

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
from typing import Any, Final, Optional, Sequence, Union
import numpy as np
import pandas as pd

from wyckoff_screener.charting.tradingview_links import generate_tradingview_links
from wyckoff_screener.data.batch_downloader import (
    DEFAULT_CACHE_DIR,
    DEFAULT_MIN_BARS,
    DEFAULT_START_DATE,
    BatchDownloadResult,
    BatchMarketDataDownloader,
)
from wyckoff_screener.data_loader import DataValidationError, validate_ohlcv_dataframe

SCHEMA_VERSION: Final[str] = "1.0"
DEFAULT_ADJUSTMENT_POLICY: Final[str] = "split_adjusted_ohlc_raw_volume"
DEFAULT_DATASET_BASE_DIR: Final[str] = "data/research_datasets"


@dataclass
class ResearchDatasetManifest:
    """Complete machine-readable audit manifest for a research dataset snapshot."""

    dataset_id: str
    source_universe_snapshot: str
    source_universe_date: str
    generated_at_utc: str
    data_provider: str = "yfinance"
    adjustment_policy: str = DEFAULT_ADJUSTMENT_POLICY
    frequency: str = "1d"
    requested_start_date: str = DEFAULT_START_DATE
    requested_end_date: str = "latest"
    schema_version: str = SCHEMA_VERSION
    total_requested: int = 0
    successful_symbols: int = 0
    failed_symbols: int = 0
    cache_hits: int = 0
    fresh_downloads: int = 0
    validation_failures: int = 0
    earliest_available_date: str = "N/A"
    latest_available_date: str = "N/A"
    avg_bars_per_symbol: float = 0.0
    median_bars_per_symbol: float = 0.0
    min_bars_observed: int = 0
    max_bars_observed: int = 0
    minimum_history_requirement: int = DEFAULT_MIN_BARS
    notes: str = (
        "OPTIONAL VISUAL REVIEW LAYER NOTICE: TradingView chart links in symbols.csv are provided "
        "solely for optional human visual inspection. TradingView is not a data source, analytical "
        "prerequisite, or component of quantitative screening."
    )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ResearchDatasetResult:
    """Outcome of materializing a broad research dataset."""

    manifest: ResearchDatasetManifest
    symbols_df: pd.DataFrame
    failures_df: pd.DataFrame
    dataset_dir: Path
    data_files: dict[str, Path] = field(default_factory=dict)


def build_research_dataset(
    universe_snapshot_path: Union[str, Path] = "data/universe_snapshots/latest/eligible.csv",
    output_base_dir: Union[str, Path] = DEFAULT_DATASET_BASE_DIR,
    custom_date_tag: Optional[str] = None,
    start_date: str = DEFAULT_START_DATE,
    end_date: Optional[str] = None,
    min_bars: int = DEFAULT_MIN_BARS,
    downloader: Optional[BatchMarketDataDownloader] = None,
    preloaded_ohlcv_dict: Optional[dict[str, pd.DataFrame]] = None,
    force_refresh: bool = False,
) -> ResearchDatasetResult:
    """Construct, validate, and materialize a canonical research dataset from a Phase 9A universe snapshot.

    Args:
        universe_snapshot_path: Path to Phase 9A eligible.csv or universe CSV.
        output_base_dir: Base directory for storing dataset snapshots.
        custom_date_tag: Optional folder name (defaults to YYYYMMDD).
        start_date: Historical start date string (YYYY-MM-DD).
        end_date: Optional end date string.
        min_bars: Minimum historical bars threshold (default 60).
        downloader: Optional BatchMarketDataDownloader instance.
        preloaded_ohlcv_dict: Optional dictionary of mock DataFrames for deterministic unit testing.
        force_refresh: If True, forces redownload ignoring cache.

    Returns:
        ResearchDatasetResult containing manifest, symbols metadata, failures, and file paths.
    """
    snapshot_path = Path(universe_snapshot_path)
    now_utc = datetime.now(timezone.utc)
    date_tag = custom_date_tag or now_utc.strftime("%Y%m%d")
    dataset_dir = Path(output_base_dir) / date_tag
    data_dir = dataset_dir / "data"
    data_dir.mkdir(parents=True, exist_ok=True)

    # 1. Load universe snapshot
    if not snapshot_path.exists():
        raise FileNotFoundError(f"Universe snapshot CSV not found at: {snapshot_path}")

    df_universe = pd.read_csv(snapshot_path)
    if df_universe.empty:
        raise ValueError(f"Universe snapshot CSV is empty: {snapshot_path}")

    # Normalize column names
    col_mapping: dict[str, str] = {}
    for col in df_universe.columns:
        norm = str(col).strip().lower().replace(" ", "_")
        if norm in ("symbol", "ticker", "security_symbol"):
            col_mapping[col] = "symbol"
        elif norm in ("company_name", "name_of_company", "security_name", "company"):
            col_mapping[col] = "company_name"
        elif norm in ("series", "equity_series", "security_series"):
            col_mapping[col] = "series"
        elif norm in ("yfinance_ticker", "yahoo_ticker"):
            col_mapping[col] = "yfinance_ticker"
        elif norm in ("source_date", "source_universe_date"):
            col_mapping[col] = "source_date"
        elif norm in ("universe_source", "source_name"):
            col_mapping[col] = "universe_source"

    df_u = df_universe.rename(columns=col_mapping)
    total_requested = len(df_u)

    source_date_str = str(df_u.get("source_date", [str(now_utc.strftime("%Y-%m-%d %H:%M:%S UTC"))])[0])
    source_snapshot_name = str(snapshot_path.as_posix())

    # Prepare download list
    tickers_to_process: list[tuple[str, str, str, str]] = [] # (symbol, yfinance_ticker, company_name, series)
    for _, row in df_u.iterrows():
        sym = str(row.get("symbol", "")).strip().upper()
        comp = str(row.get("company_name", sym)).strip()
        ser = str(row.get("series", "EQ")).strip().upper()
        yf_ticker = str(row.get("yfinance_ticker", f"{sym}.NS")).strip().upper()
        if not yf_ticker.endswith(".NS"):
            yf_ticker = f"{yf_ticker}.NS"
        tickers_to_process.append((sym, yf_ticker, comp, ser))

    # 2. Acquire and validate data
    market_downloader = downloader or BatchMarketDataDownloader(
        cache_dir=DEFAULT_CACHE_DIR,
        start_date=start_date,
        end_date=end_date,
        min_bars=min_bars,
        force_refresh=force_refresh,
    )

    symbols_records: list[dict[str, Any]] = []
    failures_records: list[dict[str, Any]] = []
    data_files: dict[str, Path] = {}

    bar_counts: list[int] = []
    all_start_dates: list[str] = []
    all_end_dates: list[str] = []

    cache_hits = 0
    fresh_downloads = 0
    validation_failures = 0

    # Process each ticker with failure isolation
    for sym, yf_ticker, company, series in tickers_to_process:
        df_raw: Optional[pd.DataFrame] = None
        acquisition_status = "UNKNOWN"

        if preloaded_ohlcv_dict and yf_ticker in preloaded_ohlcv_dict:
            df_raw = preloaded_ohlcv_dict[yf_ticker]
            acquisition_status = "PRELOADED_MOCK"
        else:
            cache_file = Path(DEFAULT_CACHE_DIR) / f"{yf_ticker}.csv"
            cache_meta = Path(DEFAULT_CACHE_DIR) / f"{yf_ticker}.meta.json"
            had_cache = cache_file.exists() and cache_meta.exists() and not force_refresh

            try:
                df_raw = market_downloader.get_ticker_data(yf_ticker)
                if df_raw is not None and not df_raw.empty:
                    acquisition_status = "CACHE_HIT" if had_cache else "FRESH_DOWNLOAD"
                    if had_cache:
                        cache_hits += 1
                    else:
                        fresh_downloads += 1
            except Exception as exc:
                failures_records.append({
                    "symbol": sym,
                    "yfinance_ticker": yf_ticker,
                    "stage": "download",
                    "primary_reason": "DOWNLOAD_FAILED",
                    "error_message": str(exc),
                    "retries_attempted": 3,
                    "timestamp_utc": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
                })
                continue

        if df_raw is None or df_raw.empty:
            failures_records.append({
                "symbol": sym,
                "yfinance_ticker": yf_ticker,
                "stage": "data_availability",
                "primary_reason": "EMPTY_DATA",
                "error_message": f"No data returned for ticker {yf_ticker}.",
                "retries_attempted": 3,
                "timestamp_utc": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
            })
            continue

        # Validate canonical schema and OHLC geometry
        try:
            validated_df = validate_ohlcv_dataframe(df_raw, reject_duplicates=True)
        except DataValidationError as exc:
            validation_failures += 1
            failures_records.append({
                "symbol": sym,
                "yfinance_ticker": yf_ticker,
                "stage": "validation",
                "primary_reason": "DATA_QUALITY_FAILURE",
                "error_message": str(exc),
                "retries_attempted": 0,
                "timestamp_utc": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
            })
            continue
        except Exception as exc:
            validation_failures += 1
            failures_records.append({
                "symbol": sym,
                "yfinance_ticker": yf_ticker,
                "stage": "validation",
                "primary_reason": "UNEXPECTED_VALIDATION_ERROR",
                "error_message": str(exc),
                "retries_attempted": 0,
                "timestamp_utc": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
            })
            continue

        # Check minimum history requirement
        bar_count = len(validated_df)
        if bar_count < min_bars:
            validation_failures += 1
            failures_records.append({
                "symbol": sym,
                "yfinance_ticker": yf_ticker,
                "stage": "history",
                "primary_reason": "INSUFFICIENT_HISTORY",
                "error_message": f"Bar count ({bar_count}) is below minimum requirement ({min_bars}).",
                "retries_attempted": 0,
                "timestamp_utc": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
            })
            continue

        # Check zero-volume session rate
        zero_vol_rate = float((validated_df["Volume"] == 0).sum() / bar_count * 100.0)
        if zero_vol_rate >= 10.0:
            validation_failures += 1
            failures_records.append({
                "symbol": sym,
                "yfinance_ticker": yf_ticker,
                "stage": "data_quality",
                "primary_reason": "HIGH_ZERO_VOLUME_RATE",
                "error_message": f"Zero-volume session percentage ({zero_vol_rate:.1f}%) exceeds maximum 10.0%.",
                "retries_attempted": 0,
                "timestamp_utc": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
            })
            continue

        # Calculate metrics
        tail_20 = validated_df.tail(20)
        avg_20_turnover = float((tail_20["Close"] * tail_20["Volume"] / 10_000_000.0).mean())
        start_d = str(validated_df["Date"].iloc[0])[:10]
        end_d = str(validated_df["Date"].iloc[-1])[:10]

        bar_counts.append(bar_count)
        all_start_dates.append(start_d)
        all_end_dates.append(end_d)

        # Generate optional TradingView review links (strictly isolated from dataset construction)
        tv_daily_url = ""
        tv_weekly_url = ""
        tv_75m_url = ""
        try:
            tv_links = generate_tradingview_links(sym, exchange="NSE")
            tv_daily_url = tv_links.daily_url
            tv_weekly_url = tv_links.weekly_url
            tv_75m_url = tv_links.intraday_75m_url
        except Exception:
            # Failure in TradingView URL generation never fails OHLCV dataset materialization
            pass

        # Write canonical OHLCV CSV file
        out_csv_path = data_dir / f"{yf_ticker}.csv"
        validated_df.to_csv(out_csv_path, index=False)
        data_files[yf_ticker] = out_csv_path

        symbols_records.append({
            "symbol": sym,
            "yfinance_ticker": yf_ticker,
            "company_name": company,
            "series": series,
            "source_universe_snapshot": source_snapshot_name,
            "source_universe_date": source_date_str,
            "research_eligibility_status": True,
            "data_acquisition_status": acquisition_status,
            "bar_count": bar_count,
            "actual_start_date": start_d,
            "actual_end_date": end_d,
            "zero_volume_pct": round(zero_vol_rate, 2),
            "avg_20_daily_turnover_cr": round(avg_20_turnover, 2),
            "canonical_file_path": str(out_csv_path.as_posix()),
            "tradingview_daily_url": tv_daily_url,
            "tradingview_weekly_url": tv_weekly_url,
            "tradingview_75m_url": tv_75m_url,
        })

    # 3. Create DataFrames and Manifest
    df_symbols = pd.DataFrame(symbols_records)
    df_failures = pd.DataFrame(failures_records)

    symbols_csv_path = dataset_dir / "symbols.csv"
    failures_csv_path = dataset_dir / "failures.csv"
    manifest_json_path = dataset_dir / "manifest.json"

    df_symbols.to_csv(symbols_csv_path, index=False)
    df_failures.to_csv(failures_csv_path, index=False)

    earliest_date = min(all_start_dates) if all_start_dates else "N/A"
    latest_date = max(all_end_dates) if all_end_dates else "N/A"
    avg_bars = float(np.mean(bar_counts)) if bar_counts else 0.0
    med_bars = float(np.median(bar_counts)) if bar_counts else 0.0
    min_b = int(np.min(bar_counts)) if bar_counts else 0
    max_b = int(np.max(bar_counts)) if bar_counts else 0

    manifest = ResearchDatasetManifest(
        dataset_id=f"research_dataset_{date_tag}",
        source_universe_snapshot=source_snapshot_name,
        source_universe_date=source_date_str,
        generated_at_utc=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
        data_provider="yfinance",
        adjustment_policy=DEFAULT_ADJUSTMENT_POLICY,
        frequency="1d",
        requested_start_date=start_date,
        requested_end_date=end_date or "latest",
        schema_version=SCHEMA_VERSION,
        total_requested=total_requested,
        successful_symbols=len(symbols_records),
        failed_symbols=len(failures_records),
        cache_hits=cache_hits,
        fresh_downloads=fresh_downloads,
        validation_failures=validation_failures,
        earliest_available_date=earliest_date,
        latest_available_date=latest_date,
        avg_bars_per_symbol=round(avg_bars, 1),
        median_bars_per_symbol=round(med_bars, 1),
        min_bars_observed=min_b,
        max_bars_observed=max_b,
        minimum_history_requirement=min_bars,
    )

    with open(manifest_json_path, "w", encoding="utf-8") as f:
        json.dump(manifest.to_dict(), f, indent=2)

    return ResearchDatasetResult(
        manifest=manifest,
        symbols_df=df_symbols,
        failures_df=df_failures,
        dataset_dir=dataset_dir,
        data_files=data_files,
    )
