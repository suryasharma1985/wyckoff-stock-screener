"""Tests for Signal_ID determinism and duplicate signal management."""

import pandas as pd
import pytest

from wyckoff_screener.forward_testing.exporter import parse_candidates_csv_to_forward_signals


def test_signal_id_determinism_and_multi_run_separation() -> None:
    """Verify that repeated signals on different run dates create distinct Signal_IDs."""
    df_run1 = pd.DataFrame([
        {
            "symbol": "TCS",
            "company_name": "Tata Consultancy Services Limited",
            "as_of_date": "2026-08-21",
            "candidate_category": "HIGH_PRIORITY_CANDIDATE",
            "composite_score": 72.0,
            "most_recent_event_type": "LPS",
            "close": 4200.0,
        }
    ])

    df_run2 = pd.DataFrame([
        {
            "symbol": "TCS",
            "company_name": "Tata Consultancy Services Limited",
            "as_of_date": "2026-09-15",
            "candidate_category": "QUALIFIED_CANDIDATE",
            "composite_score": 66.0,
            "most_recent_event_type": "SOS",
            "close": 4450.0,
        }
    ])

    signals_1 = parse_candidates_csv_to_forward_signals(df_run1, run_id="20260824_1530")
    signals_2 = parse_candidates_csv_to_forward_signals(df_run2, run_id="20260915_1530")

    assert len(signals_1) == 1
    assert len(signals_2) == 1

    # Deterministic and distinct IDs
    assert signals_1[0].signal_id == "20260824_1530_TCS"
    assert signals_2[0].signal_id == "20260915_1530_TCS"
    assert signals_1[0].signal_id != signals_2[0].signal_id

    # Entry prices and scores remain independent
    assert signals_1[0].entry_price == 4200.0
    assert signals_2[0].entry_price == 4450.0
    assert signals_1[0].score == 72.0
    assert signals_2[0].score == 66.0
