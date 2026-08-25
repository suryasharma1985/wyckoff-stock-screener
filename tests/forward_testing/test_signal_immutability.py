"""Tests for ForwardSignal immutability and lookahead protection."""

from dataclasses import FrozenInstanceError
import pandas as pd
import pytest

from wyckoff_screener.forward_testing.models import ForwardSignal
from wyckoff_screener.forward_testing.evaluator import evaluate_forward_performance


def test_forward_signal_dataclass_is_immutable() -> None:
    """Verify ForwardSignal is frozen and rejects attribute mutations."""
    sig = ForwardSignal(
        signal_id="20260824_1530_RELIANCE",
        run_id="20260824_1530",
        signal_date="2026-08-21",
        symbol="RELIANCE",
        company_name="Reliance Industries Limited",
        exchange="NSE",
        priority="HIGH_PRIORITY_CANDIDATE",
        score=75.0,
        signal_type="LPS",
        wyckoff_event="LPS",
        wyckoff_phase="Phase C/D Candidate",
        vsa_status="Vol: 0.8x, Spr: 0.6x, Pos: 0.6",
        p_and_f_score="Tgt: 3200",
        entry_price=2950.0,
        close_price=2950.0,
        broad_setup_status=True,
        mechanically_qualified=True,
        tradingview_url="https://www.tradingview.com",
        screening_date="2026-08-21",
        source_run_date="2026-08-21",
        notes="LPS evidence",
    )

    with pytest.raises(FrozenInstanceError):
        sig.entry_price = 3000.0  # type: ignore

    with pytest.raises(FrozenInstanceError):
        sig.score = 80.0  # type: ignore


def test_performance_evaluation_does_not_mutate_signal() -> None:
    """Verify that forward performance evaluation preserves signal attributes identically."""
    sig = ForwardSignal(
        signal_id="20260824_1530_TEST",
        run_id="20260824_1530",
        signal_date="2026-08-21",
        symbol="TEST",
        company_name="Test Corp",
        exchange="NSE",
        priority="HIGH_PRIORITY_CANDIDATE",
        score=72.0,
        signal_type="SOS",
        wyckoff_event="SOS",
        wyckoff_phase="Phase D Candidate",
        vsa_status="Vol: 2.5x",
        p_and_f_score="Tgt: 150",
        entry_price=100.0,
        close_price=100.0,
        broad_setup_status=True,
        mechanically_qualified=True,
        tradingview_url="https://www.tradingview.com",
        screening_date="2026-08-21",
        source_run_date="2026-08-21",
        notes="SOS evidence",
    )

    # Future bars with massive rally
    future_df = pd.DataFrame([
        {"Date": "2026-08-24", "Open": 100.0, "High": 135.0, "Low": 98.0, "Close": 130.0, "Volume": 5000},
    ])

    res = evaluate_forward_performance(sig, future_ohlc_df=future_df)

    # Performance values reflect future data
    assert res.result == "WIN"
    assert res.target_10_reached == "YES"
    assert res.target_20_reached == "YES"
    assert res.target_30_reached == "YES"
    assert res.max_gain_pct == 35.0

    # Signal itself remains strictly unchanged
    assert sig.entry_price == 100.0
    assert sig.score == 72.0
    assert sig.signal_date == "2026-08-21"
    assert sig.wyckoff_event == "SOS"
