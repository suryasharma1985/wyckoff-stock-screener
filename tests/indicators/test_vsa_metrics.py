"""Unit tests for Volume Spread Analysis (VSA) metrics per AGENTS.md."""

import pytest
import numpy as np
import pandas as pd

from wyckoff_screener.indicators.vsa_metrics import (
    CLOSE_POS_HIGH,
    CLOSE_POS_LOW,
    SPREAD_RATIO_AVG,
    SPREAD_RATIO_WIDE,
    VOL_RATIO_AVG,
    VOL_RATIO_HIGH,
    VOL_RATIO_LOW,
    VOL_RATIO_VERY_HIGH,
    classify_close_position,
    classify_spread_ratio,
    classify_volume_ratio,
    close_position,
    spread_ratio,
    volume_ratio,
)


def test_volume_ratio_hand_calculated():
    """Verify volume_ratio = bar volume / rolling 20-period average volume."""
    # 20 bars with volume 1000, 21st bar with volume 4200 (SC climactic volume)
    volumes = [1000.0] * 20 + [4200.0]
    df = pd.DataFrame({"Volume": volumes})

    vr = volume_ratio(df, period=20)

    # 20th bar (index 19): avg = 1000, ratio = 1000/1000 = 1.0
    assert pytest.approx(vr.iloc[19], rel=1e-5) == 1.0
    assert classify_volume_ratio(vr.iloc[19]) == "Average"

    # 21st bar (index 20): rolling avg of bars 1..20 is (19*1000 + 4200)/20 = 23200/20 = 1160
    # ratio = 4200 / 1160 = 3.6206896
    expected_vr_21 = 4200.0 / ((19 * 1000.0 + 4200.0) / 20.0)
    assert pytest.approx(vr.iloc[20], rel=1e-5) == expected_vr_21
    assert classify_volume_ratio(vr.iloc[20]) == "Very High"


def test_spread_ratio_hand_calculated():
    """Verify spread_ratio = bar (high-low) / rolling 20-period average true range."""
    # 20 bars with constant range 10 (H=110, L=100, C=105)
    # 21st bar is wide spread: H=130, L=100, C=125 (spread = 30)
    highs = [110.0] * 20 + [130.0]
    lows = [100.0] * 20 + [100.0]
    closes = [105.0] * 20 + [125.0]
    df = pd.DataFrame({"High": highs, "Low": lows, "Close": closes})

    sr = spread_ratio(df, period=20)

    # 20th bar (index 19): spread = 10, ATR = 10 -> ratio = 1.0
    assert pytest.approx(sr.iloc[19], rel=1e-5) == 1.0
    assert classify_spread_ratio(sr.iloc[19]) == "Average"

    # 21st bar (index 20): spread = 30, prev_close = 105
    # TR_21 = max(130-100=30, |130-105|=25, |100-105|=5) = 30
    # ATR_20 at bar 21 = (19*10 + 30)/20 = 220/20 = 11.0
    # spread_ratio = 30 / 11.0 = 2.727272...
    assert pytest.approx(sr.iloc[20], rel=1e-5) == 30.0 / 11.0
    assert classify_spread_ratio(sr.iloc[20]) == "Wide"


def test_close_position_calculations_and_zero_range_safety():
    """Verify close position calculation, threshold classifications, and zero-range handling."""
    df = pd.DataFrame({
        "High": [100.0, 100.0, 100.0, 50.0],
        "Low": [0.0, 0.0, 0.0, 50.0],
        "Close": [85.0, 15.0, 50.0, 50.0],
    })

    cp = close_position(df)

    # Row 0: (85 - 0)/(100 - 0) = 0.85 -> Strong close (>0.7)
    assert pytest.approx(cp.iloc[0], rel=1e-5) == 0.85
    assert classify_close_position(cp.iloc[0]) == "Near High"

    # Row 1: (15 - 0)/(100 - 0) = 0.15 -> Weak close (<0.3)
    assert pytest.approx(cp.iloc[1], rel=1e-5) == 0.15
    assert classify_close_position(cp.iloc[1]) == "Near Low"

    # Row 2: (50 - 0)/(100 - 0) = 0.50 -> Mid-range close (0.3 - 0.7)
    assert pytest.approx(cp.iloc[2], rel=1e-5) == 0.50
    assert classify_close_position(cp.iloc[2]) == "Mid-Range"

    # Row 3: High == Low == 50.0 (Zero range bar) -> should safely return 0.5 without error
    assert pytest.approx(cp.iloc[3], rel=1e-5) == 0.50
    assert not np.isnan(cp.iloc[3])
    assert not np.isinf(cp.iloc[3])


def test_vsa_threshold_constants_match_agents_md():
    """Ensure defined constants match AGENTS.md quantitative thresholds exactly."""
    assert VOL_RATIO_VERY_HIGH == 2.0
    assert VOL_RATIO_HIGH == 1.5
    assert VOL_RATIO_AVG == 0.75
    assert VOL_RATIO_LOW == 0.4

    assert SPREAD_RATIO_WIDE == 1.5
    assert SPREAD_RATIO_AVG == 0.6

    assert CLOSE_POS_HIGH == 0.7
    assert CLOSE_POS_LOW == 0.3


def test_vsa_metrics_error_handling():
    """Verify KeyError when required columns are missing and ValueError on non-positive period."""
    df = pd.DataFrame({"High": [10.0], "Low": [5.0]})

    with pytest.raises(KeyError):
        volume_ratio(df)

    with pytest.raises(KeyError):
        spread_ratio(df)

    with pytest.raises(KeyError):
        close_position(df)

    with pytest.raises(ValueError):
        volume_ratio(pd.DataFrame({"Volume": [100.0]}), period=0)


def test_spread_ratio_explicitly_uses_simple_rolling_mean_atr():
    """Verify that spread_ratio strictly uses simple rolling mean ATR (not Wilder's RMA) as documented."""
    from wyckoff_screener.indicators.volatility import average_true_range

    # 25 bars with variable prices
    highs = [100.0 + i * 2.0 for i in range(25)]
    lows = [90.0 + i * 1.5 for i in range(25)]
    closes = [95.0 + i * 1.8 for i in range(25)]
    df = pd.DataFrame({"High": highs, "Low": lows, "Close": closes})

    sr = spread_ratio(df, period=20)
    sma_atr = average_true_range(df, period=20, use_wilder=False)
    wilder_atr = average_true_range(df, period=20, use_wilder=True)

    bar_spread = df["High"] - df["Low"]
    expected_sma_sr = bar_spread / sma_atr
    expected_wilder_sr = bar_spread / wilder_atr

    # Verify matching SMA ATR
    assert pytest.approx(sr.iloc[-1], rel=1e-6) == expected_sma_sr.iloc[-1]
    # Verify that SMA ATR and Wilder ATR differ on dynamic data, and sr did NOT use Wilder ATR
    assert abs(expected_sma_sr.iloc[-1] - expected_wilder_sr.iloc[-1]) > 1e-3
    assert pytest.approx(sr.iloc[-1], rel=1e-6) != expected_wilder_sr.iloc[-1]

