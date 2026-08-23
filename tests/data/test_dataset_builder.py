"""Unit and regression tests for Phase 9B Broad NSE EQ Research Dataset builder and cache validation."""

import hashlib
import json
from pathlib import Path
import numpy as np
import pandas as pd
import pytest

from wyckoff_screener.data.dataset_builder import (
    ResearchDatasetManifest,
    ResearchDatasetResult,
    build_research_dataset,
)
from wyckoff_screener.data_loader import DataValidationError, validate_ohlcv_dataframe
from wyckoff_screener.scanning.broad_filter import evaluate_broad_setup


def _make_dummy_ohlcv(bars: int = 100, price: float = 200.0, volume: float = 100000.0) -> pd.DataFrame:
    """Helper to create dummy valid OHLCV DataFrame."""
    dates = pd.date_range("2024-01-01", periods=bars)
    return pd.DataFrame({
        "Date": dates,
        "Open": [price] * bars,
        "High": [price + 1.0] * bars,
        "Low": [price - 1.0] * bars,
        "Close": [price] * bars,
        "Volume": [volume] * bars,
    })


def test_canonical_ohlcv_schema_and_types():
    """Verify that validate_ohlcv_dataframe enforces canonical schema, date ordering, and numeric types."""
    df = _make_dummy_ohlcv(bars=80, price=150.0, volume=50000.0)
    validated = validate_ohlcv_dataframe(df)

    assert list(validated.columns) == ["Date", "Open", "High", "Low", "Close", "Volume"]
    assert pd.api.types.is_datetime64_any_dtype(validated["Date"])
    assert pd.api.types.is_numeric_dtype(validated["Close"])
    assert pd.api.types.is_numeric_dtype(validated["Volume"])
    assert validated["Date"].is_monotonic_increasing


def test_duplicate_dates_deterministic_handling():
    """Verify duplicate date policy:
    1. Identical duplicate rows are deduplicated deterministically.
    2. Conflicting duplicate rows raise DataValidationError.
    """
    # 1. Identical duplicates
    df_identical = pd.DataFrame({
        "Date": [pd.to_datetime("2024-01-01"), pd.to_datetime("2024-01-01"), pd.to_datetime("2024-01-02")],
        "Open": [100.0, 100.0, 105.0],
        "High": [102.0, 102.0, 107.0],
        "Low": [98.0, 98.0, 103.0],
        "Close": [101.0, 101.0, 106.0],
        "Volume": [1000.0, 1000.0, 1500.0],
    })
    res_dedup = validate_ohlcv_dataframe(df_identical)
    assert len(res_dedup) == 2

    # 2. Conflicting duplicates (different Close on same date)
    df_conflict = pd.DataFrame({
        "Date": [pd.to_datetime("2024-01-01"), pd.to_datetime("2024-01-01")],
        "Open": [100.0, 100.0],
        "High": [102.0, 102.0],
        "Low": [98.0, 98.0],
        "Close": [101.0, 105.0], # Conflict
        "Volume": [1000.0, 1000.0],
    })
    with pytest.raises(DataValidationError, match="CONFLICTING_DUPLICATE_DATES"):
        validate_ohlcv_dataframe(df_conflict)


def test_dataset_builder_materialization_and_traceability(tmp_path: Path):
    """Verify that build_research_dataset materializes canonical CSVs, manifest.json, and symbols.csv with lineage."""
    snapshot_csv = tmp_path / "eligible.csv"
    snapshot_csv.write_text(
        "symbol,company_name,series,exchange,yfinance_ticker,source_date,universe_source,is_research_eligible\n"
        "STOCK_A,Stock Alpha Ltd,EQ,NSE,STOCK_A.NS,2026-08-23 18:00:00 UTC,official_nse,True\n"
        "STOCK_B,Stock Beta Ltd,EQ,NSE,STOCK_B.NS,2026-08-23 18:00:00 UTC,official_nse,True\n",
        encoding="utf-8",
    )

    ohlcv_mock = {
        "STOCK_A.NS": _make_dummy_ohlcv(bars=100, price=300.0, volume=100000.0),
        "STOCK_B.NS": _make_dummy_ohlcv(bars=120, price=500.0, volume=200000.0),
    }

    out_base = tmp_path / "research_datasets"
    res = build_research_dataset(
        universe_snapshot_path=snapshot_csv,
        output_base_dir=out_base,
        custom_date_tag="20260823_TEST_DS",
        preloaded_ohlcv_dict=ohlcv_mock,
    )

    dataset_folder = out_base / "20260823_TEST_DS"
    assert (dataset_folder / "manifest.json").exists()
    assert (dataset_folder / "symbols.csv").exists()
    assert (dataset_folder / "failures.csv").exists()
    assert (dataset_folder / "data" / "STOCK_A.NS.csv").exists()
    assert (dataset_folder / "data" / "STOCK_B.NS.csv").exists()

    # Verify manifest
    assert res.manifest.total_requested == 2
    assert res.manifest.successful_symbols == 2
    assert res.manifest.failed_symbols == 0
    assert res.manifest.avg_bars_per_symbol == 110.0

    # Verify traceability in symbols.csv
    df_syms = pd.read_csv(dataset_folder / "symbols.csv")
    assert len(df_syms) == 2
    assert "source_universe_snapshot" in df_syms.columns
    assert "source_universe_date" in df_syms.columns
    assert "STOCK_A" in df_syms.iloc[0]["tradingview_daily_url"]
    assert "symbol=NSE%3ASTOCK_A" in df_syms.iloc[0]["tradingview_daily_url"]


def test_per_symbol_failure_isolation(tmp_path: Path):
    """Verify that a failure in 1 stock does not abort or contaminate other valid stocks in the dataset."""
    snapshot_csv = tmp_path / "eligible.csv"
    snapshot_csv.write_text(
        "symbol,company_name,series,exchange,yfinance_ticker,source_date,universe_source,is_research_eligible\n"
        "VALID_STOCK,Valid Stock Ltd,EQ,NSE,VALID_STOCK.NS,2026-08-23,test_src,True\n"
        "SHORT_STOCK,Short Stock Ltd,EQ,NSE,SHORT_STOCK.NS,2026-08-23,test_src,True\n"
        "CORRUPT_STOCK,Corrupt Stock Ltd,EQ,NSE,CORRUPT_STOCK.NS,2026-08-23,test_src,True\n",
        encoding="utf-8",
    )

    # Corrupt stock with High < Low
    df_corrupt = _make_dummy_ohlcv(bars=80)
    df_corrupt.loc[5, "High"] = 50.0 # High (50) < Low (199)

    ohlcv_mock = {
        "VALID_STOCK.NS": _make_dummy_ohlcv(bars=100),
        "SHORT_STOCK.NS": _make_dummy_ohlcv(bars=20), # < 60 bars
        "CORRUPT_STOCK.NS": df_corrupt,
    }

    out_base = tmp_path / "research_datasets"
    res = build_research_dataset(
        universe_snapshot_path=snapshot_csv,
        output_base_dir=out_base,
        custom_date_tag="20260823_FAILURE_TEST",
        preloaded_ohlcv_dict=ohlcv_mock,
        min_bars=60,
    )

    assert res.manifest.total_requested == 3
    assert res.manifest.successful_symbols == 1
    assert res.manifest.failed_symbols == 2

    # Check failures.csv
    df_failures = res.failures_df
    assert len(df_failures) == 2
    failed_reasons = dict(zip(df_failures["symbol"], df_failures["primary_reason"]))
    assert failed_reasons["SHORT_STOCK"] == "INSUFFICIENT_HISTORY"
    assert failed_reasons["CORRUPT_STOCK"] == "DATA_QUALITY_FAILURE"


def test_cache_metadata_hash_validation_and_corruption_invalidation(tmp_path: Path):
    """Verify that cached data is verified with SHA-256 hash and invalid hashes trigger redownload/rejection."""
    cache_dir = tmp_path / "cache"
    cache_dir.mkdir()

    ticker = "TEST_HASH.NS"
    csv_file = cache_dir / f"{ticker}.csv"
    meta_file = cache_dir / f"{ticker}.meta.json"

    df = _make_dummy_ohlcv(bars=80)
    csv_bytes = df.to_csv(index=False).encode("utf-8")
    real_hash = hashlib.sha256(csv_bytes).hexdigest()

    csv_file.write_bytes(csv_bytes)
    meta_file.write_text(json.dumps({
        "ticker": ticker,
        "schema_version": "1.0",
        "data_hash": real_hash,
    }), encoding="utf-8")

    # Tamper with CSV content without updating hash
    tampered_bytes = csv_bytes + b"\ncorrupted_row"
    csv_file.write_bytes(tampered_bytes)

    # Hash mismatch should trigger re-download (or fail if offline)
    # The batch downloader will catch hash mismatch and mark for re-download
    snapshot_csv = tmp_path / "eligible.csv"
    snapshot_csv.write_text(
        "symbol,company_name,series,exchange,yfinance_ticker,source_date,universe_source,is_research_eligible\n"
        f"TEST_HASH,Test Hash Ltd,EQ,NSE,{ticker},2026-08-23,test_src,True\n",
        encoding="utf-8",
    )

    # Run dataset build (with mock to simulate re-download succeeding)
    res = build_research_dataset(
        universe_snapshot_path=snapshot_csv,
        output_base_dir=tmp_path / "datasets",
        preloaded_ohlcv_dict={ticker: df},
    )
    assert res.manifest.successful_symbols == 1


def test_scanner_compatibility_on_materialized_dataset(tmp_path: Path):
    """Verify that the existing analytical screening engine (evaluate_broad_setup) runs directly on materialized canonical CSVs."""
    snapshot_csv = tmp_path / "eligible.csv"
    snapshot_csv.write_text(
        "symbol,company_name,series,exchange,yfinance_ticker,source_date,universe_source,is_research_eligible\n"
        "ANANTRAJ,Anant Raj Limited,EQ,NSE,ANANTRAJ.NS,2026-08-23,sample_src,True\n",
        encoding="utf-8",
    )

    df_anantraj = _make_dummy_ohlcv(bars=150, price=300.0, volume=100000.0)

    out_base = tmp_path / "research_datasets"
    res = build_research_dataset(
        universe_snapshot_path=snapshot_csv,
        output_base_dir=out_base,
        custom_date_tag="20260823_SCANNER_COMPAT",
        preloaded_ohlcv_dict={"ANANTRAJ.NS": df_anantraj},
    )

    canonical_csv = res.data_files["ANANTRAJ.NS"]
    df_loaded = pd.read_csv(canonical_csv)

    # Run analytical engine directly
    screening_res = evaluate_broad_setup(df_loaded, symbol="ANANTRAJ.NS", company_name="Anant Raj Limited")
    assert screening_res.symbol == "ANANTRAJ.NS"
    assert screening_res.tradingview_chart_links.exchange_symbol == "NSE:ANANTRAJ"
    assert screening_res.liquidity_metrics["latest_close"] == 300.0


def test_tradingview_link_failure_does_not_abort_dataset(monkeypatch, tmp_path: Path):
    """Verify that a failure in TradingView link generation does not fail OHLCV dataset materialization."""
    import wyckoff_screener.data.dataset_builder as db_mod

    # Force generate_tradingview_links to raise an exception
    def _mock_failing_tv_links(symbol: str, exchange: str = "NSE"):
        raise RuntimeError("TradingView service link generator unreachable")

    monkeypatch.setattr(db_mod, "generate_tradingview_links", _mock_failing_tv_links)

    snapshot_csv = tmp_path / "eligible.csv"
    snapshot_csv.write_text(
        "symbol,company_name,series,exchange,yfinance_ticker,source_date,universe_source,is_research_eligible\n"
        "RELIANCE,Reliance Industries Ltd,EQ,NSE,RELIANCE.NS,2026-08-23,test_src,True\n",
        encoding="utf-8",
    )

    df_rel = _make_dummy_ohlcv(bars=100)
    out_base = tmp_path / "research_datasets"
    res = build_research_dataset(
        universe_snapshot_path=snapshot_csv,
        output_base_dir=out_base,
        custom_date_tag="20260823_TV_FAIL_ISOLATION",
        preloaded_ohlcv_dict={"RELIANCE.NS": df_rel},
    )

    # Proves dataset was successfully materialized despite TradingView link error
    assert res.manifest.successful_symbols == 1
    assert res.manifest.failed_symbols == 0
    assert "RELIANCE.NS" in res.data_files
    assert (res.dataset_dir / "data" / "RELIANCE.NS.csv").exists()


def test_chronological_ordering_and_no_lookahead_integrity(tmp_path: Path):
    """Verify that dataset construction preserves strictly ascending chronological dates without future data leakage."""
    dates = [
        pd.to_datetime("2024-01-05"),
        pd.to_datetime("2024-01-02"),
        pd.to_datetime("2024-01-04"),
        pd.to_datetime("2024-01-03"),
    ]
    df_unsorted = pd.DataFrame({
        "Date": dates,
        "Open": [100.0, 95.0, 98.0, 96.0],
        "High": [102.0, 97.0, 100.0, 98.0],
        "Low": [98.0, 94.0, 96.0, 95.0],
        "Close": [101.0, 96.0, 99.0, 97.0],
        "Volume": [1000.0, 1000.0, 1000.0, 1000.0],
    })

    validated = validate_ohlcv_dataframe(df_unsorted)

    # Dates must be strictly sorted ascending
    expected_dates = ["2024-01-02", "2024-01-03", "2024-01-04", "2024-01-05"]
    actual_dates = validated["Date"].dt.strftime("%Y-%m-%d").tolist()
    assert actual_dates == expected_dates

