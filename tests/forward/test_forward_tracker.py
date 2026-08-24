"""Unit tests for Phase 11 Forward Price-Path Tracker, Outcome Calculations, and Zero-Lookahead Isolation."""

from pathlib import Path
import numpy as np
import pandas as pd
import pytest

from wyckoff_screener.forward.ledger import ForwardLedger
from wyckoff_screener.forward.models import (
    FORWARD_ENGINE_VERSION,
    ForwardCandidateRecord,
    ForwardOutcomeRecord,
    HorizonStatus,
    generate_candidate_id,
)
from wyckoff_screener.forward.tracker import (
    update_all_forward_outcomes,
    update_candidate_outcome,
)


def _build_synthetic_ohlcv(
    num_bars: int = 100,
    start_price: float = 100.0,
    daily_growth: float = 1.0,
) -> pd.DataFrame:
    """Build a deterministic synthetic OHLCV DataFrame for testing forward calculations."""
    dates = pd.date_range("2025-01-01", periods=num_bars, freq="B").strftime("%Y-%m-%d")
    closes = [start_price + i * daily_growth for i in range(num_bars)]
    highs = [c + 2.0 for c in closes]
    lows = [c - 2.0 for c in closes]
    opens = [c - 0.5 for c in closes]
    volumes = [1000000 + i * 5000 for i in range(num_bars)]

    return pd.DataFrame({
        "Date": dates,
        "Open": opens,
        "High": highs,
        "Low": lows,
        "Close": closes,
        "Volume": volumes,
    })


def test_exact_forward_return_and_excursion_calculations():
    """Verify that 10d, 20d, 60d returns, MFE, and MAE calculate with exact mathematical precision."""
    df = _build_synthetic_ohlcv(num_bars=100, start_price=100.0, daily_growth=1.0)
    # Day 0: Date = 2025-01-01, Close = 100.0, High = 102.0, Low = 98.0
    # Day 10: Date = 2025-01-15, Close = 110.0
    # Day 20: Date = 2025-01-29, Close = 120.0
    # Day 60: Date = 2025-03-26, Close = 160.0

    scr_date = df.iloc[0]["Date"]
    ref_close = float(df.iloc[0]["Close"])  # 100.0

    outcome = ForwardOutcomeRecord(
        candidate_id="cand_test_01",
        symbol="SYNTH",
        screening_date=scr_date,
        reference_close_price=ref_close,
        candidate_category="HIGH_PRIORITY_CANDIDATE",
        composite_score=70.0,
    )

    updated = update_candidate_outcome(outcome, df, horizons=(10, 20, 60))

    assert updated.available_forward_bars == 99
    assert updated.status_10d == HorizonStatus.MATURED.value
    assert updated.status_20d == HorizonStatus.MATURED.value
    assert updated.status_60d == HorizonStatus.MATURED.value

    # Close return at 10d: (110 - 100) / 100 = +10.0%
    assert updated.fwd_ret_10d == 10.0
    # Close return at 20d: (120 - 100) / 100 = +20.0%
    assert updated.fwd_ret_20d == 20.0
    # Close return at 60d: (160 - 100) / 100 = +60.0%
    assert updated.fwd_ret_60d == 60.0

    # MFE 10d: Max high over bars 1..10 = 110 + 2 = 112.0 -> (112 - 100)/100 = +12.0%
    assert updated.mfe_10d == 12.0
    # MAE 10d: Min low over bars 1..10 = 101 - 2 = 99.0 -> (99 - 100)/100 = -1.0%
    assert updated.mae_10d == -1.0


def test_partial_horizon_remains_pending():
    """Verify that horizons with insufficient future bars remain strictly PENDING with null values."""
    df = _build_synthetic_ohlcv(num_bars=25, start_price=100.0)  # Only 24 future bars available after bar 0
    scr_date = df.iloc[0]["Date"]

    outcome = ForwardOutcomeRecord(
        candidate_id="cand_test_partial",
        symbol="SYNTH",
        screening_date=scr_date,
        reference_close_price=100.0,
        candidate_category="QUALIFIED_CANDIDATE",
        composite_score=55.0,
    )

    updated = update_candidate_outcome(outcome, df, horizons=(10, 20, 60))

    assert updated.available_forward_bars == 24
    assert updated.status_10d == HorizonStatus.MATURED.value
    assert updated.fwd_ret_10d is not None

    assert updated.status_20d == HorizonStatus.MATURED.value
    assert updated.fwd_ret_20d is not None

    # 60d horizon MUST remain PENDING because only 24 future bars exist
    assert updated.status_60d == HorizonStatus.PENDING.value
    assert updated.fwd_ret_60d is None
    assert updated.mfe_60d is None
    assert updated.mae_60d is None


def test_screening_day_bar_exclusion():
    """Verify that the screening-day bar T is excluded from the forward excursion window."""
    df = _build_synthetic_ohlcv(num_bars=15, start_price=100.0)
    # Give bar 0 an extreme low that should NOT enter the forward MAE
    df.loc[0, "Low"] = 50.0  # Would be -50% if included

    scr_date = df.iloc[0]["Date"]
    outcome = ForwardOutcomeRecord(
        candidate_id="cand_test_excl",
        symbol="SYNTH",
        screening_date=scr_date,
        reference_close_price=100.0,
        candidate_category="HIGH_PRIORITY_CANDIDATE",
        composite_score=75.0,
    )

    updated = update_candidate_outcome(outcome, df, horizons=(10,))

    # MAE should reflect min low from bar 1..10 (which is 101 - 2 = 99.0, i.e. -1.0%), NOT 50.0 (-50.0%)
    assert updated.mae_10d == -1.0


def test_idempotent_update_all_forward_outcomes(tmp_path: Path):
    """Verify that running update_all_forward_outcomes multiple times is completely idempotent."""
    ledger = ForwardLedger(base_dir=tmp_path)
    data_dir = tmp_path / "data"
    data_dir.mkdir(parents=True, exist_ok=True)

    df_synth = _build_synthetic_ohlcv(num_bars=30, start_price=200.0)
    df_synth.to_csv(data_dir / "SYNTH.NS.csv", index=False)

    cand_id = generate_candidate_id("SYNTH", df_synth.iloc[0]["Date"], 200.0, FORWARD_ENGINE_VERSION)
    rec = ForwardCandidateRecord(
        candidate_id=cand_id,
        screening_date=df_synth.iloc[0]["Date"],
        symbol="SYNTH",
        yfinance_ticker="SYNTH.NS",
        company_name="Synthetic Corp",
        reference_close_price=200.0,
        data_bars=30,
        candidate_category="HIGH_PRIORITY_CANDIDATE",
        composite_score=70.0,
        is_mechanically_qualified=True,
        is_disqualified=False,
        disqualifying_flags="None",
        weekly_uptrend=True,
        dma_50_above_100=True,
        rsi_in_band=True,
        atr_contracting=True,
        vcp_bbw_contracting=True,
        vsa_volume_ratio=2.0,
        vsa_spread_ratio=1.5,
        vsa_close_position=0.8,
        is_stopping_volume=False,
        is_no_demand=False,
        is_no_supply=False,
        is_effort_vs_result=False,
        most_recent_event_type="LPS",
        most_recent_event_date=df_synth.iloc[0]["Date"],
        possible_LPS=True,
        possible_SOS=False,
        possible_Spring=False,
        is_UTAD_warning=False,
        numeric_evidence="LPS detected",
        pf_target_price=250.0,
        pf_upside_pct=25.0,
        pf_count_columns=6,
        pf_is_stale_anchor=False,
        explanation_summary="Valid LPS test",
        tradingview_daily_url="",
        tradingview_weekly_url="",
        tradingview_75m_url="",
        engine_version=FORWARD_ENGINE_VERSION,
        created_at_utc="2026-08-24T10:00:00Z",
    )

    ledger.save_screening_snapshot(df_synth.iloc[0]["Date"], [rec])

    # Run update 1
    total_1, matured_1 = update_all_forward_outcomes(ledger, data_dir=data_dir)
    outcomes_1 = ledger.load_outcomes_dataframe()

    # Run update 2 with same data
    total_2, matured_2 = update_all_forward_outcomes(ledger, data_dir=data_dir)
    outcomes_2 = ledger.load_outcomes_dataframe()

    assert total_1 == total_2 == 1
    assert matured_1 == matured_2 == 2  # 10d and 20d matured
    assert len(outcomes_1) == len(outcomes_2) == 1
    assert outcomes_1.iloc[0]["fwd_ret_10d"] == outcomes_2.iloc[0]["fwd_ret_10d"]
    assert outcomes_1.iloc[0]["fwd_ret_20d"] == outcomes_2.iloc[0]["fwd_ret_20d"]


def test_zero_lookahead_forward_isolation(tmp_path: Path):
    """Verify that changing future market data alters outcome fields but leaves candidate snapshot immutable."""
    ledger = ForwardLedger(base_dir=tmp_path)
    data_dir = tmp_path / "data"
    data_dir.mkdir(parents=True, exist_ok=True)

    df_base = _build_synthetic_ohlcv(num_bars=30, start_price=100.0, daily_growth=1.0)
    scr_date = df_base.iloc[0]["Date"]

    cand_id = generate_candidate_id("TESTISO", scr_date, 100.0, FORWARD_ENGINE_VERSION)
    rec = ForwardCandidateRecord(
        candidate_id=cand_id,
        screening_date=scr_date,
        symbol="TESTISO",
        yfinance_ticker="TESTISO.NS",
        company_name="Test Isolation Corp",
        reference_close_price=100.0,
        data_bars=30,
        candidate_category="HIGH_PRIORITY_CANDIDATE",
        composite_score=85.0,
        is_mechanically_qualified=True,
        is_disqualified=False,
        disqualifying_flags="None",
        weekly_uptrend=True,
        dma_50_above_100=True,
        rsi_in_band=True,
        atr_contracting=True,
        vcp_bbw_contracting=True,
        vsa_volume_ratio=2.5,
        vsa_spread_ratio=1.8,
        vsa_close_position=0.9,
        is_stopping_volume=False,
        is_no_demand=False,
        is_no_supply=False,
        is_effort_vs_result=False,
        most_recent_event_type="SOS",
        most_recent_event_date=scr_date,
        possible_LPS=False,
        possible_SOS=True,
        possible_Spring=False,
        is_UTAD_warning=False,
        numeric_evidence="SOS breakout bar",
        pf_target_price=140.0,
        pf_upside_pct=40.0,
        pf_count_columns=10,
        pf_is_stale_anchor=False,
        explanation_summary="Strong SOS breakout",
        tradingview_daily_url="",
        tradingview_weekly_url="",
        tradingview_75m_url="",
        engine_version=FORWARD_ENGINE_VERSION,
        created_at_utc="2026-08-24T10:00:00Z",
    )

    # 1. Save original screening snapshot
    manifest_orig = ledger.save_screening_snapshot(scr_date, [rec])
    snap_orig = ledger.load_snapshot(scr_date)

    # 2. Write initial market data where stock rises
    df_base.to_csv(data_dir / "TESTISO.NS.csv", index=False)
    update_all_forward_outcomes(ledger, data_dir)
    out_1 = ledger.load_outcomes_dataframe()
    assert out_1.iloc[0]["fwd_ret_10d"] == 10.0  # +10.0%

    # 3. Simulate future market crash after screening date T (bars 1..29 drop by 50%)
    df_crashed = df_base.copy()
    for i in range(1, len(df_crashed)):
        df_crashed.loc[i, "Open"] = 50.0
        df_crashed.loc[i, "Close"] = 50.0
        df_crashed.loc[i, "High"] = 52.0
        df_crashed.loc[i, "Low"] = 48.0
    df_crashed.to_csv(data_dir / "TESTISO.NS.csv", index=False)

    # 4. Re-run forward outcome update
    update_all_forward_outcomes(ledger, data_dir)
    out_2 = ledger.load_outcomes_dataframe()

    # Outcome metric MUST change to reflect the market crash
    assert out_2.iloc[0]["fwd_ret_10d"] == -50.0  # -50.0%

    # 5. Crucially verify that the original screening snapshot is 100% UNCHANGED
    snap_after = ledger.load_snapshot(scr_date)
    assert snap_after.total_candidates == snap_orig.total_candidates
    assert snap_after.candidate_records[0]["composite_score"] == 85.0
    assert snap_after.candidate_records[0]["candidate_category"] == "HIGH_PRIORITY_CANDIDATE"
    assert snap_after.candidate_records[0]["reference_close_price"] == 100.0
    assert snap_after.candidate_records[0]["vsa_volume_ratio"] == 2.5


def test_forward_cli_execution(tmp_path: Path):
    """Verify that CLI subcommands screen, update, and report run cleanly."""
    from wyckoff_screener.forward.cli import handle_report, handle_screen, handle_update
    import argparse

    # Build mock dataset
    ds_dir = tmp_path / "mock_dataset"
    data_dir = ds_dir / "data"
    data_dir.mkdir(parents=True, exist_ok=True)

    df_synth = _build_synthetic_ohlcv(num_bars=60, start_price=100.0)
    df_synth.to_csv(data_dir / "ANANTRAJ.NS.csv", index=False)

    symbols_df = pd.DataFrame([{"symbol": "ANANTRAJ", "yfinance_ticker": "ANANTRAJ.NS", "company_name": "Anant Raj"}])
    symbols_df.to_csv(ds_dir / "symbols.csv", index=False)

    fwd_dir = tmp_path / "fwd_val"

    # Test screen command at bar 50
    scr_date = df_synth.iloc[49]["Date"]
    args_screen = argparse.Namespace(
        date=scr_date,
        dataset_dir=str(ds_dir),
        forward_dir=str(fwd_dir),
        overwrite=False,
        min_turnover_cr=0.0,
        high_priority_threshold=60.0,
        qualified_threshold=40.0,
        watchlist_threshold=30.0,
    )
    handle_screen(args_screen)

    # Verify snapshot was created
    ledger = ForwardLedger(base_dir=fwd_dir)
    assert ledger.snapshot_exists(scr_date)

    # Test update command
    args_update = argparse.Namespace(
        dataset_dir=str(ds_dir),
        forward_dir=str(fwd_dir),
    )
    handle_update(args_update)
    outcomes = ledger.load_outcomes_dataframe()
    assert len(outcomes) == 1
    assert outcomes.iloc[0]["status_10d"] == HorizonStatus.MATURED.value

    # Test report command (should run without error)
    args_report = argparse.Namespace(forward_dir=str(fwd_dir))
    handle_report(args_report)

    # Test screen command with invalid/early date raises SystemExit
    args_invalid_screen = argparse.Namespace(
        date="1990-01-01",
        dataset_dir=str(ds_dir),
        forward_dir=str(fwd_dir),
        overwrite=False,
        min_turnover_cr=0.0,
        high_priority_threshold=60.0,
        qualified_threshold=40.0,
        watchlist_threshold=30.0,
    )
    with pytest.raises(SystemExit):
        handle_screen(args_invalid_screen)
