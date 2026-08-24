"""Unit tests for Phase 11 Forward Validation data models and deterministic IDs."""

import pytest
from dataclasses import FrozenInstanceError

from wyckoff_screener.forward.models import (
    FORWARD_ENGINE_VERSION,
    ForwardCandidateRecord,
    ForwardOutcomeRecord,
    ForwardSnapshotManifest,
    HorizonStatus,
    generate_candidate_id,
)


def test_generate_candidate_id_determinism():
    """Verify that candidate ID generation is strictly deterministic and provably unique."""
    id1 = generate_candidate_id("ANANTRAJ", "2026-08-24", 750.50, FORWARD_ENGINE_VERSION)
    id2 = generate_candidate_id("ANANTRAJ", "2026-08-24", 750.50, FORWARD_ENGINE_VERSION)
    id_different_price = generate_candidate_id("ANANTRAJ", "2026-08-24", 751.00, FORWARD_ENGINE_VERSION)
    id_different_date = generate_candidate_id("ANANTRAJ", "2026-08-25", 750.50, FORWARD_ENGINE_VERSION)
    id_different_symbol = generate_candidate_id("APOLLO", "2026-08-24", 750.50, FORWARD_ENGINE_VERSION)

    assert id1 == id2
    assert len(id1) == 16
    assert id1 != id_different_price
    assert id1 != id_different_date
    assert id1 != id_different_symbol


def test_forward_candidate_record_immutability():
    """Verify that ForwardCandidateRecord is a frozen dataclass and cannot be mutated after creation."""
    rec = ForwardCandidateRecord(
        candidate_id="cand_12345",
        screening_date="2026-08-24",
        symbol="ANANTRAJ",
        yfinance_ticker="ANANTRAJ.NS",
        company_name="Anant Raj Limited",
        reference_close_price=750.0,
        data_bars=500,
        candidate_category="HIGH_PRIORITY_CANDIDATE",
        composite_score=75.5,
        is_mechanically_qualified=True,
        is_disqualified=False,
        disqualifying_flags="None",
        weekly_uptrend=True,
        dma_50_above_100=True,
        rsi_in_band=True,
        atr_contracting=True,
        vcp_bbw_contracting=True,
        vsa_volume_ratio=2.1,
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
        numeric_evidence="LPS on volume ratio 0.65x",
        pf_target_price=920.0,
        pf_upside_pct=22.67,
        pf_count_columns=8,
        pf_is_stale_anchor=False,
        explanation_summary="Strong setup in Phase D",
        tradingview_daily_url="https://tradingview.com/chart/?symbol=NSE:ANANTRAJ",
        tradingview_weekly_url="https://tradingview.com/chart/?symbol=NSE:ANANTRAJ&interval=W",
        tradingview_75m_url="",
        engine_version=FORWARD_ENGINE_VERSION,
        created_at_utc="2026-08-24T10:00:00Z",
    )

    with pytest.raises(FrozenInstanceError):
        rec.composite_score = 80.0  # type: ignore

    with pytest.raises(FrozenInstanceError):
        rec.candidate_category = "QUALIFIED_CANDIDATE"  # type: ignore

    d = rec.to_dict()
    assert d["symbol"] == "ANANTRAJ"
    assert d["composite_score"] == 75.5
    assert d["is_mechanically_qualified"] is True


def test_forward_outcome_record_defaults():
    """Verify that ForwardOutcomeRecord initializes with proper pending status defaults."""
    out = ForwardOutcomeRecord(
        candidate_id="cand_12345",
        symbol="ANANTRAJ",
        screening_date="2026-08-24",
        reference_close_price=750.0,
        candidate_category="HIGH_PRIORITY_CANDIDATE",
        composite_score=75.5,
    )

    assert out.available_forward_bars == 0
    assert out.status_10d == HorizonStatus.PENDING.value
    assert out.status_20d == HorizonStatus.PENDING.value
    assert out.status_60d == HorizonStatus.PENDING.value
    assert out.fwd_ret_10d is None
    assert out.fwd_ret_20d is None
    assert out.fwd_ret_60d is None
    assert out.mfe_60d is None
    assert out.mae_60d is None

    # Can update outcome fields prospectively
    out.available_forward_bars = 10
    out.status_10d = HorizonStatus.MATURED.value
    out.fwd_ret_10d = 3.5
    out.mfe_10d = 5.2
    out.mae_10d = -1.2
    assert out.fwd_ret_10d == 3.5
