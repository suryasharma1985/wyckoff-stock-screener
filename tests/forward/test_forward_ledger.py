"""Unit tests for Phase 11 Forward Validation Ledger manager and snapshot persistence."""

from pathlib import Path
import pytest
import pandas as pd

from wyckoff_screener.forward.ledger import (
    DuplicateScreeningDateError,
    ForwardLedger,
)
from wyckoff_screener.forward.models import (
    FORWARD_ENGINE_VERSION,
    ForwardCandidateRecord,
    HorizonStatus,
    generate_candidate_id,
)
from wyckoff_screener.research.models import ResearchCandidateResult


def _make_dummy_candidate(
    symbol: str = "ANANTRAJ",
    screening_date: str = "2026-08-24",
    close_price: float = 750.0,
    category: str = "HIGH_PRIORITY_CANDIDATE",
    score: float = 75.0,
) -> ForwardCandidateRecord:
    """Helper to construct a mock ForwardCandidateRecord for ledger testing."""
    cand_id = generate_candidate_id(symbol, screening_date, close_price, FORWARD_ENGINE_VERSION)
    return ForwardCandidateRecord(
        candidate_id=cand_id,
        screening_date=screening_date,
        symbol=symbol,
        yfinance_ticker=f"{symbol}.NS",
        company_name=f"{symbol} Limited",
        reference_close_price=close_price,
        data_bars=500,
        candidate_category=category,
        composite_score=score,
        is_mechanically_qualified=True,
        is_disqualified=False,
        disqualifying_flags="None",
        weekly_uptrend=True,
        dma_50_above_100=True,
        rsi_in_band=True,
        atr_contracting=True,
        vcp_bbw_contracting=True,
        vsa_volume_ratio=2.1,
        vsa_spread_ratio=1.5,
        vsa_close_position=0.8,
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
        numeric_evidence="LPS candidate detected",
        pf_target_price=900.0,
        pf_upside_pct=20.0,
        pf_count_columns=8,
        pf_is_stale_anchor=False,
        explanation_summary="Valid LPS test on support",
        tradingview_daily_url="https://tradingview.com/chart/?symbol=NSE:ANANTRAJ",
        tradingview_weekly_url="",
        tradingview_75m_url="",
        engine_version=FORWARD_ENGINE_VERSION,
        created_at_utc="2026-08-24T10:00:00Z",
    )


def test_forward_ledger_save_and_load_snapshot(tmp_path: Path):
    """Verify that forward ledger writes and reads immutable snapshots accurately."""
    ledger = ForwardLedger(base_dir=tmp_path)

    c1 = _make_dummy_candidate("ANANTRAJ", "2026-08-24", 750.0, "HIGH_PRIORITY_CANDIDATE", 75.0)
    c2 = _make_dummy_candidate("APOLLO", "2026-08-24", 520.0, "QUALIFIED_CANDIDATE", 55.0)

    manifest = ledger.save_screening_snapshot(
        screening_date="2026-08-24",
        candidate_records=[c1, c2],
        source_description="Test Screening Run",
        overwrite=False,
    )

    assert manifest.screening_date == "2026-08-24"
    assert manifest.total_candidates == 2
    assert manifest.category_counts["HIGH_PRIORITY_CANDIDATE"] == 1
    assert manifest.category_counts["QUALIFIED_CANDIDATE"] == 1

    # Verify snapshot file on disk
    snap_path = ledger.get_snapshot_path("2026-08-24")
    assert snap_path.exists()

    # Load back
    loaded = ledger.load_snapshot("2026-08-24")
    assert loaded.snapshot_id == manifest.snapshot_id
    assert loaded.total_candidates == 2
    assert len(loaded.candidate_records) == 2
    assert loaded.candidate_records[0]["symbol"] == "ANANTRAJ"


def test_forward_ledger_duplicate_protection(tmp_path: Path):
    """Verify that saving a snapshot for an existing date without overwrite raises an error."""
    ledger = ForwardLedger(base_dir=tmp_path)
    c1 = _make_dummy_candidate("ANANTRAJ", "2026-08-24", 750.0)

    ledger.save_screening_snapshot("2026-08-24", [c1], overwrite=False)

    # Second run without overwrite MUST fail
    with pytest.raises(DuplicateScreeningDateError):
        ledger.save_screening_snapshot("2026-08-24", [c1], overwrite=False)

    # Second run with explicit overwrite MUST succeed
    c1_updated = _make_dummy_candidate("ANANTRAJ", "2026-08-24", 755.0)
    manifest_updated = ledger.save_screening_snapshot("2026-08-24", [c1_updated], overwrite=True)
    assert manifest_updated.candidate_records[0]["reference_close_price"] == 755.0


def test_forward_ledger_sync_tables(tmp_path: Path):
    """Verify that forward_ledger.csv and forward_outcomes.csv sync correctly."""
    ledger = ForwardLedger(base_dir=tmp_path)

    c1 = _make_dummy_candidate("ANANTRAJ", "2026-08-24", 750.0)
    c2 = _make_dummy_candidate("HINDCOPPER", "2026-08-25", 340.0)

    ledger.save_screening_snapshot("2026-08-24", [c1])
    ledger.save_screening_snapshot("2026-08-25", [c2])

    ledger_df = ledger.load_ledger_dataframe()
    assert len(ledger_df) == 2
    assert set(ledger_df["symbol"].tolist()) == {"ANANTRAJ", "HINDCOPPER"}

    outcomes_df = ledger.load_outcomes_dataframe()
    assert len(outcomes_df) == 2
    assert set(outcomes_df["symbol"].tolist()) == {"ANANTRAJ", "HINDCOPPER"}
    assert all(outcomes_df["status_10d"] == HorizonStatus.PENDING.value)
    assert all(outcomes_df["available_forward_bars"] == 0)


def test_candidate_result_to_forward_record_conversion(tmp_path: Path):
    """Verify conversion from Phase 9C ResearchCandidateResult into ForwardCandidateRecord."""
    ledger = ForwardLedger(base_dir=tmp_path)

    res = ResearchCandidateResult(
        symbol="ANANTRAJ",
        yfinance_ticker="ANANTRAJ.NS",
        company_name="Anant Raj Limited",
        as_of_date="2026-08-24",
        data_bars=700,
        dataset_snapshot_path="data/research_datasets/20260823",
        dataset_date="20260823",
        candidate_category="HIGH_PRIORITY_CANDIDATE",
        is_research_eligible=True,
        is_mechanically_qualified=True,
        is_disqualified=False,
        disqualifying_flags=[],
        composite_score=78.2,
        score_breakdown={"mechanical_filters": 30.0, "recent_event": 30.0, "peer_rank": 10.0, "pf_upside": 8.2},
        peer_analysis_skipped=False,
        filter_flags={"weekly_uptrend": True, "dma_50_above_100": True, "rsi_in_band": True, "atr_contracting": True, "vcp_bbw_contracting": False},
        filter_values={"close": 752.40, "rsi_14": 62.5},
        vsa_volume_ratio=2.4,
        vsa_spread_ratio=1.7,
        vsa_close_position=0.88,
        is_stopping_volume=False,
        is_no_demand=False,
        is_no_supply=False,
        is_effort_vs_result=False,
        most_recent_event_type="SOS",
        most_recent_event_date="2026-08-22",
        possible_LPS=False,
        possible_SOS=True,
        possible_Spring=False,
        is_UTAD_warning=False,
        total_events_detected=3,
        numeric_evidence="SOS breakout bar on 2.4x volume",
        pf_target_price=950.0,
        pf_upside_pct=26.26,
        pf_count_columns=9,
        pf_is_stale_anchor=False,
        explanation_summary="Sign of Strength breakout detected",
        tradingview_daily_url="https://tradingview.com/chart/?symbol=NSE:ANANTRAJ",
        tradingview_weekly_url="",
        tradingview_75m_url="",
    )

    fwd_rec = ledger.candidate_result_to_forward_record(res)
    assert fwd_rec.symbol == "ANANTRAJ"
    assert fwd_rec.screening_date == "2026-08-24"
    assert fwd_rec.reference_close_price == 752.40
    assert fwd_rec.candidate_category == "HIGH_PRIORITY_CANDIDATE"
    assert fwd_rec.possible_SOS is True
    assert fwd_rec.vsa_volume_ratio == 2.4
    assert fwd_rec.pf_target_price == 950.0
