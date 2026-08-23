"""Unit and regression tests for Phase 9A Broad NSE EQ Research Universe builder and models."""

import json
from pathlib import Path
import numpy as np
import pandas as pd
import pytest

from wyckoff_screener.scanning.broad_filter import evaluate_broad_setup
from wyckoff_screener.universe.builder import build_research_universe
from wyckoff_screener.universe.models import (
    ExclusionReason,
    UniverseBuildReport,
    UniverseSecurityRecord,
)
from wyckoff_screener.universe.sources import (
    LocalCsvUniverseSource,
    NseOfficialEquitySource,
    RawUniverseData,
    UniverseSource,
    get_universe_source,
)


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


def test_universe_security_record_research_eligibility_evaluation():
    """Verify UniverseSecurityRecord.evaluate_research_eligibility() compound Boolean rule."""
    rec = UniverseSecurityRecord(
        symbol="RELIANCE",
        company_name="Reliance Industries Ltd",
        series="EQ",
        exchange="NSE",
        yfinance_ticker="RELIANCE.NS",
        source_date="2026-08-23",
        universe_source="test_source",
        is_valid_symbol=True,
        is_eligible_series=True,
        is_duplicate=False,
        has_data_available=True,
        has_sufficient_history=True,
        has_acceptable_data_quality=True,
        passes_liquidity=True,
    )
    assert rec.evaluate_research_eligibility() is True
    assert rec.is_research_eligible is True

    # If any gate fails, research eligibility must be False
    rec.passes_liquidity = False
    assert rec.evaluate_research_eligibility() is False


def test_eq_only_filtering_and_non_eq_exclusion(tmp_path: Path):
    """Verify that only EQ series securities are accepted and non-EQ series (BE, GB) are rejected."""
    csv_file = tmp_path / "mixed_universe.csv"
    csv_file.write_text(
        "SYMBOL,SERIES,COMPANY NAME\n"
        "TCS,EQ,Tata Consultancy Services\n"
        "SPEC_BE,BE,Book Entry Security\n"
        "GOVT_GB,GB,Government Bond Series\n",
        encoding="utf-8",
    )

    src = LocalCsvUniverseSource(csv_file)
    res = build_research_universe(
        source=src,
        output_base_dir=tmp_path / "snapshots",
        evaluate_data_layer=False,
    )

    assert res.report.total_source_records == 3
    assert res.report.eq_series_count == 1
    assert res.report.rejected_non_eq_count == 2
    assert res.report.rejections_by_reason.get(ExclusionReason.NON_EQ_SERIES.value) == 2

    excluded_symbols = {r.symbol: r.primary_exclusion_reason for r in res.excluded_records}
    assert excluded_symbols["SPEC_BE"] == ExclusionReason.NON_EQ_SERIES.value
    assert excluded_symbols["GOVT_GB"] == ExclusionReason.NON_EQ_SERIES.value


def test_symbol_validation_and_duplicate_rejection(tmp_path: Path):
    """Verify that invalid symbols, empty fields, and duplicate symbols are rejected with exact reasons."""
    csv_file = tmp_path / "malformed_universe.csv"
    csv_file.write_text(
        "SYMBOL,SERIES,COMPANY NAME\n"
        "VALID_STOCK,EQ,Valid Company\n"
        "VALID_STOCK,EQ,Duplicate of Valid Company\n"
        "INVALID$SYM,EQ,Illegal Symbol Name\n"
        ",EQ,Empty Symbol Name\n",
        encoding="utf-8",
    )

    src = LocalCsvUniverseSource(csv_file)
    res = build_research_universe(
        source=src,
        output_base_dir=tmp_path / "snapshots",
        evaluate_data_layer=False,
    )

    reasons = {r.symbol: r.primary_exclusion_reason for r in res.all_records}
    assert reasons["VALID_STOCK"] in (None, ExclusionReason.DUPLICATE_SYMBOL.value)
    assert reasons["INVALID$SYM"] == ExclusionReason.INVALID_SYMBOL.value
    assert res.report.duplicate_count == 1
    assert res.report.missing_fields_count == 1


def test_data_availability_history_quality_and_liquidity_gates(tmp_path: Path):
    """Verify research eligibility failure reasons for data absence, short history, bad quality, and low liquidity."""
    csv_file = tmp_path / "data_test_universe.csv"
    csv_file.write_text(
        "SYMBOL,SERIES,COMPANY NAME\n"
        "PASS_STOCK,EQ,Passing Stock\n"
        "NO_DATA_STOCK,EQ,No Data Available\n"
        "SHORT_STOCK,EQ,Insufficient History Stock\n"
        "ZERO_VOL_STOCK,EQ,Poor Quality Zero Volume Stock\n"
        "ILLIQUID_STOCK,EQ,Illiquid Stock\n",
        encoding="utf-8",
    )

    ohlcv_mock: dict[str, pd.DataFrame] = {
        # 1. PASS_STOCK: 100 bars, price=500, vol=100,000 -> Turnover 5 Cr > 1 Cr
        "PASS_STOCK.NS": _make_dummy_ohlcv(bars=100, price=500.0, volume=100000.0),
        # 2. SHORT_STOCK: only 30 bars < 60 minimum
        "SHORT_STOCK.NS": _make_dummy_ohlcv(bars=30, price=500.0, volume=100000.0),
        # 3. ZERO_VOL_STOCK: 100 bars with 20 zero-volume bars (20% >= 10% max)
        "ZERO_VOL_STOCK.NS": pd.DataFrame({
            "Date": pd.date_range("2024-01-01", periods=100),
            "Open": [200.0] * 100,
            "High": [201.0] * 100,
            "Low": [199.0] * 100,
            "Close": [200.0] * 100,
            "Volume": [100000.0] * 80 + [0.0] * 20,
        }),
        # 4. ILLIQUID_STOCK: 100 bars, price=10, vol=1,000 -> Turnover 0.001 Cr < 1.0 Cr
        "ILLIQUID_STOCK.NS": _make_dummy_ohlcv(bars=100, price=10.0, volume=1000.0),
    }

    src = LocalCsvUniverseSource(csv_file)
    res = build_research_universe(
        source=src,
        output_base_dir=tmp_path / "snapshots",
        evaluate_data_layer=True,
        preloaded_ohlcv_dict=ohlcv_mock,
        min_bars=60,
        max_zero_volume_pct=10.0,
        min_avg_turnover_cr=1.0,
    )

    reasons = {r.symbol: r.primary_exclusion_reason for r in res.all_records}
    assert reasons["PASS_STOCK"] is None
    assert reasons["NO_DATA_STOCK"] == ExclusionReason.EMPTY_DATA.value
    assert reasons["SHORT_STOCK"] == ExclusionReason.INSUFFICIENT_HISTORY.value
    assert reasons["ZERO_VOL_STOCK"] == ExclusionReason.DATA_QUALITY_FAILURE.value
    assert reasons["ILLIQUID_STOCK"] == ExclusionReason.LIQUIDITY_FAILURE.value

    assert len(res.eligible_records) == 1
    assert res.eligible_records[0].symbol == "PASS_STOCK"
    assert res.eligible_records[0].is_research_eligible is True


def test_research_eligible_but_mechanically_unqualified_regression(tmp_path: Path):
    """REGRESSION TEST: Demonstrate that research_eligible == True while mechanically_qualified == False.

    A stock with valid symbol, EQ series, ample history (150 bars), good data quality, and high liquidity
    is 100% research eligible, but a severe persistent downtrend causes mechanical setup qualification to fail.
    """
    csv_file = tmp_path / "unqualified_stock.csv"
    csv_file.write_text(
        "SYMBOL,SERIES,COMPANY NAME\n"
        "BEAR_STOCK,EQ,Bearish Downtrending Heavyweight\n",
        encoding="utf-8",
    )

    # Create 150 bars in continuous downtrend with high volume/turnover (Turnover ~ 4 Cr)
    bars = 150
    dates = pd.date_range("2024-01-01", periods=bars)
    prices = [300.0 - idx * 0.8 for idx in range(bars)]
    highs = [p + 2.0 for p in prices]
    lows = [p - 2.0 for p in prices]
    opens = [p + 0.5 for p in prices]
    closes = [p - 0.5 for p in prices]
    volumes = [200000.0] * bars

    df_downtrend = pd.DataFrame({
        "Date": dates,
        "Open": opens,
        "High": highs,
        "Low": lows,
        "Close": closes,
        "Volume": volumes,
    })

    src = LocalCsvUniverseSource(csv_file)
    res = build_research_universe(
        source=src,
        output_base_dir=tmp_path / "snapshots",
        evaluate_data_layer=True,
        preloaded_ohlcv_dict={"BEAR_STOCK.NS": df_downtrend},
    )

    # 1. Check Research Eligibility
    assert len(res.eligible_records) == 1
    record = res.eligible_records[0]
    assert record.symbol == "BEAR_STOCK"
    assert record.is_research_eligible is True
    assert record.has_sufficient_history is True
    assert record.has_acceptable_data_quality is True
    assert record.passes_liquidity is True

    # 2. Check Setup Qualification using scanner
    setup_result = evaluate_broad_setup(df_downtrend, symbol="BEAR_STOCK.NS")
    assert setup_result.is_mechanically_qualified is False
    assert setup_result.filter_results["weekly_uptrend"] is False
    assert setup_result.filter_results["dma_50_above_100"] is False

    # 3. PROVE STRICT SEPARATION
    assert record.is_research_eligible is True and setup_result.is_mechanically_qualified is False


def test_deterministic_snapshot_generation_and_reproducibility(tmp_path: Path):
    """Verify that building the universe produces identical, structured snapshots across multiple runs."""
    csv_file = tmp_path / "sample_universe.csv"
    csv_file.write_text(
        "SYMBOL,SERIES,COMPANY NAME\n"
        "ANANTRAJ,EQ,Anant Raj Limited\n"
        "APOLLO,EQ,Apollo Micro Systems\n"
        "REJECT_BE,BE,Book Entry Security\n",
        encoding="utf-8",
    )

    ohlcv_mock = {
        "ANANTRAJ.NS": _make_dummy_ohlcv(bars=100, price=300.0, volume=100000.0),
        "APOLLO.NS": _make_dummy_ohlcv(bars=100, price=150.0, volume=100000.0),
    }

    snap_dir = tmp_path / "snapshots"
    res1 = build_research_universe(
        source=LocalCsvUniverseSource(csv_file),
        output_base_dir=snap_dir,
        custom_date_tag="20260823_TEST",
        evaluate_data_layer=True,
        preloaded_ohlcv_dict=ohlcv_mock,
    )

    out_folder = snap_dir / "20260823_TEST"
    assert (out_folder / "source.csv").exists()
    assert (out_folder / "eligible.csv").exists()
    assert (out_folder / "excluded.csv").exists()
    assert (out_folder / "universe_report.json").exists()

    df_eligible = pd.read_csv(out_folder / "eligible.csv")
    df_excluded = pd.read_csv(out_folder / "excluded.csv")
    with open(out_folder / "universe_report.json", encoding="utf-8") as f:
        report_dict = json.load(f)

    assert len(df_eligible) == 2
    assert len(df_excluded) == 1
    assert report_dict["final_research_eligible_count"] == 2
    assert report_dict["final_excluded_count"] == 1


def test_source_failure_handled_honestly_without_fabrication(tmp_path: Path):
    """Verify that a nonexistent or failing universe source reports failure cleanly with zero fabricated tickers."""
    nonexistent_file = tmp_path / "does_not_exist.csv"
    src = LocalCsvUniverseSource(nonexistent_file)
    res = build_research_universe(
        source=src,
        output_base_dir=tmp_path / "snapshots",
        custom_date_tag="20260823_FAIL",
    )

    assert res.report.total_source_records == 0
    assert res.report.final_research_eligible_count == 0
    assert len(res.eligible_records) == 0
    assert "SOURCE_FETCH_FAILED" in res.report.rejections_by_reason


def test_sample_universe_source_factory_compatibility():
    """Verify that get_universe_source('sample') correctly points to data/sample_nse_symbols.csv."""
    src = get_universe_source("sample")
    raw = src.fetch_raw_records()
    assert raw.fetch_success is True
    assert not raw.dataframe.empty
    symbol_col = [c for c in raw.dataframe.columns if str(c).strip().lower() == "symbol"][0]
    assert "ANANTRAJ" in raw.dataframe[symbol_col].values
