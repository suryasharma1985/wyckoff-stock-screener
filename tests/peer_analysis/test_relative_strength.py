"""Unit tests for Bogomazov comparative relative strength and low-to-low slope analysis."""

import pytest
import pandas as pd

from wyckoff_screener.peer_analysis.relative_strength import (
    compare_low_to_low_slope,
    rank_peer_relative_strength,
    synchronize_to_reference_date,
)


def test_synchronize_to_reference_date():
    """Verify price series normalization to percentage change from reference date."""
    dates = pd.date_range("2024-01-01", periods=3)
    p_df = pd.DataFrame({"Date": dates, "Close": [100.0, 110.0, 120.0]})  # +0%, +10%, +20%
    q_df = pd.DataFrame({"Date": dates, "Close": [50.0, 45.0, 40.0]})    # +0%, -10%, -20%

    synced = synchronize_to_reference_date(p_df, q_df, reference_date="2024-01-01")

    assert len(synced) == 3
    assert synced["primary_pct"].iloc[0] == 0.0
    assert synced["primary_pct"].iloc[1] == 10.0
    assert synced["primary_pct"].iloc[2] == 20.0

    assert synced["peer_pct"].iloc[0] == 0.0
    assert synced["peer_pct"].iloc[1] == -10.0
    assert synced["peer_pct"].iloc[2] == -20.0


def test_compare_low_to_low_slope_and_ranking_with_failed_peers():
    """Verify low-to-low slope calculation and ranking across primary and peers including error tracking."""
    dates = pd.date_range("2024-01-01", periods=10)

    # Primary: Low1 = 100 on 2024-01-02, Low2 = 125 on 2024-01-07 (+25% gain)
    primary_lows = [105.0, 100.0, 110.0, 115.0, 120.0, 122.0, 125.0, 130.0, 132.0, 135.0]
    primary_df = pd.DataFrame({"Date": dates, "Close": primary_lows, "Low": primary_lows})

    # Peer A (Stronger): Low1 = 100, Low2 = 150 (+50% gain)
    peer_a_lows = [105.0, 100.0, 115.0, 125.0, 135.0, 140.0, 150.0, 160.0, 165.0, 170.0]
    peer_a_df = pd.DataFrame({"Date": dates, "Close": peer_a_lows, "Low": peer_a_lows})

    # Peer B (Weaker): Low1 = 100, Low2 = 80 (-20% loss / Lower Low)
    peer_b_lows = [105.0, 100.0, 95.0, 90.0, 88.0, 85.0, 80.0, 78.0, 75.0, 70.0]
    peer_b_df = pd.DataFrame({"Date": dates, "Close": peer_b_lows, "Low": peer_b_lows})

    # Peer C (Missing Date / Error): Short DataFrame
    peer_c_df = pd.DataFrame({"Date": dates[:3], "Close": [100.0, 100.0, 100.0], "Low": [100.0, 100.0, 100.0]})

    # 1. Test individual slope
    res_primary = compare_low_to_low_slope(primary_df, first_low_date=dates[1], second_low_date=dates[6], symbol="PRIMARY", validate_swing=False)
    assert res_primary.price_change_pct == 25.0
    assert res_primary.is_higher_low is True
    assert res_primary.slope_per_bar == (125.0 - 100.0) / 5.0

    # 2. Test ranking with error reporting tuple
    peer_dict = {"PEER_A": peer_a_df, "PEER_B": peer_b_df, "PEER_C": peer_c_df}
    ranked, failed = rank_peer_relative_strength(
        primary_symbol="PRIMARY",
        primary_df=primary_df,
        peer_dict=peer_dict,
        first_low_date=dates[1],
        second_low_date=dates[6],
        validate_swing=False,
    )

    assert len(ranked) == 3
    assert len(failed) == 1
    assert failed[0][0] == "PEER_C"
    assert "not found in DataFrame" in failed[0][1]

    # Rank 1: PEER_A (+50%)
    assert ranked[0].symbol == "PEER_A"
    assert ranked[0].relative_strength_rank == 1
    assert ranked[0].price_change_pct == 50.0

    # Rank 2: PRIMARY (+25%)
    assert ranked[1].symbol == "PRIMARY"
    assert ranked[1].relative_strength_rank == 2
    assert ranked[1].price_change_pct == 25.0

    # Rank 3: PEER_B (-20%)
    assert ranked[2].symbol == "PEER_B"
    assert ranked[2].relative_strength_rank == 3
    assert ranked[2].price_change_pct == -20.0


def test_compare_low_to_low_slope_swing_validation():
    """Verify validate_swing=True raises ValueError on non-swing lows."""
    dates = pd.date_range("2024-01-01", periods=10)
    # Monotonically increasing lows: index 1 and 6 are NOT swing lows (they don't have higher lows on both sides)
    lows = [100.0 + i * 5 for i in range(10)]
    df = pd.DataFrame({"Date": dates, "Close": lows, "Low": lows})

    with pytest.raises(ValueError, match="Swing low validation failed"):
        compare_low_to_low_slope(df, first_low_date=dates[1], second_low_date=dates[6], symbol="TEST", validate_swing=True, swing_window=1)
