"""Unit tests for Wyckoff setup scoring and watchlist ranking."""

import pytest
import pandas as pd
import numpy as np

from wyckoff_screener.scoring.setup_scorer import (
    ScoredSetup,
    rank_watchlist,
    score_setup,
    WEIGHT_MECHANICAL_FILTERS,
    WEIGHT_RECENT_EVENT,
    WEIGHT_PEER_RANK,
    WEIGHT_PF_UPSIDE,
)


def _build_strong_fixture(num_bars: int = 250) -> pd.DataFrame:
    """Build synthetic OHLCV fixture of a strong Wyckoff markup setup with prior Spring and recent LPS."""
    dates = pd.date_range("2024-01-01", periods=num_bars)
    
    # 1. Bars 0..50: Flat base trading range around 100 [Low=98, High=105]
    opens = [100.0] * num_bars
    highs = [105.0] * num_bars
    lows = [98.0] * num_bars
    closes = [101.0] * num_bars
    volumes = [1000.0] * num_bars

    # 2. Bar 51: Spring (Low=94 undercut support 98, Close=102 back above)
    lows[51] = 94.0
    closes[51] = 102.0
    highs[51] = 103.0
    volumes[51] = 1600.0

    # 3. Bar 55: LPS (Higher low 99 > 94, holds support >= 98, low volume 400 < 0.75x)
    lows[55] = 99.0
    closes[55] = 103.0
    highs[55] = 104.0
    volumes[55] = 400.0

    # 4. Bar 60: SOS breakout (Close=110 > 105 resistance, volume 2500, close pos near high)
    lows[60] = 104.0
    opens[60] = 105.0
    closes[60] = 110.0
    highs[60] = 111.0
    volumes[60] = 2500.0

    # 5. Bars 61..199: Steady markup uptrend from 110 to 180
    for idx in range(61, 200):
        step_price = 110.0 + (idx - 61) * (70.0 / (200 - 61))
        opens[idx] = step_price - 0.5
        highs[idx] = step_price + 1.5
        lows[idx] = step_price - 1.5
        closes[idx] = step_price + 0.5
        volumes[idx] = 1000.0

    # 6. Bars 200..240: Reaccumulation range at 180 [Low=176, High=185]
    for idx in range(200, 241):
        opens[idx] = 180.0
        highs[idx] = 185.0
        lows[idx] = 176.0
        closes[idx] = 181.0
        volumes[idx] = 1000.0

    # 7. Bar 241: Spring in reaccumulation base (Low=172 < 176, Close=182)
    lows[241] = 172.0
    closes[241] = 182.0
    highs[241] = 183.0
    volumes[241] = 1500.0

    # 8. Bar 245: Fresh LPS 5 bars ago (Higher low 178 > 172, holding range, low volume 350)
    lows[245] = 178.0
    closes[245] = 183.0
    highs[245] = 184.0
    volumes[245] = 350.0

    # 9. Bars 246..249: Holding higher
    for idx in range(246, num_bars):
        opens[idx] = 183.0
        highs[idx] = 186.0
        lows[idx] = 182.0
        closes[idx] = 185.0
        volumes[idx] = 800.0

    return pd.DataFrame({
        "Date": dates,
        "Open": opens,
        "High": highs,
        "Low": lows,
        "Close": closes,
        "Volume": volumes,
    })


def _build_weak_utad_fixture(num_bars: int = 100) -> pd.DataFrame:
    """Build synthetic OHLCV fixture ending in a severe UTAD rejection with no prior base."""
    dates = pd.date_range("2024-01-01", periods=num_bars)
    prices = [100.0] * num_bars
    
    highs = [102.0] * num_bars
    lows = [98.0] * num_bars
    opens = [100.0] * num_bars
    closes = [100.0] * num_bars
    volumes = [1000.0] * num_bars

    # Bar 99: UTAD (high spikes to 110 above 102 resistance, closes down at 99 on heavy 3500 volume)
    highs[99] = 110.0
    opens[99] = 101.0
    lows[99] = 98.0
    closes[99] = 99.0
    volumes[99] = 3500.0

    return pd.DataFrame({
        "Date": dates,
        "Open": opens,
        "High": highs,
        "Low": lows,
        "Close": closes,
        "Volume": volumes,
    })


def test_weights_sum_to_100():
    """Verify that scoring weights explicitly sum to 100.0."""
    total_weights = WEIGHT_MECHANICAL_FILTERS + WEIGHT_RECENT_EVENT + WEIGHT_PEER_RANK + WEIGHT_PF_UPSIDE
    assert total_weights == 100.0


def test_strong_setup_scoring():
    """Verify strong setup scores high, passes filters, and has no disqualifying flags."""
    df_strong = _build_strong_fixture()
    scored = score_setup(df_strong, symbol="STRONG_STOCK", peer_rank=1, total_peers=3)

    assert scored.symbol == "STRONG_STOCK"
    assert scored.is_disqualified is False
    assert len(scored.disqualifying_flags) == 0
    assert scored.composite_score > 60.0
    assert "mechanical_filters" in scored.score_breakdown
    assert "schematic_recency" in scored.score_breakdown
    assert "peer_relative_strength" in scored.score_breakdown
    assert "pf_target_upside" in scored.score_breakdown
    assert scored.peer_analysis_skipped is False


def test_weak_utad_setup_is_disqualified():
    """Verify weak setup with recent UTAD gets flagged as disqualified with red flag."""
    df_weak = _build_weak_utad_fixture()
    scored = score_setup(df_weak, symbol="WEAK_UTAD_STOCK", peer_rank=3, total_peers=3)

    assert scored.symbol == "WEAK_UTAD_STOCK"
    assert scored.is_disqualified is True
    assert any("UTAD" in flag for flag in scored.disqualifying_flags)
    assert scored.score_breakdown["schematic_recency"] == 0.0


def test_rank_watchlist_orders_qualified_first():
    """Verify watchlist ranking places qualified strong setups above disqualified setups."""
    df_strong = _build_strong_fixture()
    df_weak = _build_weak_utad_fixture()

    watchlist = {
        "WEAK_UTAD": df_weak,
        "STRONG_LPS": df_strong,
    }

    ranked = rank_watchlist(watchlist, peer_rankings={"STRONG_LPS": 1, "WEAK_UTAD": 2})

    assert len(ranked) == 2
    # Strong setup must be rank 1
    assert ranked[0].symbol == "STRONG_LPS"
    assert ranked[0].is_disqualified is False

    # Weak UTAD setup must be at the bottom
    assert ranked[1].symbol == "WEAK_UTAD"
    assert ranked[1].is_disqualified is True


def test_peer_rank_none_scores_zero_and_flags_skipped():
    """Verify bug fix: when peer_rank is None, peer score is strictly 0.0 and peer_analysis_skipped is True."""
    df_strong = _build_strong_fixture()
    scored = score_setup(df_strong, symbol="NO_PEER_STOCK", peer_rank=None)

    assert scored.peer_analysis_skipped is True
    assert scored.peer_rank is None
    assert scored.score_breakdown["peer_relative_strength"] == 0.0


def test_schematic_recency_decay_fresh_vs_old_lps():
    """Verify recency decay: fresh LPS (5 bars ago) scores 40.0 pts vs old LPS (60 bars ago) scores 15.0 pts."""
    # 1. Fresh LPS (from strong fixture at bar 245 out of 250)
    df_fresh = _build_strong_fixture(num_bars=250)
    scored_fresh = score_setup(df_fresh, symbol="FRESH_LPS", peer_rank=1)
    assert scored_fresh.score_breakdown["schematic_recency"] == 40.0

    # 2. Old LPS (append 60 bars of flat continuation so LPS at bar 245 is now 65 bars ago)
    extra_dates = pd.date_range("2024-09-08", periods=60)
    extra_df = pd.DataFrame({
        "Date": extra_dates,
        "Open": [185.0] * 60,
        "High": [187.0] * 60,
        "Low": [183.0] * 60,
        "Close": [185.0] * 60,
        "Volume": [1000.0] * 60,
    })
    df_old = pd.concat([df_fresh, extra_df], ignore_index=True)
    scored_old = score_setup(df_old, symbol="OLD_LPS", peer_rank=1)

    assert scored_old.score_breakdown["schematic_recency"] == 15.0
    assert scored_fresh.composite_score > scored_old.composite_score


def test_all_mechanical_filters_failing_disqualifies():
    """Verify setup that fails all mechanical filters gets flagged as disqualified."""
    # Monotonic downtrend from 200 to 50
    dates = pd.date_range("2024-01-01", periods=100)
    prices = np.linspace(200.0, 50.0, 100)
    df_down = pd.DataFrame({
        "Date": dates,
        "Open": prices + 1.0,
        "High": prices + 2.0,
        "Low": prices - 2.0,
        "Close": prices - 1.0,
        "Volume": [1000.0] * 100,
    })

    scored = score_setup(df_down, symbol="DOWN_STOCK")
    assert scored.is_disqualified is True
    assert any("Failed all mechanical" in flag for flag in scored.disqualifying_flags)
    assert scored.score_breakdown["mechanical_filters"] == 0.0


def test_multiple_disqualifying_flags_simultaneous():
    """Verify setup with multiple red flags accumulates all disqualifying reasons."""
    df_weak = _build_weak_utad_fixture()
    scored = score_setup(df_weak, symbol="MULTI_FLAG")

    assert scored.is_disqualified is True
    # Must have multiple disqualifying flags simultaneously (UTAD + Failed mechanical filters)
    assert len(scored.disqualifying_flags) >= 2
    assert any("UTAD" in f for f in scored.disqualifying_flags)
    assert any("Failed all mechanical" in f for f in scored.disqualifying_flags)


def test_stale_pf_anchor_scores_zero_and_flags_warning():
    """Verify that an anchor event >60 bars ago sets stale_anchor=True, scores 0 pts, and adds warning."""
    # 200 bars total: base trading range at bars 0..50 with Spring at 51, LPS at 55
    # Then bars 56..200 (145 bars) drift sideways/downwards so LPS is 145 bars old (>60)
    dates = pd.date_range("2024-01-01", periods=200)
    opens = [100.0] * 200
    highs = [105.0] * 200
    lows = [98.0] * 200
    closes = [101.0] * 200
    volumes = [1000.0] * 200

    # Spring at 51
    lows[51] = 94.0
    closes[51] = 102.0
    highs[51] = 103.0
    volumes[51] = 1600.0

    # LPS at 55 (145 bars ago from end of 200 bars)
    lows[55] = 99.0
    closes[55] = 103.0
    highs[55] = 104.0
    volumes[55] = 400.0

    # Bars 56..199: flat sideways around 101
    df_stale = pd.DataFrame({
        "Date": dates,
        "Open": opens,
        "High": highs,
        "Low": lows,
        "Close": closes,
        "Volume": volumes,
    })

    scored = score_setup(df_stale, symbol="STALE_PF")
    assert scored.pf_price_objective is not None
    assert scored.pf_price_objective.stale_anchor is True
    assert "WARNING: Count row anchor" in scored.pf_price_objective.supporting_note
    assert scored.score_breakdown["pf_target_upside"] == 0.0
