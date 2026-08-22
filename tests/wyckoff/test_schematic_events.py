"""Unit tests for Wyckoff schematic event detectors.

Contains dedicated hand-built synthetic OHLCV fixtures for all 7 event types:
- Selling Climax (SC) + near misses
- Automatic Rally (AR) + near misses
- Secondary Test (ST) + near misses
- Spring + near misses
- Last Point of Support (LPS) + near misses
- Sign of Strength (SOS) + near misses
- Upthrust After Distribution (UTAD) + near misses
"""

import pytest
import numpy as np
import pandas as pd

from wyckoff_screener.wyckoff.schematic_events import (
    detect_all_schematic_events,
    detect_automatic_rally_candidates,
    detect_lps_candidates,
    detect_secondary_test_candidates,
    detect_selling_climax_candidates,
    detect_sos_candidates,
    detect_spring_candidates,
    detect_utad_candidates,
)


# ============================================================================
# 1. Selling Climax (SC) Tests
# ============================================================================

def test_selling_climax_hit():
    """Verify SC candidate fires on wide spread, down-close, climactic volume after clear decline."""
    # 20 bars in clear decline: 200 down to 150
    dates = pd.date_range("2024-01-01", periods=21)
    open_prices = [200.0 - i * 2.5 for i in range(20)] + [150.0]
    high_prices = [o + 2.0 for o in open_prices[:-1]] + [152.0]
    low_prices = [o - 4.0 for o in open_prices[:-1]] + [110.0]
    close_prices = [o - 3.0 for o in open_prices[:-1]] + [112.0]  # Bar 20 down-close: 150 -> 112
    volumes = [1000.0] * 20 + [4000.0]  # Bar 20 climactic volume

    df = pd.DataFrame({
        "Date": dates,
        "Open": open_prices,
        "High": high_prices,
        "Low": low_prices,
        "Close": close_prices,
        "Volume": volumes,
    })

    events = detect_selling_climax_candidates(df)
    assert len(events) == 1
    sc = events[0]
    assert sc.event_type == "SC"
    assert sc.date == dates[20]
    assert sc.price == 112.0
    assert sc.volume_ratio >= 2.0
    assert sc.spread_ratio >= 1.5
    assert "Candidate SC" in sc.supporting_note


def test_selling_climax_near_miss_low_volume():
    """Near miss: wide spread and down-close, but volume_ratio is 1.7 (< 2.0 threshold)."""
    dates = pd.date_range("2024-01-01", periods=21)
    open_prices = [200.0 - i * 2.5 for i in range(20)] + [150.0]
    high_prices = [o + 2.0 for o in open_prices[:-1]] + [152.0]
    low_prices = [o - 4.0 for o in open_prices[:-1]] + [110.0]
    close_prices = [o - 3.0 for o in open_prices[:-1]] + [112.0]
    volumes = [1000.0] * 20 + [1700.0]  # Not climactic enough

    df = pd.DataFrame({
        "Date": dates,
        "Open": open_prices,
        "High": high_prices,
        "Low": low_prices,
        "Close": close_prices,
        "Volume": volumes,
    })

    events = detect_selling_climax_candidates(df)
    assert len(events) == 0


def test_selling_climax_near_miss_up_close():
    """Near miss: climactic volume and wide spread, but close is above open (up-close)."""
    dates = pd.date_range("2024-01-01", periods=21)
    open_prices = [200.0 - i * 2.5 for i in range(20)] + [115.0]
    high_prices = [o + 2.0 for o in open_prices[:-1]] + [152.0]
    low_prices = [o - 4.0 for o in open_prices[:-1]] + [110.0]
    close_prices = [o - 3.0 for o in open_prices[:-1]] + [150.0]  # Up close (150 > 115)
    volumes = [1000.0] * 20 + [4000.0]

    df = pd.DataFrame({
        "Date": dates,
        "Open": open_prices,
        "High": high_prices,
        "Low": low_prices,
        "Close": close_prices,
        "Volume": volumes,
    })

    events = detect_selling_climax_candidates(df)
    assert len(events) == 0


# ============================================================================
# 2. Automatic Rally (AR) Tests
# ============================================================================

def test_automatic_rally_hit():
    """Verify AR candidate fires on sharp up bar immediately following SC with volume_ratio >= 1.0."""
    dates = pd.date_range("2024-01-01", periods=22)
    # 20 bars decline + Bar 20 SC + Bar 21 AR
    open_prices = [200.0 - i * 2.5 for i in range(20)] + [150.0, 114.0]
    high_prices = [o + 2.0 for o in open_prices[:20]] + [152.0, 140.0]
    low_prices = [o - 4.0 for o in open_prices[:20]] + [110.0, 112.0]
    close_prices = [o - 3.0 for o in open_prices[:20]] + [112.0, 138.0]  # Bar 21 sharp up bar
    volumes = [1000.0] * 20 + [4000.0, 2000.0]  # Bar 21 vol_ratio >= 1.0

    df = pd.DataFrame({
        "Date": dates,
        "Open": open_prices,
        "High": high_prices,
        "Low": low_prices,
        "Close": close_prices,
        "Volume": volumes,
    })

    ar_events = detect_automatic_rally_candidates(df)
    assert len(ar_events) == 1
    ar = ar_events[0]
    assert ar.event_type == "AR"
    assert ar.date == dates[21]
    assert ar.price == 138.0
    assert ar.volume_ratio >= 1.0


def test_automatic_rally_near_miss_down_bar():
    """Near miss: bar following SC is a down bar."""
    dates = pd.date_range("2024-01-01", periods=22)
    open_prices = [200.0 - i * 2.5 for i in range(20)] + [150.0, 112.0]
    high_prices = [o + 2.0 for o in open_prices[:20]] + [152.0, 115.0]
    low_prices = [o - 4.0 for o in open_prices[:20]] + [110.0, 105.0]
    close_prices = [o - 3.0 for o in open_prices[:20]] + [112.0, 108.0]  # Down bar
    volumes = [1000.0] * 20 + [4000.0, 2000.0]

    df = pd.DataFrame({
        "Date": dates,
        "Open": open_prices,
        "High": high_prices,
        "Low": low_prices,
        "Close": close_prices,
        "Volume": volumes,
    })

    ar_events = detect_automatic_rally_candidates(df)
    assert len(ar_events) == 0


# ============================================================================
# 3. Secondary Test (ST) Tests
# ============================================================================

def test_secondary_test_hit():
    """Verify ST candidate fires on retest of SC low area on strictly lower volume."""
    dates = pd.date_range("2024-01-01", periods=25)
    # Bars 0..19: decline
    # Bar 20: SC with Low=100.0, Close=102.0, Vol=4000 (vol_ratio ~ 3.5)
    # Bar 21: AR rebound to 125.0
    # Bars 22..23: trading in range
    # Bar 24: ST retest with Low=101.0 (within 3% of 100), Vol=800 (vol_ratio ~ 0.7 << 3.5)
    open_prices = [200.0 - i * 4.0 for i in range(20)] + [140.0, 104.0, 120.0, 115.0, 108.0]
    high_prices = [o + 2.0 for o in open_prices[:20]] + [142.0, 126.0, 122.0, 118.0, 110.0]
    low_prices = [o - 4.0 for o in open_prices[:20]] + [100.0, 103.0, 114.0, 110.0, 101.0]  # Bar 24 Low = 101.0
    close_prices = [o - 3.0 for o in open_prices[:20]] + [102.0, 125.0, 116.0, 112.0, 104.0]
    volumes = [1000.0] * 20 + [4000.0, 2000.0, 1200.0, 900.0, 800.0]

    df = pd.DataFrame({
        "Date": dates,
        "Open": open_prices,
        "High": high_prices,
        "Low": low_prices,
        "Close": close_prices,
        "Volume": volumes,
    })

    st_events = detect_secondary_test_candidates(df)
    assert len(st_events) == 1
    st = st_events[0]
    assert st.event_type == "ST"
    assert st.date == dates[24]
    assert "Candidate ST" in st.supporting_note


def test_secondary_test_near_miss_high_volume():
    """Near miss: price retests low area but volume is higher than SC."""
    dates = pd.date_range("2024-01-01", periods=25)
    open_prices = [200.0 - i * 4.0 for i in range(20)] + [140.0, 104.0, 120.0, 115.0, 108.0]
    high_prices = [o + 2.0 for o in open_prices[:20]] + [142.0, 126.0, 122.0, 118.0, 110.0]
    low_prices = [o - 4.0 for o in open_prices[:20]] + [100.0, 103.0, 114.0, 110.0, 101.0]
    close_prices = [o - 3.0 for o in open_prices[:20]] + [102.0, 125.0, 116.0, 112.0, 104.0]
    volumes = [1000.0] * 20 + [4000.0, 2000.0, 1200.0, 900.0, 5000.0]  # Vol 5000 > SC vol 4000

    df = pd.DataFrame({
        "Date": dates,
        "Open": open_prices,
        "High": high_prices,
        "Low": low_prices,
        "Close": close_prices,
        "Volume": volumes,
    })

    st_events = detect_secondary_test_candidates(df)
    assert len(st_events) == 0


# ============================================================================
# 4. Spring Tests
# ============================================================================

def test_spring_hit():
    """Verify Spring candidate fires when low undercuts prior support and closes back above it."""
    # 20 bars oscillating in [100, 120] -> prior support is 100.0
    dates = pd.date_range("2024-01-01", periods=21)
    high_prices = [120.0] * 20 + [108.0]
    low_prices = [100.0] * 20 + [95.0]  # Bar 20 undercuts support (95 < 100)
    open_prices = [105.0] * 20 + [98.0]
    close_prices = [110.0] * 20 + [104.0]  # Bar 20 closes back above support (104 > 100)
    volumes = [1000.0] * 21

    df = pd.DataFrame({
        "Date": dates,
        "Open": open_prices,
        "High": high_prices,
        "Low": low_prices,
        "Close": close_prices,
        "Volume": volumes,
    })

    springs = detect_spring_candidates(df)
    assert len(springs) == 1
    spring = springs[0]
    assert spring.event_type == "Spring"
    assert spring.date == dates[20]
    assert spring.price == 104.0
    assert "undercut prior support" in spring.supporting_note


def test_spring_near_miss_closes_below_support():
    """Near miss: low undercuts support but close remains below support (breakdown)."""
    dates = pd.date_range("2024-01-01", periods=21)
    high_prices = [120.0] * 20 + [99.0]
    low_prices = [100.0] * 20 + [94.0]  # Undercuts 100
    open_prices = [105.0] * 20 + [98.0]
    close_prices = [110.0] * 20 + [96.0]  # Closes BELOW 100
    volumes = [1000.0] * 21

    df = pd.DataFrame({
        "Date": dates,
        "Open": open_prices,
        "High": high_prices,
        "Low": low_prices,
        "Close": close_prices,
        "Volume": volumes,
    })

    springs = detect_spring_candidates(df)
    assert len(springs) == 0


# ============================================================================
# 5. Last Point of Support (LPS) Tests
# ============================================================================

def test_lps_hit():
    """Verify LPS candidate fires on higher low than prior Spring/ST, volume_ratio < 0.75, holding support."""
    # 20 bars range [100, 120]
    # Bar 20: Spring (Low=95, Close=104)
    # Bar 21..23: rally to 118
    # Bar 24: LPS pullback (Low=103 > 95, Close=106 >= 100 support, Volume=400 -> vol_ratio ~ 0.4 < 0.75)
    dates = pd.date_range("2024-01-01", periods=25)
    high_prices = [120.0] * 20 + [108.0, 118.0, 116.0, 112.0, 108.0]
    low_prices = [100.0] * 20 + [95.0, 104.0, 110.0, 106.0, 103.0]  # Bar 24 Low = 103 > 95
    open_prices = [105.0] * 20 + [98.0, 106.0, 112.0, 110.0, 105.0]
    close_prices = [110.0] * 20 + [104.0, 116.0, 114.0, 108.0, 106.0]  # Bar 24 Close = 106 >= 100
    volumes = [1000.0] * 20 + [1000.0, 1500.0, 1200.0, 800.0, 400.0]  # Bar 24 low volume (400)

    df = pd.DataFrame({
        "Date": dates,
        "Open": open_prices,
        "High": high_prices,
        "Low": low_prices,
        "Close": close_prices,
        "Volume": volumes,
    })

    lps_events = detect_lps_candidates(df)
    assert len(lps_events) >= 1
    lps = lps_events[-1]
    assert lps.event_type == "LPS"
    assert lps.volume_ratio < 0.75
    assert "higher low" in lps.supporting_note


def test_lps_near_miss_high_volume():
    """Near miss: higher low holds support, but volume_ratio is 1.2 (>= 0.75 threshold)."""
    dates = pd.date_range("2024-01-01", periods=25)
    high_prices = [120.0] * 20 + [108.0, 118.0, 116.0, 112.0, 108.0]
    low_prices = [100.0] * 20 + [95.0, 104.0, 110.0, 106.0, 103.0]
    open_prices = [105.0] * 20 + [98.0, 106.0, 112.0, 110.0, 105.0]
    close_prices = [110.0] * 20 + [104.0, 116.0, 114.0, 108.0, 106.0]
    volumes = [1000.0] * 20 + [1000.0, 1500.0, 1200.0, 800.0, 1400.0]  # High volume (1400)

    df = pd.DataFrame({
        "Date": dates,
        "Open": open_prices,
        "High": high_prices,
        "Low": low_prices,
        "Close": close_prices,
        "Volume": volumes,
    })

    lps_events = detect_lps_candidates(df)
    assert len(lps_events) == 0


# ============================================================================
# 6. Sign of Strength (SOS) Tests
# ============================================================================

def test_sos_hit():
    """Verify SOS candidate fires on close breaking resistance with volume_ratio >= 1.5 and close_position > 0.7."""
    # 20 bars in range [100, 120] -> resistance is 120.0
    # Bar 20: Open=118, Low=117, High=132, Close=130 (close_pos = 13/15 = 0.867 > 0.7, Vol=3000 -> vol_ratio ~ 2.7 >= 1.5)
    dates = pd.date_range("2024-01-01", periods=21)
    high_prices = [120.0] * 20 + [132.0]
    low_prices = [100.0] * 20 + [117.0]
    open_prices = [105.0] * 20 + [118.0]
    close_prices = [110.0] * 20 + [130.0]
    volumes = [1000.0] * 20 + [3000.0]

    df = pd.DataFrame({
        "Date": dates,
        "Open": open_prices,
        "High": high_prices,
        "Low": low_prices,
        "Close": close_prices,
        "Volume": volumes,
    })

    sos_events = detect_sos_candidates(df)
    assert len(sos_events) == 1
    sos = sos_events[0]
    assert sos.event_type == "SOS"
    assert sos.date == dates[20]
    assert sos.price == 130.0
    assert sos.volume_ratio >= 1.5
    assert sos.close_position > 0.7
    assert "broke above range resistance" in sos.supporting_note


def test_sos_near_miss_weak_close():
    """Near miss: close breaks resistance and volume is high, but close_position is 0.4 (<= 0.7)."""
    dates = pd.date_range("2024-01-01", periods=21)
    high_prices = [120.0] * 20 + [135.0]
    low_prices = [100.0] * 20 + [115.0]
    open_prices = [105.0] * 20 + [118.0]
    close_prices = [110.0] * 20 + [123.0]  # Close 123 > 120, but pos = (123-115)/20 = 0.40 <= 0.7
    volumes = [1000.0] * 20 + [3000.0]

    df = pd.DataFrame({
        "Date": dates,
        "Open": open_prices,
        "High": high_prices,
        "Low": low_prices,
        "Close": close_prices,
        "Volume": volumes,
    })

    sos_events = detect_sos_candidates(df)
    assert len(sos_events) == 0


# ============================================================================
# 7. Upthrust After Distribution (UTAD) Tests
# ============================================================================

def test_utad_hit():
    """Verify UTAD candidate fires when high breaks resistance intrabar but closes back below it."""
    # 20 bars range [100, 120] -> resistance = 120.0
    # Bar 20: High=128 (> 120), Close=116 (< 120), Volume=2000 (vol_ratio >= 1.0)
    dates = pd.date_range("2024-01-01", periods=21)
    high_prices = [120.0] * 20 + [128.0]
    low_prices = [100.0] * 20 + [112.0]
    open_prices = [105.0] * 20 + [118.0]
    close_prices = [110.0] * 20 + [116.0]
    volumes = [1000.0] * 20 + [2000.0]

    df = pd.DataFrame({
        "Date": dates,
        "Open": open_prices,
        "High": high_prices,
        "Low": low_prices,
        "Close": close_prices,
        "Volume": volumes,
    })

    utads = detect_utad_candidates(df)
    assert len(utads) == 1
    utad = utads[0]
    assert utad.event_type == "UTAD"
    assert utad.date == dates[20]
    assert utad.price == 116.0
    assert "exceeded range resistance" in utad.supporting_note


def test_utad_near_miss_closes_above():
    """Near miss: high breaks resistance, but close stays above resistance (breakout rather than UTAD)."""
    dates = pd.date_range("2024-01-01", periods=21)
    high_prices = [120.0] * 20 + [128.0]
    low_prices = [100.0] * 20 + [112.0]
    open_prices = [105.0] * 20 + [118.0]
    close_prices = [110.0] * 20 + [124.0]  # Closed ABOVE 120
    volumes = [1000.0] * 20 + [2000.0]

    df = pd.DataFrame({
        "Date": dates,
        "Open": open_prices,
        "High": high_prices,
        "Low": low_prices,
        "Close": close_prices,
        "Volume": volumes,
    })

    utads = detect_utad_candidates(df)
    assert len(utads) == 0


def test_utad_near_miss_low_volume():
    """Near miss: high breaks resistance and closes below, but volume_ratio is 1.25 (< 1.5 threshold)."""
    dates = pd.date_range("2024-01-01", periods=21)
    high_prices = [120.0] * 20 + [128.0]
    low_prices = [100.0] * 20 + [112.0]
    open_prices = [105.0] * 20 + [118.0]
    close_prices = [110.0] * 20 + [116.0]
    volumes = [1000.0] * 20 + [1250.0]  # vol_ratio = 1250 / 1012.5 ~ 1.23 < 1.5

    df = pd.DataFrame({
        "Date": dates,
        "Open": open_prices,
        "High": high_prices,
        "Low": low_prices,
        "Close": close_prices,
        "Volume": volumes,
    })

    utads = detect_utad_candidates(df)
    assert len(utads) == 0


def test_detect_all_schematic_events_dictionary():
    """Verify detect_all_schematic_events returns dict with all 7 event keys."""
    dates = pd.date_range("2024-01-01", periods=25)
    df = pd.DataFrame({
        "Date": dates,
        "Open": [100.0] * 25,
        "High": [105.0] * 25,
        "Low": [95.0] * 25,
        "Close": [102.0] * 25,
        "Volume": [1000.0] * 25,
    })

    results = detect_all_schematic_events(df)
    assert set(results.keys()) == {"SC", "AR", "ST", "Spring", "LPS", "SOS", "UTAD"}
    for event_type, events in results.items():
        assert isinstance(events, list)


def test_st_and_lps_single_event_per_anchor_bounded():
    """Verify bug fix: only ONE event is recorded per anchor, even if multiple bars qualify within lookahead."""
    # 20 bars range [100, 120]
    # Bar 20: Spring anchor with Low=95, Close=104
    # Bars 21..28: 8 consecutive bars that each satisfy LPS criteria (higher low > 95, volume < 0.75, holds support >= 100)
    dates = pd.date_range("2024-01-01", periods=29)
    high_prices = [120.0] * 20 + [108.0] + [112.0] * 8
    low_prices = [100.0] * 20 + [95.0] + [103.0] * 8  # 8 consecutive candidate bars
    open_prices = [105.0] * 20 + [98.0] + [105.0] * 8
    close_prices = [110.0] * 20 + [104.0] + [106.0] * 8
    volumes = [1000.0] * 20 + [1000.0] + [400.0] * 8  # Low volume on all 8 bars

    df = pd.DataFrame({
        "Date": dates,
        "Open": open_prices,
        "High": high_prices,
        "Low": low_prices,
        "Close": close_prices,
        "Volume": volumes,
    })

    lps_events = detect_lps_candidates(df)
    # Must record exactly 1 LPS (the first one at bar 21), not 8 LPS events!
    assert len(lps_events) == 1
    assert lps_events[0].date == dates[21]

