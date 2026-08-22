"""Unit tests for RSI and momentum calculations using Wilder's smoothing."""

import pytest
import numpy as np
import pandas as pd

from wyckoff_screener.indicators.momentum import (
    DEFAULT_RSI_PERIOD,
    RSI_BULLISH_BAND_LOWER,
    RSI_BULLISH_BAND_UPPER,
    rsi,
)


def test_rsi_hand_calculated_wilder():
    """Verify RSI calculation against step-by-step hand-computed Wilder's RMA values."""
    # 15 prices (14 deltas for initial period)
    # Gains: 9 gains of 2.0 -> sum = 18, avg_gain = 18/14
    # Losses: 5 losses of 1.0 -> sum = 5, avg_loss = 5/14
    # Initial RS = (18/14) / (5/14) = 18/5 = 3.6
    # Initial RSI (at index 14) = 100 - (100 / (1 + 3.6)) = 100 - (100/4.6) = 78.260870
    # 16th price = 116 (+3 delta, gain=3, loss=0)
    # Next avg_gain = ( (18/14)*13 + 3 ) / 14 = (16.71428571 + 3) / 14 = 19.71428571 / 14 = 1.40816327
    # Next avg_loss = ( (5/14)*13 + 0 ) / 14 = 4.64285714 / 14 = 0.33163265
    # Next RS = 1.40816327 / 0.33163265 = 4.24615385
    # Next RSI (at index 15) = 100 - (100 / 5.24615385) = 80.938416
    prices = [
        100.0, 102.0, 101.0, 103.0, 105.0,
        104.0, 106.0, 108.0, 107.0, 109.0,
        111.0, 110.0, 112.0, 114.0, 113.0,
        116.0
    ]
    df = pd.DataFrame({"Close": prices})

    res = rsi(df, period=14)

    # Initial 14 indices (0 to 13) should be NaN
    for i in range(14):
        assert np.isnan(res.iloc[i])

    # Index 14 (15th row)
    assert pytest.approx(res.iloc[14], rel=1e-5) == 78.260870

    # Index 15 (16th row)
    assert pytest.approx(res.iloc[15], rel=1e-5) == 80.938416


def test_rsi_all_gains():
    """Verify RSI is 100 when all price changes are positive."""
    prices = [10.0 + i for i in range(20)]
    df = pd.DataFrame({"Close": prices})
    res = rsi(df, period=14)
    assert pytest.approx(res.iloc[14], rel=1e-5) == 100.0
    assert pytest.approx(res.iloc[-1], rel=1e-5) == 100.0


def test_rsi_all_losses():
    """Verify RSI is 0 when all price changes are negative."""
    prices = [100.0 - i for i in range(20)]
    df = pd.DataFrame({"Close": prices})
    res = rsi(df, period=14)
    assert pytest.approx(res.iloc[14], rel=1e-5) == 0.0
    assert pytest.approx(res.iloc[-1], rel=1e-5) == 0.0


def test_rsi_constants():
    """Verify default RSI constants."""
    assert DEFAULT_RSI_PERIOD == 14
    assert RSI_BULLISH_BAND_LOWER == 55.0
    assert RSI_BULLISH_BAND_UPPER == 70.0


def test_rsi_invalid_inputs():
    """Verify error on missing column or invalid period."""
    df = pd.DataFrame({"Close": [10, 12, 11]})
    with pytest.raises(KeyError):
        rsi(df, column="Price")
    with pytest.raises(ValueError):
        rsi(df, period=0)
