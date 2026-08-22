"""Unit tests for Point & Figure chart box construction and Bruce Fraser price objectives."""

import pytest
import pandas as pd

from wyckoff_screener.pointfigure.pf_chart import (
    build_point_and_figure_chart,
    calculate_dynamic_box_size,
    count_price_objective,
)


def test_pf_box_construction_hand_calculated():
    """Verify P&F column construction and 3-box reversal against step-by-step hand calculation."""
    # Hand-built OHLC sequence with box_size = 1.0, reversal = 3:
    # Bar 0 (2024-01-01): H=10.5, L=10.0 -> X column: [10.0]
    # Bar 1 (2024-01-02): H=13.2, L=10.8 -> X column up: [10.0, 11.0, 12.0, 13.0]
    # Bar 2 (2024-01-03): H=13.0, L=11.5 -> Inside bar (11.5 > 13 - 3 = 10, no reversal)
    # Bar 3 (2024-01-04): H=12.0, L=9.8  -> Reversal down (9.8 <= 10.0)! Col 0 ends X[10..13], Col 1 starts O[12.0, 11.0, 10.0]
    # Bar 4 (2024-01-05): H=13.5, L=10.2 -> Reversal up (13.5 >= 10 + 3 = 13.0)! Col 1 ends O[12..10], Col 2 starts X[11.0, 12.0, 13.0]
    dates = pd.date_range("2024-01-01", periods=5)
    df = pd.DataFrame({
        "Date": dates,
        "Open": [10.2, 11.0, 12.5, 11.8, 10.5],
        "High": [10.5, 13.2, 13.0, 12.0, 13.5],
        "Low": [10.0, 10.8, 11.5, 9.8, 10.2],
        "Close": [10.4, 13.0, 12.0, 10.0, 13.2],
    })

    columns, box_size = build_point_and_figure_chart(df, box_size=1.0, reversal=3)

    assert box_size == 1.0
    assert len(columns) == 3

    # Column 0: X column up [10, 11, 12, 13]
    col0 = columns[0]
    assert col0.direction == "X"
    assert col0.boxes == [10.0, 11.0, 12.0, 13.0]
    assert col0.top == 13.0
    assert col0.bottom == 10.0

    # Column 1: O column down [12, 11, 10]
    col1 = columns[1]
    assert col1.direction == "O"
    assert col1.boxes == [12.0, 11.0, 10.0]
    assert col1.top == 12.0
    assert col1.bottom == 10.0

    # Column 2: X column up [11, 12, 13]
    col2 = columns[2]
    assert col2.direction == "X"
    assert col2.boxes == [11.0, 12.0, 13.0]
    assert col2.top == 13.0
    assert col2.bottom == 11.0


def test_multi_box_continuation_up():
    """Verify multi-box continuation up within an existing X column."""
    dates = pd.date_range("2024-01-01", periods=2)
    df = pd.DataFrame({
        "Date": dates,
        "Open": [10.0, 11.0],
        "High": [10.5, 16.5],
        "Low": [10.0, 10.5],
        "Close": [10.2, 16.0],
    })
    columns, box_size = build_point_and_figure_chart(df, box_size=1.0, reversal=3)

    assert len(columns) == 1
    assert columns[0].direction == "X"
    assert columns[0].boxes == [10.0, 11.0, 12.0, 13.0, 14.0, 15.0, 16.0]
    assert columns[0].top == 16.0


def test_x_to_o_reversal():
    """Verify 3-box reversal from X column to O column."""
    dates = pd.date_range("2024-01-01", periods=2)
    df = pd.DataFrame({
        "Date": dates,
        "Open": [20.0, 19.0],
        "High": [20.5, 20.0],
        "Low": [20.0, 16.8],  # Drop of 3.2 from 20.0 -> reverses down
        "Close": [20.2, 17.0],
    })
    columns, _ = build_point_and_figure_chart(df, box_size=1.0, reversal=3)

    assert len(columns) == 2
    assert columns[0].direction == "X"
    assert columns[0].boxes == [20.0]
    assert columns[1].direction == "O"
    assert columns[1].boxes == [19.0, 18.0, 17.0]
    assert columns[1].top == 19.0
    assert columns[1].bottom == 17.0


def test_o_to_x_reversal():
    """Verify 3-box reversal from O column to X column."""
    dates = pd.date_range("2024-01-01", periods=3)
    df = pd.DataFrame({
        "Date": dates,
        "Open": [20.0, 19.0, 17.0],
        "High": [20.5, 20.0, 20.2],  # Rise of 3.2 from 17.0 -> reverses up
        "Low": [20.0, 16.8, 17.0],
        "Close": [20.2, 17.0, 20.0],
    })
    columns, _ = build_point_and_figure_chart(df, box_size=1.0, reversal=3)

    assert len(columns) == 3
    assert columns[0].direction == "X"
    assert columns[1].direction == "O"
    assert columns[2].direction == "X"
    assert columns[2].boxes == [18.0, 19.0, 20.0]


def test_continuation_down_move():
    """Verify multi-box continuation down within an existing O column."""
    dates = pd.date_range("2024-01-01", periods=3)
    df = pd.DataFrame({
        "Date": dates,
        "Open": [20.0, 19.0, 16.5],
        "High": [20.5, 20.0, 17.0],
        "Low": [20.0, 16.8, 12.2],  # Continuation down to 12.0
        "Close": [20.2, 17.0, 12.5],
    })
    columns, _ = build_point_and_figure_chart(df, box_size=1.0, reversal=3)

    assert len(columns) == 2
    assert columns[1].direction == "O"
    assert columns[1].boxes == [19.0, 18.0, 17.0, 16.0, 15.0, 14.0, 13.0]
    assert columns[1].bottom == 13.0


def test_count_price_objective_exact_touch_and_fallback_warning():
    """Verify exact touch vs fallback warning branches in count_price_objective."""
    dates = pd.date_range("2024-01-01", periods=5)
    df = pd.DataFrame({
        "Date": dates,
        "High": [10.5, 13.2, 13.0, 12.0, 13.5],
        "Low": [10.0, 10.8, 11.5, 9.8, 10.2],
        "Close": [10.4, 13.0, 12.0, 10.0, 13.2],
    })
    columns, _ = build_point_and_figure_chart(df, box_size=1.0, reversal=3)

    # 1. Exact touch branch: count row at 11.0
    obj_exact = count_price_objective(columns, count_row_price=11.0, box_size=1.0, reversal=3, direction="bullish")
    assert obj_exact.used_fallback_count is False
    assert "WARNING" not in obj_exact.supporting_note
    assert obj_exact.num_columns == 3
    assert obj_exact.price_objective == 20.0

    # 2. Fallback branch: count row at 99.0 (outside any column range)
    obj_fallback = count_price_objective(columns, count_row_price=99.0, box_size=1.0, reversal=3, direction="bullish")
    assert obj_fallback.used_fallback_count is True
    assert "WARNING: no column exactly touched the count row" in obj_fallback.supporting_note
    assert obj_fallback.num_columns == 3  # Falls back to all 3 columns in the range
    assert obj_fallback.price_objective == 99.0 + (3 * 1.0 * 3) == 108.0


def test_calculate_dynamic_box_size():
    """Verify dynamic box size scaling."""
    assert calculate_dynamic_box_size(100.0, box_pct=0.01) == 1.0
    assert calculate_dynamic_box_size(500.0, box_pct=0.01) == 5.0
    assert calculate_dynamic_box_size(25.0, box_pct=0.01) == 0.25
