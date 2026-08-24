"""Unit, integration, and regression tests for Phase 10 Historical Validation & Backtesting."""

import json
from pathlib import Path
import shutil
from typing import Any
import numpy as np
import pandas as pd
import pytest

from wyckoff_screener.research.models import CandidateCategory
from wyckoff_screener.validation.models import (
    HistoricalSignalObservation,
    ValidationFailureRecord,
    CohortSummaryStats,
    SURVIVORSHIP_BIAS_WARNING,
)
from wyckoff_screener.validation.metrics import (
    calculate_forward_metrics_for_bar,
    aggregate_all_cohorts,
)
from wyckoff_screener.validation.engine import (
    evaluate_single_security_history,
    run_historical_validation,
)


@pytest.fixture
def mock_validation_dataset(tmp_path: Path) -> Path:
    """Create a synthetic 300-bar Phase 9B research dataset directory with 3 test securities."""
    ds_dir = tmp_path / "mock_val_dataset"
    data_dir = ds_dir / "data"
    data_dir.mkdir(parents=True, exist_ok=True)

    # 300 daily bars spanning 2024-01-01 through early 2025
    dates = pd.date_range(start="2024-01-01", periods=300, freq="B")
    dates_str = dates.strftime("%Y-%m-%d")

    # Stock 1: Strong uptrend with high turnover
    prices_1 = np.linspace(100.0, 300.0, 300)
    df_1 = pd.DataFrame({
        "Date": dates_str,
        "Open": prices_1,
        "High": prices_1 * 1.02,
        "Low": prices_1 * 0.98,
        "Close": prices_1 * 1.01,
        "Volume": [500_000] * 300,
    })
    df_1.to_csv(data_dir / "SYM1.NS.csv", index=False)

    # Stock 2: Sideways consolidation with dry-up and LPS-like holding
    prices_2 = 150.0 + np.sin(np.linspace(0, 10, 300)) * 10.0
    df_2 = pd.DataFrame({
        "Date": dates_str,
        "Open": prices_2,
        "High": prices_2 + 2.0,
        "Low": prices_2 - 2.0,
        "Close": prices_2 + 0.5,
        "Volume": [200_000] * 300,
    })
    df_2.to_csv(data_dir / "SYM2.NS.csv", index=False)

    # Stock 3: Severe downtrend
    prices_3 = np.linspace(200.0, 50.0, 300)
    df_3 = pd.DataFrame({
        "Date": dates_str,
        "Open": prices_3,
        "High": prices_3 * 1.01,
        "Low": prices_3 * 0.97,
        "Close": prices_3 * 0.98,
        "Volume": [100_000] * 300,
    })
    df_3.to_csv(data_dir / "SYM3.NS.csv", index=False)

    symbols_df = pd.DataFrame({
        "symbol": ["SYM1", "SYM2", "SYM3"],
        "yfinance_ticker": ["SYM1.NS", "SYM2.NS", "SYM3.NS"],
        "company_name": ["Symbol 1 Ltd", "Symbol 2 Ltd", "Symbol 3 Ltd"],
    })
    symbols_df.to_csv(ds_dir / "symbols.csv", index=False)

    return ds_dir


def test_forward_return_formulas():
    """Test exact mathematical calculation of forward return, MFE, and MAE against known values."""
    # Synthetic 10-bar price series
    closes = np.array([100.0, 102.0, 105.0, 110.0, 95.0, 100.0, 120.0, 115.0, 90.0, 105.0])
    highs  = np.array([101.0, 104.0, 108.0, 112.0, 98.0, 102.0, 125.0, 118.0, 92.0, 108.0])
    lows   = np.array([ 99.0, 101.0, 103.0, 108.0, 92.0,  98.0, 118.0, 112.0, 88.0, 102.0])

    # Checkpoint at bar_idx = 0 (Base close = 100.0)
    # For h = 3:
    # Target close at index 3 = 110.0 => Return = +10.0%
    # Forward highs in [1..3] = [104, 108, 112] => Max High = 112.0 => MFE = +12.0%
    # Forward lows in [1..3] = [101, 103, 108] => Min Low = 101.0 => MAE = +1.0%
    res = calculate_forward_metrics_for_bar(
        prices_close=closes,
        prices_high=highs,
        prices_low=lows,
        bar_idx=0,
        horizons=[3, 4],
    )

    assert res["fwd_ret_3d"] == 10.0
    assert res["mfe_3d"] == 12.0
    assert res["mae_3d"] == 1.0

    # For h = 4:
    # Target close at index 4 = 95.0 => Return = -5.0%
    # Forward highs in [1..4] = [104, 108, 112, 98] => Max High = 112.0 => MFE = +12.0%
    # Forward lows in [1..4] = [101, 103, 108, 92] => Min Low = 92.0 => MAE = -8.0%
    assert res["fwd_ret_4d"] == -5.0
    assert res["mfe_4d"] == 12.0
    assert res["mae_4d"] == -8.0


def test_point_in_time_slice_isolation(tmp_path: Path):
    """Test that slice passed to signal evaluator strictly contains data up to bar T only."""
    csv_file = tmp_path / "TEST.NS.csv"
    dates = pd.date_range(start="2024-01-01", periods=250, freq="B").strftime("%Y-%m-%d")
    df = pd.DataFrame({
        "Date": dates,
        "Open": np.linspace(100.0, 200.0, 250),
        "High": np.linspace(101.0, 202.0, 250),
        "Low": np.linspace(99.0, 198.0, 250),
        "Close": np.linspace(100.5, 201.0, 250),
        "Volume": [100_000] * 250,
    })
    df.to_csv(csv_file, index=False)

    obs_list, failures, attempted = evaluate_single_security_history(
        csv_path=csv_file,
        symbol="TEST",
        yf_ticker="TEST.NS",
        company_name="Test Corp",
        warmup_bars=200,
        step_bars=10,
        horizons=[10, 20],
    )

    assert len(failures) == 0
    assert len(obs_list) > 0

    for obs in obs_list:
        # Assert bar_index corresponds exactly to the checkpoint date in original df
        assert df["Date"].iloc[obs.bar_index] == obs.checkpoint_date
        assert round(df["Close"].iloc[obs.bar_index], 2) == round(obs.close_at_checkpoint, 2)


def test_future_bar_leakage_detection(tmp_path: Path):
    """CRITICAL TEST: Mutate future prices after checkpoint T and prove that signal at T is 100% invariant."""
    csv_unmodified = tmp_path / "UNMOD.NS.csv"
    csv_mutated = tmp_path / "MUTATED.NS.csv"

    dates = pd.date_range(start="2024-01-01", periods=250, freq="B").strftime("%Y-%m-%d")
    base_prices = np.linspace(100.0, 200.0, 250)

    df_base = pd.DataFrame({
        "Date": dates,
        "Open": base_prices,
        "High": base_prices * 1.02,
        "Low": base_prices * 0.98,
        "Close": base_prices * 1.01,
        "Volume": [500_000] * 250,
    })
    df_base.to_csv(csv_unmodified, index=False)

    # Mutate all prices after bar 220 by 5x (extreme shock) while preserving valid OHLC geometry
    df_mutated = df_base.copy()
    df_mutated.loc[220:, "Open"] = df_mutated.loc[220:, "Open"] * 5.0
    df_mutated.loc[220:, "High"] = df_mutated.loc[220:, "High"] * 5.0
    df_mutated.loc[220:, "Low"] = df_mutated.loc[220:, "Low"] * 5.0
    df_mutated.loc[220:, "Close"] = df_mutated.loc[220:, "Close"] * 5.0
    df_mutated.loc[220:, "Volume"] = df_mutated.loc[220:, "Volume"] * 10.0
    df_mutated.to_csv(csv_mutated, index=False)

    # Evaluate both on checkpoint T = 205 (which is BEFORE the mutation at bar 220)
    obs_unmod, _, _ = evaluate_single_security_history(
        csv_path=csv_unmodified,
        symbol="SYM",
        yf_ticker="SYM.NS",
        company_name="Sym Ltd",
        warmup_bars=200,
        step_bars=5,
        horizons=[10],
    )

    obs_mutated, _, _ = evaluate_single_security_history(
        csv_path=csv_mutated,
        symbol="SYM",
        yf_ticker="SYM.NS",
        company_name="Sym Ltd",
        warmup_bars=200,
        step_bars=5,
        horizons=[10],
    )

    # Find observation for checkpoint index 204 (T=204 < 220)
    obs_t_unmod = [o for o in obs_unmod if o.bar_index == 204][0]
    obs_t_mutated = [o for o in obs_mutated if o.bar_index == 204][0]

    # Signal, category, score, and mechanical qualification at T=204 MUST BE EXACTLY IDENTICAL
    assert obs_t_unmod.candidate_category == obs_t_mutated.candidate_category
    assert obs_t_unmod.composite_score == obs_t_mutated.composite_score
    assert obs_t_unmod.is_mechanically_qualified == obs_t_mutated.is_mechanically_qualified
    assert obs_t_unmod.is_disqualified == obs_t_mutated.is_disqualified
    assert obs_t_unmod.most_recent_event == obs_t_mutated.most_recent_event


def test_horizon_truncation_handling(tmp_path: Path):
    """Test that horizons extending beyond available historical data return None/NaN cleanly."""
    closes = np.array([100.0, 102.0, 105.0])
    highs  = np.array([101.0, 104.0, 106.0])
    lows   = np.array([ 99.0, 101.0, 103.0])

    res = calculate_forward_metrics_for_bar(
        prices_close=closes,
        prices_high=highs,
        prices_low=lows,
        bar_idx=1,
        horizons=[1, 10],  # 1-bar exists, 10-bar extends past end
    )

    assert res["fwd_ret_1d"] is not None
    assert res["fwd_ret_10d"] is None
    assert res["mfe_10d"] is None
    assert res["mae_10d"] is None


def test_warmup_bars_enforcement(tmp_path: Path):
    """Test that checkpoints before the warm-up bar threshold are not evaluated."""
    csv_file = tmp_path / "SHORT.NS.csv"
    dates = pd.date_range(start="2024-01-01", periods=150, freq="B").strftime("%Y-%m-%d")
    df = pd.DataFrame({
        "Date": dates,
        "Open": [100.0] * 150,
        "High": [102.0] * 150,
        "Low": [98.0] * 150,
        "Close": [101.0] * 150,
        "Volume": [100_000] * 150,
    })
    df.to_csv(csv_file, index=False)

    obs_list, failures, attempted = evaluate_single_security_history(
        csv_path=csv_file,
        symbol="SHORT",
        yf_ticker="SHORT.NS",
        company_name="Short Corp",
        warmup_bars=200,  # 200 > 150
        step_bars=5,
    )

    assert len(obs_list) == 0
    assert attempted == 0


def test_cohort_and_baseline_aggregation(mock_validation_dataset: Path, tmp_path: Path):
    """Test full historical validation execution and cohort/baseline statistics aggregation."""
    out_dir = tmp_path / "val_results"
    res = run_historical_validation(
        dataset_dir=mock_validation_dataset,
        output_base_dir=out_dir,
        warmup_bars=200,
        step_bars=20,
        horizons=[10, 20, 60],
        split_date="2024-09-01",
    )

    m = res.manifest
    assert m.total_securities_in_dataset == 3
    assert m.securities_evaluated == 3
    assert m.total_successful_observations > 0
    assert m.total_failed_observations == 0

    # Reconciliation check: attempted == success + failed
    assert m.total_checkpoints_attempted == m.total_successful_observations + m.total_failed_observations

    # Check category performance table
    cat_df = res.category_performance_df
    assert "universe_baseline" in cat_df["cohort_group"].values
    assert "candidate_category" in cat_df["cohort_group"].values
    assert "mechanical_qualification" in cat_df["cohort_group"].values

    # Check that baseline observation count matches total observations
    base_10d = cat_df[(cat_df["cohort_group"] == "universe_baseline") & (cat_df["horizon"] == "10d")]
    assert len(base_10d) == 1
    assert base_10d["observation_count"].iloc[0] == m.total_successful_observations


def test_in_sample_out_sample_split(mock_validation_dataset: Path, tmp_path: Path):
    """Test proper temporal partitioning between in-sample and out-of-sample periods."""
    out_dir = tmp_path / "val_results_split"
    split_date = "2024-11-01"

    res = run_historical_validation(
        dataset_dir=mock_validation_dataset,
        output_base_dir=out_dir,
        warmup_bars=200,
        step_bars=20,
        horizons=[10, 20],
        split_date=split_date,
    )

    df_signals = res.signal_events_df
    assert not df_signals.empty

    for _, row in df_signals.iterrows():
        c_date = row["checkpoint_date"]
        split_tag = row["period_split"]
        if c_date < split_date:
            assert split_tag == "in_sample"
        else:
            assert split_tag == "out_of_sample"


def test_failure_isolation(mock_validation_dataset: Path, tmp_path: Path):
    """Test that a corrupt CSV file does not abort the validation of other valid securities."""
    # Corrupt one of the files
    corrupt_file = mock_validation_dataset / "data" / "SYM2.NS.csv"
    with open(corrupt_file, "w") as f:
        f.write("Corrupt,NonOHLCV,Data\n1,2,3")

    out_dir = tmp_path / "val_results_fail_iso"
    res = run_historical_validation(
        dataset_dir=mock_validation_dataset,
        output_base_dir=out_dir,
        warmup_bars=200,
        step_bars=20,
    )

    m = res.manifest
    assert m.total_securities_in_dataset == 3
    # 2 valid securities evaluated successfully
    assert m.total_successful_observations > 0
    # 1 failure recorded for SYM2
    assert m.total_failed_observations == 1
    assert "SYM2" in res.failures_df["symbol"].values


def test_tradingview_link_failure_isolation(mock_validation_dataset: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """Test that TradingView URL generator failure does not abort validation or affect returns."""
    import wyckoff_screener.validation.engine as engine_mod

    def mock_broken_tv(symbol: str):
        raise RuntimeError("TradingView URL generation failure simulation")

    monkeypatch.setattr(engine_mod, "generate_tradingview_links", mock_broken_tv)

    out_dir = tmp_path / "val_results_tv_iso"
    res = run_historical_validation(
        dataset_dir=mock_validation_dataset,
        output_base_dir=out_dir,
        warmup_bars=200,
        step_bars=20,
    )

    assert res.manifest.total_failed_observations == 0
    assert len(res.signal_events_df) > 0


def test_deterministic_validation_rerun(mock_validation_dataset: Path, tmp_path: Path):
    """Test that running validation twice on the same dataset produces identical analytical data."""
    out_dir_1 = tmp_path / "run_1"
    out_dir_2 = tmp_path / "run_2"

    res_1 = run_historical_validation(
        dataset_dir=mock_validation_dataset,
        output_base_dir=out_dir_1,
        warmup_bars=200,
        step_bars=20,
        custom_date_tag="TEST_DETERMINISM",
    )

    res_2 = run_historical_validation(
        dataset_dir=mock_validation_dataset,
        output_base_dir=out_dir_2,
        warmup_bars=200,
        step_bars=20,
        custom_date_tag="TEST_DETERMINISM",
    )

    # Assert bitwise identical analytical columns
    cols_to_compare = [
        "symbol", "checkpoint_date", "bar_index", "candidate_category",
        "composite_score", "is_mechanically_qualified", "fwd_ret_10d", "fwd_ret_20d", "fwd_ret_60d"
    ]
    pd.testing.assert_frame_equal(
        res_1.signal_events_df[cols_to_compare],
        res_2.signal_events_df[cols_to_compare],
    )
