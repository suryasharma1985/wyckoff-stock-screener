"""Batch market data downloader with local caching, validation, and structured error tracking.

Guiding Principles (AGENTS.md):
- Never download data inside an indicator, event-detection, or scoring loop.
- Fetch all required market data once upfront, validate it, and persist to local cache.
- Record every failure with ticker, stage, exception, and timestamp.
"""

from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import time
from typing import Any, Final, Optional, Sequence, Union
import numpy as np
import pandas as pd
import yfinance as yf

from wyckoff_screener.data_loader import validate_ohlcv_dataframe

DEFAULT_CACHE_DIR: Final[str] = "data/cache"
DEFAULT_START_DATE: Final[str] = "2023-01-01"
DEFAULT_MAX_RETRIES: Final[int] = 3
DEFAULT_INITIAL_BACKOFF_SEC: Final[float] = 1.0
DEFAULT_MIN_BARS: Final[int] = 60


@dataclass
class DownloadFailure:
    """Detailed record of a failed ticker download."""

    ticker: str
    stage: str
    exception_type: str
    error_message: str
    retries_attempted: int
    timestamp_utc: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "ticker": self.ticker,
            "stage": self.stage,
            "exception_type": self.exception_type,
            "error_message": self.error_message,
            "retries_attempted": self.retries_attempted,
            "timestamp_utc": self.timestamp_utc,
        }


@dataclass
class DataQualityReport:
    """Quality metrics for a downloaded/cached OHLCV DataFrame."""

    ticker: str
    bar_count: int
    start_date: str
    end_date: str
    zero_volume_bars: int
    zero_volume_pct: float
    warnings: list[str] = field(default_factory=list)


@dataclass
class BatchDownloadResult:
    """Overall outcome of a batch download run."""

    total_requested: int
    cached_count: int
    downloaded_count: int
    failed_count: int
    successful_data: dict[str, pd.DataFrame] = field(default_factory=dict)
    quality_reports: dict[str, DataQualityReport] = field(default_factory=dict)
    failures: list[DownloadFailure] = field(default_factory=list)
    cache_dir: str = DEFAULT_CACHE_DIR
    completed_at: str = field(default_factory=lambda: datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"))

    def get_dataframe(self, ticker: str) -> Optional[pd.DataFrame]:
        return self.successful_data.get(ticker)

    def to_summary_dict(self) -> dict[str, Any]:
        return {
            "total_requested": self.total_requested,
            "cached_count": self.cached_count,
            "downloaded_count": self.downloaded_count,
            "failed_count": self.failed_count,
            "cache_dir": self.cache_dir,
            "completed_at": self.completed_at,
            "failures": [f.to_dict() for f in self.failures],
        }


def _validate_data_quality(df: pd.DataFrame, ticker: str, min_bars: int = DEFAULT_MIN_BARS) -> DataQualityReport:
    """Inspect DataFrame quality and generate warnings."""
    warnings: list[str] = []
    bar_count = len(df)

    if bar_count < min_bars:
        warnings.append(f"Insufficient history: {bar_count} bars found, minimum required is {min_bars}.")

    zero_vol = int((df["Volume"] == 0).sum())
    zero_vol_pct = (zero_vol / bar_count) * 100.0 if bar_count > 0 else 0.0

    if zero_vol_pct > 10.0:
        warnings.append(f"High zero-volume rate: {zero_vol}/{bar_count} bars ({zero_vol_pct:.1f}%) have zero volume.")

    start_date_str = str(df["Date"].iloc[0])[:10] if "Date" in df.columns and bar_count > 0 else "N/A"
    end_date_str = str(df["Date"].iloc[-1])[:10] if "Date" in df.columns and bar_count > 0 else "N/A"

    return DataQualityReport(
        ticker=ticker,
        bar_count=bar_count,
        start_date=start_date_str,
        end_date=end_date_str,
        zero_volume_bars=zero_vol,
        zero_volume_pct=round(zero_vol_pct, 2),
        warnings=warnings,
    )


def _download_single_ticker_with_retry(
    ticker: str,
    start_date: str,
    end_date: Optional[str],
    interval: str = "1d",
    max_retries: int = DEFAULT_MAX_RETRIES,
    initial_backoff_sec: float = DEFAULT_INITIAL_BACKOFF_SEC,
) -> pd.DataFrame:
    """Download OHLCV for a single ticker with exponential backoff retry."""
    last_exception: Optional[Exception] = None
    backoff = initial_backoff_sec

    for attempt in range(1, max_retries + 1):
        try:
            raw = yf.download(ticker, start=start_date, end=end_date, interval=interval, progress=False)
            if raw is None or raw.empty:
                raise ValueError(f"yfinance returned empty dataset for {ticker} between {start_date} and {end_date}.")

            if isinstance(raw.columns, pd.MultiIndex):
                raw.columns = raw.columns.get_level_values(0)

            df = raw.reset_index()
            validated_df = validate_ohlcv_dataframe(df)
            return validated_df
        except Exception as exc:
            last_exception = exc
            if attempt < max_retries:
                time.sleep(backoff)
                backoff *= 2.0

    raise last_exception or RuntimeError(f"Download failed for {ticker} after {max_retries} attempts.")


def download_and_cache_universe(
    tickers: Sequence[str],
    cache_dir: Union[str, Path] = DEFAULT_CACHE_DIR,
    start_date: str = DEFAULT_START_DATE,
    end_date: Optional[str] = None,
    interval: str = "1d",
    force_refresh: bool = False,
    max_retries: int = DEFAULT_MAX_RETRIES,
    min_bars: int = DEFAULT_MIN_BARS,
    max_workers: int = 4,
) -> BatchDownloadResult:
    """Download OHLCV history once per ticker, cache locally, and track all outcomes.

    Args:
        tickers: Sequence of yfinance-compatible ticker symbols (e.g. ['ANANTRAJ.NS', 'HINDCOPPER.NS']).
        cache_dir: Local directory for caching CSVs and metadata.
        start_date: Start date string (YYYY-MM-DD).
        end_date: End date string (YYYY-MM-DD) or None for latest.
        interval: Bar interval (default '1d').
        force_refresh: If True, ignores local cache and re-downloads fresh data.
        max_retries: Maximum download retry attempts before failing.
        min_bars: Minimum historical bars threshold.
        max_workers: Thread pool concurrency limit.

    Returns:
        BatchDownloadResult containing all loaded DataFrames, quality reports, and structured failures.
    """
    cache_path = Path(cache_dir)
    cache_path.mkdir(parents=True, exist_ok=True)

    successful_data: dict[str, pd.DataFrame] = {}
    quality_reports: dict[str, DataQualityReport] = {}
    failures: list[DownloadFailure] = []

    cached_count = 0
    downloaded_count = 0
    to_download: list[str] = []

    # Step 1: Check cache first
    for ticker in tickers:
        csv_file = cache_path / f"{ticker}.csv"
        meta_file = cache_path / f"{ticker}.meta.json"

        if not force_refresh and csv_file.exists() and meta_file.exists():
            try:
                raw_df = pd.read_csv(csv_file)
                validated_df = validate_ohlcv_dataframe(raw_df)
                q_report = _validate_data_quality(validated_df, ticker, min_bars=min_bars)

                successful_data[ticker] = validated_df
                quality_reports[ticker] = q_report
                cached_count += 1
                continue
            except Exception:
                # If cached file is corrupted, schedule for re-download
                to_download.append(ticker)
        else:
            to_download.append(ticker)

    # Step 2: Batch download missing or refreshed tickers
    if to_download:
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_ticker = {
                executor.submit(
                    _download_single_ticker_with_retry,
                    ticker=ticker,
                    start_date=start_date,
                    end_date=end_date,
                    interval=interval,
                    max_retries=max_retries,
                ): ticker
                for ticker in to_download
            }

            for future in as_completed(future_to_ticker):
                ticker = future_to_ticker[future]
                try:
                    df = future.result()
                    q_report = _validate_data_quality(df, ticker, min_bars=min_bars)

                    # Persist to cache
                    csv_file = cache_path / f"{ticker}.csv"
                    meta_file = cache_path / f"{ticker}.meta.json"

                    df.to_csv(csv_file, index=False)

                    meta = {
                        "ticker": ticker,
                        "start_date": start_date,
                        "end_date": end_date or str(df["Date"].iloc[-1])[:10],
                        "interval": interval,
                        "source": "yfinance",
                        "timezone": "Asia/Kolkata",
                        "download_timestamp_utc": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
                        "bar_count": len(df),
                        "is_adjusted": True,
                    }
                    with open(meta_file, "w", encoding="utf-8") as mf:
                        json.dump(meta, mf, indent=2)

                    successful_data[ticker] = df
                    quality_reports[ticker] = q_report
                    downloaded_count += 1
                except Exception as exc:
                    now_utc = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
                    failures.append(
                        DownloadFailure(
                            ticker=ticker,
                            stage="download_and_validate",
                            exception_type=type(exc).__name__,
                            error_message=str(exc),
                            retries_attempted=max_retries,
                            timestamp_utc=now_utc,
                        )
                    )

    return BatchDownloadResult(
        total_requested=len(tickers),
        cached_count=cached_count,
        downloaded_count=downloaded_count,
        failed_count=len(failures),
        successful_data=successful_data,
        quality_reports=quality_reports,
        failures=failures,
        cache_dir=str(cache_path),
    )


class BatchMarketDataDownloader:
    """Downloader helper providing single and batch ticker caching interface."""

    def __init__(
        self,
        cache_dir: Union[str, Path] = DEFAULT_CACHE_DIR,
        start_date: str = DEFAULT_START_DATE,
        end_date: Optional[str] = None,
        interval: str = "1d",
        force_refresh: bool = False,
        max_retries: int = DEFAULT_MAX_RETRIES,
        min_bars: int = DEFAULT_MIN_BARS,
        max_workers: int = 4,
    ):
        self.cache_dir = cache_dir
        self.start_date = start_date
        self.end_date = end_date
        self.interval = interval
        self.force_refresh = force_refresh
        self.max_retries = max_retries
        self.min_bars = min_bars
        self.max_workers = max_workers

    def get_ticker_data(self, ticker: str) -> Optional[pd.DataFrame]:
        """Download or fetch single ticker from cache."""
        res = download_and_cache_universe(
            tickers=[ticker],
            cache_dir=self.cache_dir,
            start_date=self.start_date,
            end_date=self.end_date,
            interval=self.interval,
            force_refresh=self.force_refresh,
            max_retries=self.max_retries,
            min_bars=self.min_bars,
            max_workers=1,
        )
        return res.get_dataframe(ticker)

    def download_batch(self, tickers: Sequence[str]) -> BatchDownloadResult:
        """Download and cache batch of tickers."""
        return download_and_cache_universe(
            tickers=tickers,
            cache_dir=self.cache_dir,
            start_date=self.start_date,
            end_date=self.end_date,
            interval=self.interval,
            force_refresh=self.force_refresh,
            max_retries=self.max_retries,
            min_bars=self.min_bars,
            max_workers=self.max_workers,
        )

