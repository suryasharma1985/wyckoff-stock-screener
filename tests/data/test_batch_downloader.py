"""Unit tests for batch downloader, local cache, and quality report validation."""

import json
import tempfile
from pathlib import Path
import numpy as np
import pandas as pd
import pytest

from wyckoff_screener.data.batch_downloader import (
    BatchDownloadResult,
    _validate_data_quality,
    download_and_cache_universe,
)


def _create_mock_ohlcv(bars: int = 100, zero_vol_count: int = 0) -> pd.DataFrame:
    """Generate a clean synthetic OHLCV DataFrame."""
    dates = pd.date_range("2024-01-01", periods=bars)
    prices = [100.0 + i * 0.5 for i in range(bars)]
    volumes = [1000.0] * bars
    for idx in range(zero_vol_count):
        volumes[idx] = 0.0

    return pd.DataFrame({
        "Date": dates,
        "Open": [p - 0.5 for p in prices],
        "High": [p + 2.0 for p in prices],
        "Low": [p - 2.0 for p in prices],
        "Close": prices,
        "Volume": volumes,
    })


def test_validate_data_quality_warnings():
    """Verify data quality report flags insufficient history and zero-volume rates."""
    # 30 bars (less than 60 threshold) with 15 zero-volume bars (50%)
    df_poor = _create_mock_ohlcv(bars=30, zero_vol_count=15)
    report = _validate_data_quality(df_poor, ticker="TEST_POOR.NS", min_bars=60)

    assert report.bar_count == 30
    assert report.zero_volume_bars == 15
    assert report.zero_volume_pct == 50.0
    assert any("Insufficient history" in w for w in report.warnings)
    assert any("High zero-volume" in w for w in report.warnings)


def test_batch_downloader_local_cache_hit():
    """Verify batch downloader reads from local disk cache without network requests."""
    temp_dir = tempfile.mkdtemp()
    cache_path = Path(temp_dir)

    ticker = "MOCK_CACHED.NS"
    df_mock = _create_mock_ohlcv(bars=100)

    # Pre-populate cache CSV and meta JSON
    df_mock.to_csv(cache_path / f"{ticker}.csv", index=False)
    meta = {
        "ticker": ticker,
        "start_date": "2024-01-01",
        "end_date": "2024-04-10",
        "interval": "1d",
        "source": "mock_cache",
        "timezone": "Asia/Kolkata",
        "download_timestamp_utc": "2026-08-23 00:00:00 UTC",
        "bar_count": 100,
        "is_adjusted": True,
    }
    with open(cache_path / f"{ticker}.meta.json", "w", encoding="utf-8") as mf:
        json.dump(meta, mf)

    # Run batch downloader against local cache
    res = download_and_cache_universe(
        tickers=[ticker],
        cache_dir=cache_path,
        force_refresh=False,
    )

    assert res.total_requested == 1
    assert res.cached_count == 1
    assert res.downloaded_count == 0
    assert res.failed_count == 0
    assert ticker in res.successful_data
    assert len(res.successful_data[ticker]) == 100


def test_batch_downloader_records_failures_cleanly():
    """Verify that an invalid/non-existent ticker records a structured failure without crashing."""
    temp_dir = tempfile.mkdtemp()
    cache_path = Path(temp_dir)

    invalid_ticker = "NON_EXISTENT_TICKER_XYZ_123.NS"

    res = download_and_cache_universe(
        tickers=[invalid_ticker],
        cache_dir=cache_path,
        max_retries=1,
    )

    assert res.total_requested == 1
    assert res.failed_count == 1
    assert len(res.failures) == 1
    failure = res.failures[0]
    assert failure.ticker == invalid_ticker
    assert failure.stage == "download_and_validate"
    assert failure.retries_attempted == 1
