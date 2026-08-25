"""Tests for Phase 18 Forward-Testing Signal Export."""

from pathlib import Path
import pandas as pd
import pytest

from wyckoff_screener.forward_testing import (
    parse_candidates_csv_to_forward_signals,
    create_forward_testing_workbook,
    SCHEMA_VERSION,
)

CANDIDATES_PATH = Path("data/research_results/20260824/candidates.csv")


def test_parse_candidates_csv_reconciles_counts() -> None:
    """Verify 383 candidates (196 High Priority, 187 Qualified) parse cleanly."""
    assert CANDIDATES_PATH.exists(), f"Missing production candidates file at {CANDIDATES_PATH}"
    df = pd.read_csv(CANDIDATES_PATH)
    assert len(df) == 383

    signals = parse_candidates_csv_to_forward_signals(df, run_id="20260824_1530")
    assert len(signals) == 383

    hp = [s for s in signals if s.priority == "HIGH_PRIORITY_CANDIDATE"]
    q = [s for s in signals if s.priority == "QUALIFIED_CANDIDATE"]
    assert len(hp) == 196
    assert len(q) == 187


def test_signal_required_fields_non_null() -> None:
    """Verify all critical signal fields are populated and valid."""
    df = pd.read_csv(CANDIDATES_PATH)
    signals = parse_candidates_csv_to_forward_signals(df, run_id="20260824_1530")

    for sig in signals:
        assert sig.signal_id.startswith("20260824_1530_")
        assert len(sig.symbol) > 0
        assert sig.signal_date.startswith("2026-08-")
        assert sig.entry_price > 0.0

        assert sig.score >= 40.0
        assert sig.exchange == "NSE"
        assert sig.tradingview_url.startswith("https://www.tradingview.com")
        assert len(sig.wyckoff_event) > 0
