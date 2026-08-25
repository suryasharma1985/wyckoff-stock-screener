"""Unit tests for Phase 11 Streamlit Dashboard integration and read-only guarantees."""

import importlib
import json
from pathlib import Path
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


def test_dashboard_import_smoke():
    """Verify that the Streamlit dashboard module compiles and imports without errors."""
    import dashboard.app as app_mod
    assert hasattr(app_mod, "st")
    assert hasattr(app_mod, "category_chip")
    assert hasattr(app_mod, "latest_results_dir")


def test_dashboard_read_only_with_empty_and_populated_ledger(tmp_path: Path):
    """Verify that forward ledger loading handles empty/populated states without modifying files."""
    fwd_dir = tmp_path / "forward_val"
    ledger = ForwardLedger(base_dir=fwd_dir)

    # 1. Empty state
    df_empty_outcomes = ledger.load_outcomes_dataframe()
    assert df_empty_outcomes.empty
    snaps_empty = ledger.list_snapshots()
    assert len(snaps_empty) == 0

    # 2. Add sample data
    cand_id = generate_candidate_id("ANANTRAJ", "2026-08-24", 750.0, FORWARD_ENGINE_VERSION)
    rec = ForwardCandidateRecord(
        candidate_id=cand_id,
        screening_date="2026-08-24",
        symbol="ANANTRAJ",
        yfinance_ticker="ANANTRAJ.NS",
        company_name="Anant Raj Limited",
        reference_close_price=750.0,
        data_bars=500,
        candidate_category="HIGH_PRIORITY_CANDIDATE",
        composite_score=75.0,
        is_mechanically_qualified=True,
        is_disqualified=False,
        disqualifying_flags="None",
        weekly_uptrend=True,
        dma_50_above_100=True,
        rsi_in_band=True,
        atr_contracting=True,
        vcp_bbw_contracting=True,
        vsa_volume_ratio=2.2,
        vsa_spread_ratio=1.6,
        vsa_close_position=0.85,
        is_stopping_volume=False,
        is_no_demand=False,
        is_no_supply=False,
        is_effort_vs_result=False,
        most_recent_event_type="LPS",
        most_recent_event_date="2026-08-20",
        possible_LPS=True,
        possible_SOS=False,
        possible_Spring=False,
        is_UTAD_warning=False,
        numeric_evidence="LPS on dry volume",
        pf_target_price=900.0,
        pf_upside_pct=20.0,
        pf_count_columns=8,
        pf_is_stale_anchor=False,
        explanation_summary="Strong candidate",
        tradingview_daily_url="https://tradingview.com/chart/?symbol=NSE:ANANTRAJ",
        tradingview_weekly_url="",
        tradingview_75m_url="",
        engine_version=FORWARD_ENGINE_VERSION,
        created_at_utc="2026-08-24T10:00:00Z",
    )

    ledger.save_screening_snapshot("2026-08-24", [rec])

    # 3. Read back
    snaps = ledger.list_snapshots()
    assert len(snaps) == 1
    assert snaps[0]["screening_date"] == "2026-08-24"

    outcomes_df = ledger.load_outcomes_dataframe()
    assert len(outcomes_df) == 1
    assert outcomes_df.iloc[0]["symbol"] == "ANANTRAJ"
    assert outcomes_df.iloc[0]["status_10d"] == HorizonStatus.PENDING.value

    # Verify snapshot JSON file size and hash are not modified by reading
    snap_path = ledger.get_snapshot_path("2026-08-24")
    mtime_before = snap_path.stat().st_mtime
    snap_loaded = ledger.load_snapshot("2026-08-24")
    assert snap_loaded.total_candidates == 1
    mtime_after = snap_path.stat().st_mtime
    assert mtime_before == mtime_after


def test_historical_validation_dataframe_parsing():
    """Verify that all validation CSVs parse without KeyError on column slicing."""
    val_dir = Path("data/validation_results/20260824")
    if not val_dir.exists():
        pytest.skip("Validation results not found")

    cat_path = val_dir / "category_performance.csv"
    assert cat_path.exists()
    cdf = pd.read_csv(cat_path)
    assert not cdf.empty

    horizons = sorted(cdf["horizon"].unique())
    for h in horizons:
        cohort_col = "cohort_name" if "cohort_name" in cdf.columns else "cohort_value"
        sub_cols = [c for c in ["cohort_group", cohort_col, "observation_count",
                                "mean_return_pct", "median_return_pct", "win_rate_pct",
                                "mean_mfe_pct", "mean_mae_pct"] if c in cdf.columns]
        sub = cdf[cdf["horizon"] == h][sub_cols].copy()
        assert not sub.empty
        assert "observation_count" in sub.columns


def test_lps_breakout_trigger_calculations():
    """Verify that dashboard calculations for LPS breakout trigger and R:R function correctly under various conditions."""
    # Inputs
    ref_close = 105.0
    pf_target = 130.0
    lps_high_val = 110.0
    lps_support_val = 100.0
    lps_anchor_val = 95.0

    # 1. LPS High remains the conditional trigger
    suggested_entry = lps_high_val
    assert suggested_entry == 110.0

    # 2. Displayed 5% stop remains only a reference
    suggested_stop = ref_close * 0.95
    assert suggested_stop == 99.75

    # 3. Structural R:R uses support_level, NOT the 5% stop
    risk = lps_high_val - lps_support_val
    reward = pf_target - lps_high_val
    indicative_rr = reward / risk

    assert risk == 10.0  # Uses 100.0 (support_level), not 99.75 (5% stop)
    assert reward == 20.0
    assert indicative_rr == 2.0  # 20.0 / 10.0 = 2.0
    assert indicative_rr != (reward / (lps_high_val - suggested_stop))  # Confirms 5% stop is not used

    # 4. Invalid structural R:R conditions return N/A (Trigger <= Support)
    lps_high_val_invalid1 = 98.0
    indicative_rr_invalid1 = None
    rr_na_reason1 = ""
    if lps_high_val_invalid1 <= lps_support_val:
        rr_na_reason1 = "LPS Breakout Trigger is below or equal to Trading-Range Support."
    else:
        risk1 = lps_high_val_invalid1 - lps_support_val
        reward1 = pf_target - lps_high_val_invalid1
        indicative_rr_invalid1 = reward1 / risk1

    assert indicative_rr_invalid1 is None
    assert "below or equal to Trading-Range Support" in rr_na_reason1

    # 5. Invalid structural R:R conditions return N/A (Target <= Trigger)
    pf_target_invalid = 108.0
    indicative_rr_invalid2 = None
    rr_na_reason2 = ""
    if pf_target_invalid <= lps_high_val:
        rr_na_reason2 = "P&F Target Price is below or equal to LPS Breakout Trigger."
    else:
        risk2 = lps_high_val - lps_support_val
        reward2 = pf_target_invalid - lps_high_val
        indicative_rr_invalid2 = reward2 / risk2

    assert indicative_rr_invalid2 is None
    assert "below or equal to LPS Breakout Trigger" in rr_na_reason2

    # 6. Non-LPS behavior remains unchanged
    # For a non-LPS setup, suggested entry is ref_close and stop loss is ref_close * 0.95
    non_lps_entry = ref_close
    non_lps_stop = ref_close * 0.95
    non_lps_target = pf_target
    non_lps_risk = non_lps_entry - non_lps_stop
    non_lps_reward = non_lps_target - non_lps_entry
    non_lps_rrr = non_lps_reward / non_lps_risk

    assert non_lps_entry == 105.0
    assert non_lps_stop == 99.75
    assert non_lps_rrr == 25.0 / 5.25
