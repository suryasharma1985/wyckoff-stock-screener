"""Unit tests for moving averages indicator calculations."""

import pytest
import numpy as np
import pandas as pd

from wyckoff_screener.indicators.moving_averages import (
    PERIOD_MA_50,
    PERIOD_MA_100,
    PERIOD_MA_150,
    PERIOD_MA_200,
    PERIOD_MA_30_WEEK,
    PERIOD_MA_40_WEEK,
    simple_moving_average,
    sma_50,
    sma_100,
    sma_150,
    sma_200,
    sma_30_week,
    sma_40_week,
    weekly_simple_moving_average,
)


def test_simple_moving_average_hand_calculated():
    """Verify SMA calculation against hand-computed values."""
    prices = [10.0, 20.0, 30.0, 40.0, 50.0]
    df = pd.DataFrame({"Close": prices})

    # Period 3 SMA:
    # idx 0: NaN
    # idx 1: NaN
    # idx 2: (10+20+30)/3 = 20.0
    # idx 3: (20+30+40)/3 = 30.0
    # idx 4: (30+40+50)/3 = 40.0
    res = simple_moving_average(df, column="Close", period=3)

    assert np.isnan(res.iloc[0])
    assert np.isnan(res.iloc[1])
    assert pytest.approx(res.iloc[2], rel=1e-5) == 20.0
    assert pytest.approx(res.iloc[3], rel=1e-5) == 30.0
    assert pytest.approx(res.iloc[4], rel=1e-5) == 40.0


def test_sma_convenience_functions():
    """Verify sma_50, 100, 150, 200 convenience functions call correct periods."""
    df = pd.DataFrame({"Close": np.arange(1.0, 250.0)})

    res_50 = sma_50(df)
    res_100 = sma_100(df)
    res_150 = sma_150(df)
    res_200 = sma_200(df)

    assert len(res_50.dropna()) == 249 - 50 + 1
    assert len(res_100.dropna()) == 249 - 100 + 1
    assert len(res_150.dropna()) == 249 - 150 + 1
    assert len(res_200.dropna()) == 249 - 200 + 1

    # Hand check last value of 50-period SMA: mean of 200..249
    expected_last_50 = np.mean(np.arange(200.0, 250.0))
    assert pytest.approx(res_50.iloc[-1], rel=1e-5) == expected_last_50


def test_weekly_simple_moving_average():
    """Verify weekly resampled SMA with exact hand-calculated Friday closes."""
    # Create 3 weeks of daily trading days (Mon-Fri)
    # Week 1: 2024-01-01 to 2024-01-05 (Fri close = 100)
    # Week 2: 2024-01-08 to 2024-01-12 (Fri close = 120)
    # Week 3: 2024-01-15 to 2024-01-19 (Fri close = 140)
    dates = pd.date_range("2024-01-01", periods=15, freq="B")  # 3 business weeks
    closes = [
        # Week 1
        90, 92, 95, 98, 100,
        # Week 2
        105, 108, 112, 115, 120,
        # Week 3
        125, 128, 132, 135, 140,
    ]
    df = pd.DataFrame({"Date": dates, "Close": closes})

    # Weekly 2-week SMA:
    # Week 1 Friday (100): NaN
    # Week 2 Friday (120): (100 + 120)/2 = 110.0
    # Week 3 Friday (140): (120 + 140)/2 = 130.0
    weekly_ma = weekly_simple_moving_average(df, period_weeks=2, align_to_daily=False)
    assert len(weekly_ma) == 3
    assert np.isnan(weekly_ma.iloc[0])
    assert pytest.approx(weekly_ma.iloc[1], rel=1e-5) == 110.0
    assert pytest.approx(weekly_ma.iloc[2], rel=1e-5) == 130.0

    # Test daily aligned output
    daily_aligned = weekly_simple_moving_average(df, period_weeks=2, align_to_daily=True)
    assert len(daily_aligned) == 15
    # The last day of week 3 (index 14) should have the week 3 MA of 130.0
    assert pytest.approx(daily_aligned.iloc[-1], rel=1e-5) == 130.0


def test_sma_errors_on_invalid_inputs():
    """Verify KeyError on missing column and ValueError on invalid period."""
    df = pd.DataFrame({"Close": [10.0, 20.0, 30.0]})

    with pytest.raises(KeyError, match="not found"):
        simple_moving_average(df, column="NonExistent")

    with pytest.raises(ValueError, match="positive integer"):
        simple_moving_average(df, period=0)
