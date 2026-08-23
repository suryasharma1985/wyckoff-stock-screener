"""Unit, integration, and regression tests for Phase 9C Research Screening Engine."""

import json
from pathlib import Path
import shutil
from typing import Any
import numpy as np
import pandas as pd
import pytest

from wyckoff_screener.research.explanation import generate_candidate_explanation
from wyckoff_screener.research.models import (
    CandidateCategory,
    ResearchCandidateResult,
    ResearchScreeningManifest,
    ResearchScreeningResult,
)
from wyckoff_screener.research.screening_engine import run_research_screening


@pytest.fixture
def mock_phase_9b_dataset(tmp_path: Path) -> Path:
    """Create a synthetic Phase 9B research dataset directory with 4 test securities."""
    ds_dir = tmp_path / "mock_dataset"
    data_dir = ds_dir / "data"
    data_dir.mkdir(parents=True, exist_ok=True)

    # 1. Generate 120 bars of valid OHLCV data
    dates = pd.date_range(start="2024-01-01", periods=120, freq="B")
    
    # Stock A: High turnover, strong uptrend, bullish RSI
    df_a = pd.DataFrame({
        "Date": dates.strftime("%Y-%m-%d"),
        "Open": np.linspace(100.0, 200.0, 120),
        "High": np.linspace(102.0, 205.0, 120),
        "Low": np.linspace(99.0, 198.0, 120),
        "Close": np.linspace(101.0, 204.0, 120),
        "Volume": [500_000] * 120,
    })
    df_a.to_csv(data_dir / "STOCKA.NS.csv", index=False)

    # Stock B: Low turnover (fails liquidity gate), downtrend
    df_b = pd.DataFrame({
        "Date": dates.strftime("%Y-%m-%d"),
        "Open": np.linspace(100.0, 50.0, 120),
        "High": np.linspace(101.0, 52.0, 120),
        "Low": np.linspace(98.0, 48.0, 120),
        "Close": np.linspace(99.0, 49.0, 120),
        "Volume": [1_000] * 120,
    })
    df_b.to_csv(data_dir / "STOCKB.NS.csv", index=False)

    # Stock C: Normal stock
    df_c = pd.DataFrame({
        "Date": dates.strftime("%Y-%m-%d"),
        "Open": np.linspace(200.0, 250.0, 120),
        "High": np.linspace(205.0, 255.0, 120),
        "Low": np.linspace(195.0, 245.0, 120),
        "Close": np.linspace(202.0, 252.0, 120),
        "Volume": [300_000] * 120,
    })
    df_c.to_csv(data_dir / "STOCKC.NS.csv", index=False)

    # 2. Write symbols.csv
    symbols_df = pd.DataFrame({
        "symbol": ["STOCKA", "STOCKB", "STOCKC"],
        "yfinance_ticker": ["STOCKA.NS", "STOCKB.NS", "STOCKC.NS"],
        "company_name": ["Stock Alpha", "Stock Beta", "Stock Gamma"],
        "series": ["EQ", "EQ", "EQ"],
        "source_universe_snapshot": ["test_snapshot"] * 3,
        "source_universe_date": ["2026-08-23"] * 3,
        "research_eligibility_status": [True, True, True],
        "data_acquisition_status": ["success", "success", "success"],
        "bar_count": [120, 120, 120],
        "actual_start_date": ["2024-01-01"] * 3,
        "actual_end_date": [dates[-1].strftime("%Y-%m-%d")] * 3,
        "tradingview_daily_url": ["https://in.tradingview.com/chart/?symbol=NSE:STOCKA"] * 3,
        "tradingview_weekly_url": ["https://in.tradingview.com/chart/?symbol=NSE:STOCKA&interval=W"] * 3,
        "tradingview_75m_url": ["https://in.tradingview.com/chart/?symbol=NSE:STOCKA&interval=75"] * 3,
        "canonical_file_path": [str(data_dir / f"{s}.NS.csv") for s in ["STOCKA", "STOCKB", "STOCKC"]],
    })
    symbols_df.to_csv(ds_dir / "symbols.csv", index=False)

    # 3. Write manifest.json
    manifest_data = {
        "dataset_id": "research_dataset_mock",
        "source_universe_snapshot": "test_snapshot",
        "source_universe_date": "2026-08-23",
        "generated_at_utc": "2026-08-23 20:00:00 UTC",
        "total_requested": 3,
        "successful_symbols": 3,
        "failed_symbols": 0,
        "cache_hits": 3,
        "fresh_downloads": 0,
    }
    with open(ds_dir / "manifest.json", "w", encoding="utf-8") as f:
        json.dump(manifest_data, f, indent=2)

    return ds_dir


def test_full_dataset_screening_execution(mock_phase_9b_dataset: Path, tmp_path: Path):
    """Test standard execution of research screening engine producing all output artifacts."""
    out_dir = tmp_path / "research_results"
    res = run_research_screening(
        dataset_dir=mock_phase_9b_dataset,
        output_base_dir=out_dir,
        custom_date_tag="20260823_TEST",
    )

    assert res.results_dir.exists()
    assert (res.results_dir / "all_results.csv").exists()
    assert (res.results_dir / "candidates.csv").exists()
    assert (res.results_dir / "disqualified.csv").exists()
    assert (res.results_dir / "failures.csv").exists()
    assert (res.results_dir / "research_manifest.json").exists()

    m = res.manifest
    assert m.total_input_securities == 3
    assert m.attempted_evaluations == 3
    assert m.successful_evaluations == 3
    assert m.failed_evaluations == 0
    assert len(res.all_results_df) == 3


def test_exact_one_result_per_successful_input(mock_phase_9b_dataset: Path, tmp_path: Path):
    """Test that every input security produces exactly one row in all_results.csv."""
    out_dir = tmp_path / "research_results"
    res = run_research_screening(
        dataset_dir=mock_phase_9b_dataset,
        output_base_dir=out_dir,
    )

    symbols_in_df = set(res.all_results_df["symbol"])
    assert symbols_in_df == {"STOCKA", "STOCKB", "STOCKC"}
    assert len(res.all_results_df) == 3


def test_failure_isolation_with_corrupt_file(mock_phase_9b_dataset: Path, tmp_path: Path):
    """Test that a corrupt or missing CSV is isolated into failures.csv without crashing batch."""
    # Corrupt STOCKB.NS.csv
    b_csv = mock_phase_9b_dataset / "data" / "STOCKB.NS.csv"
    b_csv.write_text("CORRUPT,GARBAGE,DATA\n1,2,3\n")

    out_dir = tmp_path / "research_results"
    res = run_research_screening(
        dataset_dir=mock_phase_9b_dataset,
        output_base_dir=out_dir,
    )

    assert res.manifest.total_input_securities == 3
    assert res.manifest.successful_evaluations == 2
    assert res.manifest.failed_evaluations == 1
    assert len(res.all_results_df) == 2
    assert len(res.failures_df) == 1
    assert res.failures_df["symbol"].iloc[0] == "STOCKB"


def test_unqualified_security_processed_regression(mock_phase_9b_dataset: Path, tmp_path: Path):
    """Test regression: research_eligible == True and is_mechanically_qualified == False is preserved."""
    out_dir = tmp_path / "research_results"
    res = run_research_screening(
        dataset_dir=mock_phase_9b_dataset,
        output_base_dir=out_dir,
    )

    df_b = res.all_results_df[res.all_results_df["symbol"] == "STOCKB"]
    assert not df_b.empty
    # Stock B had turnover of 1000 * 50 / 10,000,000 = 0.005 Cr < 1.0 Cr
    assert df_b["is_research_eligible"].iloc[0] == True
    assert df_b["is_mechanically_qualified"].iloc[0] == False
    assert df_b["candidate_category"].iloc[0] in [CandidateCategory.WATCHLIST.value, CandidateCategory.NO_SETUP.value, CandidateCategory.DISQUALIFIED.value]


def test_category_mutual_exclusivity(mock_phase_9b_dataset: Path, tmp_path: Path):
    """Test that candidate categorization is strictly mutually exclusive."""
    out_dir = tmp_path / "research_results"
    res = run_research_screening(
        dataset_dir=mock_phase_9b_dataset,
        output_base_dir=out_dir,
    )

    valid_categories = {c.value for c in CandidateCategory}
    for cat in res.all_results_df["candidate_category"]:
        assert cat in valid_categories


def test_manifest_mathematical_reconciliation(mock_phase_9b_dataset: Path, tmp_path: Path):
    """Test exact mathematical reconciliation of input, successful, failed, and category counts."""
    out_dir = tmp_path / "research_results"
    res = run_research_screening(
        dataset_dir=mock_phase_9b_dataset,
        output_base_dir=out_dir,
    )

    m = res.manifest
    # 1. Total = Success + Failed
    assert m.total_input_securities == m.successful_evaluations + m.failed_evaluations

    # 2. Success = Sum of all 5 mutually exclusive categories
    category_sum = (
        m.high_priority_candidates_count
        + m.qualified_candidates_count
        + m.watchlist_candidates_count
        + m.no_setup_count
        + m.disqualified_count
    )
    assert m.successful_evaluations == category_sum


def test_deterministic_repeated_screening(mock_phase_9b_dataset: Path, tmp_path: Path):
    """Test that screening the same dataset twice produces bitwise identical results and scores."""
    out_dir1 = tmp_path / "results_1"
    out_dir2 = tmp_path / "results_2"

    res1 = run_research_screening(mock_phase_9b_dataset, output_base_dir=out_dir1, custom_date_tag="SNAP1")
    res2 = run_research_screening(mock_phase_9b_dataset, output_base_dir=out_dir2, custom_date_tag="SNAP2")

    pd.testing.assert_series_equal(res1.all_results_df["composite_score"], res2.all_results_df["composite_score"])
    pd.testing.assert_series_equal(res1.all_results_df["candidate_category"], res2.all_results_df["candidate_category"])
    pd.testing.assert_series_equal(res1.all_results_df["is_mechanically_qualified"], res2.all_results_df["is_mechanically_qualified"])


def test_tradingview_failure_does_not_abort_screening(mock_phase_9b_dataset: Path, tmp_path: Path, monkeypatch):
    """Test that a failure in TradingView URL generation records an error but never fails screening."""
    def mock_tv_fail(symbol: str, exchange: str = "NSE"):
        raise RuntimeError("Mock TradingView connection failure")

    monkeypatch.setattr("wyckoff_screener.research.screening_engine.generate_tradingview_links", mock_tv_fail)

    out_dir = tmp_path / "research_results"
    res = run_research_screening(
        dataset_dir=mock_phase_9b_dataset,
        output_base_dir=out_dir,
    )

    assert res.manifest.successful_evaluations == 3
    assert res.manifest.failed_evaluations == 0
    assert res.manifest.tradingview_link_failures_count == 3
    assert len(res.all_results_df) == 3


def test_zero_external_network_requests(mock_phase_9b_dataset: Path, tmp_path: Path, monkeypatch):
    """Test that running screening makes zero network calls."""
    import socket

    def mock_socket_connect(*args, **kwargs):
        raise AssertionError("Network request detected during offline research screening!")

    monkeypatch.setattr(socket.socket, "connect", mock_socket_connect)

    out_dir = tmp_path / "research_results"
    res = run_research_screening(
        dataset_dir=mock_phase_9b_dataset,
        output_base_dir=out_dir,
    )

    assert res.manifest.successful_evaluations == 3


def test_evidence_first_explanation_completeness():
    """Test that explanation generation produces exact numeric evidence strings."""
    expl = generate_candidate_explanation(
        symbol="ANANTRAJ",
        is_mechanically_qualified=True,
        filter_flags={"weekly_uptrend": True, "dma_50_above_100": True, "rsi_in_band": True, "atr_contracting": True},
        filter_values={"wma_30": 450.0, "wma_40": 420.0, "dma_50": 460.0, "dma_100": 430.0, "rsi_14": 62.5, "atr_contraction_ratio": 0.82},
        vsa_volume_ratio=2.45,
        vsa_close_position=0.85,
        is_stopping_volume=True,
        is_no_supply=False,
        is_no_demand=False,
        most_recent_event_type="LPS",
        numeric_evidence="volume_ratio 0.65x avg, higher low held above support",
        pf_target_price=580.0,
        pf_upside_pct=18.5,
        composite_score=72.5,
        is_disqualified=False,
        disqualifying_flags=[],
        candidate_category=CandidateCategory.HIGH_PRIORITY_CANDIDATE.value,
    )

    assert "[HIGH_PRIORITY_CANDIDATE]" in expl
    assert "Score: 72.5/100.0" in expl
    assert "Mech Qual: PASS" in expl
    assert "Weekly WMA(30/40) Up" in expl
    assert "Daily DMA(50/100) Up" in expl
    assert "RSI(14) Bullish (62.5)" in expl
    assert "ATR Contraction (0.82<1.0)" in expl
    assert "Vol Ratio: 2.45x" in expl
    assert "Stopping Volume (Absorption)" in expl
    assert "Candidate Event: LPS" in expl
    assert "P&F Target: ₹580.00 (+18.5% upside)" in expl


def test_screening_against_actual_phase_9b_audit_dataset(tmp_path: Path):
    """Integration test: execute research screening against representative slice of actual Phase 9B audited dataset."""
    p9b_audit_ds = Path("data/research_datasets/20260823_31_AUDIT")
    if not p9b_audit_ds.exists():
        pytest.skip("Phase 9B audit dataset not found on disk.")

    # Create a fast test slice of 5 symbols from the audited dataset
    slice_dir = tmp_path / "slice_dataset"
    slice_data = slice_dir / "data"
    slice_data.mkdir(parents=True, exist_ok=True)

    df_sym = pd.read_csv(p9b_audit_ds / "symbols.csv").head(5)
    df_sym.to_csv(slice_dir / "symbols.csv", index=False)
    shutil.copy2(p9b_audit_ds / "manifest.json", slice_dir / "manifest.json")
    for _, row in df_sym.iterrows():
        yf_t = row["yfinance_ticker"]
        shutil.copy2(p9b_audit_ds / "data" / f"{yf_t}.csv", slice_data / f"{yf_t}.csv")

    out_dir = tmp_path / "research_results_audit"
    res = run_research_screening(
        dataset_dir=slice_dir,
        output_base_dir=out_dir,
        custom_date_tag="20260823_AUDIT_RUN",
    )

    m = res.manifest
    assert m.total_input_securities == 5
    assert m.successful_evaluations == 5
    assert m.failed_evaluations == 0
    assert len(res.all_results_df) == 5
    assert (
        m.high_priority_candidates_count
        + m.qualified_candidates_count
        + m.watchlist_candidates_count
        + m.no_setup_count
        + m.disqualified_count
    ) == 5
