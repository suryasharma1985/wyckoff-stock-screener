"""Unit tests for volatility indicators (True Range, ATR, Bollinger Band Width, ATR Contraction)."""

import pytest
import numpy as np
import pandas as pd

from wyckoff_screener.indicators.volatility import (
    DEFAULT_ATR_LONG_PERIOD,
    DEFAULT_ATR_PERIOD,
    DEFAULT_ATR_SHORT_PERIOD,
    DEFAULT_BB_PERIOD,
    DEFAULT_BB_STD,
    atr_contraction_ratio,
    average_true_range,
    bollinger_band_width,
    true_range,
)


def test_true_range_hand_calculated():
    """Verify True Range on bars with gaps and normal ranges."""
    # Bar 0: H=105, L=95, C=100 -> TR = 105 - 95 = 10
    # Bar 1: H=110, L=102, C=108 -> TR = max(110-102=8, |110-100|=10, |102-100|=2) = 10
    # Bar 2 (gap down): H=104, L=90, C=92 -> TR = max(104-90=14, |104-108|=4, |90-108|=18) = 18
    # Bar 3 (gap up): H=120, L=115, C=118 -> TR = max(120-115=5, |120-92|=28, |115-92|=23) = 28
    df = pd.DataFrame({
        "High": [105.0, 110.0, 104.0, 120.0],
        "Low": [95.0, 102.0, 90.0, 115.0],
        "Close": [100.0, 108.0, 92.0, 118.0],
    })

    tr = true_range(df)
    expected = [10.0, 10.0, 18.0, 28.0]
    for actual, exp in zip(tr, expected):
        assert pytest.approx(actual, rel=1e-5) == exp


def test_average_true_range_rolling_mean():
    """Verify rolling average true range over 3 periods."""
    df = pd.DataFrame({
        "High": [105.0, 110.0, 104.0, 120.0],
        "Low": [95.0, 102.0, 90.0, 115.0],
        "Close": [100.0, 108.0, 92.0, 118.0],
    })
    # TR: [10, 10, 18, 28]
    # Period 3 ATR:
    # idx 0: NaN
    # idx 1: NaN
    # idx 2: (10 + 10 + 18)/3 = 38/3 = 12.66667
    # idx 3: (10 + 18 + 28)/3 = 56/3 = 18.66667
    atr = average_true_range(df, period=3, use_wilder=False)
    assert np.isnan(atr.iloc[0])
    assert np.isnan(atr.iloc[1])
    assert pytest.approx(atr.iloc[2], rel=1e-5) == 38.0 / 3.0
    assert pytest.approx(atr.iloc[3], rel=1e-5) == 56.0 / 3.0


def test_bollinger_band_width():
    """Verify Bollinger Band Width = (2 * std * 2) / SMA."""
    # 5 constant values: std = 0, BBW = 0
    df_flat = pd.DataFrame({"Close": [100.0, 100.0, 100.0, 100.0, 100.0]})
    bbw_flat = bollinger_band_width(df_flat, period=5, num_std=2.0)
    assert pytest.approx(bbw_flat.iloc[-1], abs=1e-6) == 0.0

    # Values [90, 100, 110]: mean = 100, ddof=0 std = sqrt((( -10^2 + 0 + 10^2 )/3)) = sqrt(200/3) = 8.1649658
    # BBW = (2 * 2.0 * 8.1649658) / 100 = 0.3265986
    df_var = pd.DataFrame({"Close": [90.0, 100.0, 110.0]})
    bbw = bollinger_band_width(df_var, period=3, num_std=2.0)
    assert pytest.approx(bbw.iloc[-1], rel=1e-5) == (4.0 * np.sqrt(200.0 / 3.0)) / 100.0


def test_atr_contraction_ratio():
    """Verify short ATR / long ATR ratio flags volatility compression."""
    # Synthetic data with 25 wide TRs (TR = 20) followed by 25 narrow TRs (TR = 5)
    highs = [120.0] * 25 + [105.0] * 25
    lows = [100.0] * 25 + [100.0] * 25
    closes = [110.0] * 25 + [102.0] * 25
    df = pd.DataFrame({"High": highs, "Low": lows, "Close": closes})

    # Short period = 10, Long period = 50
    ratio = atr_contraction_ratio(df, short_period=10, long_period=50)

    # At the end of the series, short ATR is ~5, long ATR is (25*20 + 25*5)/50 = 625/50 = 12.5
    # Ratio = 5.0 / 12.5 = 0.40 (strong contraction)
    assert pytest.approx(ratio.iloc[-1], rel=1e-2) == 5.0 / 12.5
    assert ratio.iloc[-1] < 1.0


def test_volatility_errors():
    """Verify parameter validations."""
    df = pd.DataFrame({"High": [10], "Low": [5], "Close": [8]})
    with pytest.raises(ValueError, match="positive integer"):
        average_true_range(df, period=0)
    with pytest.raises(ValueError, match="strictly less than"):
        atr_contraction_ratio(df, short_period=50, long_period=14)
