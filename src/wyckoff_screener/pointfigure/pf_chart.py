"""Point & Figure (P&F) chart construction and horizontal price counting.

Implements Bruce Fraser's P&F method per AGENTS.md:
1. Algorithmic box construction from OHLC High/Low data.
2. Standard 3-box reversal (configurable).
3. Horizontal count-row price objective formulation:
   Price Objective = Count-Row Price + (Columns * Box Size * Reversal N)
"""

from dataclasses import dataclass
from typing import Any, Final, Optional
import numpy as np
import pandas as pd

DEFAULT_BOX_PCT: Final[float] = 0.01  # Default 1% dynamic box size if fixed box_size is None
DEFAULT_REVERSAL: Final[int] = 3
DEFAULT_HIGH_COL: Final[str] = "High"
DEFAULT_LOW_COL: Final[str] = "Low"
DEFAULT_CLOSE_COL: Final[str] = "Close"
DEFAULT_DATE_COL: Final[str] = "Date"


@dataclass(frozen=True)
class PFColumn:
    """Represents a single vertical column in a Point & Figure chart."""

    direction: str  # 'X' for up, 'O' for down
    boxes: list[float]  # Ascending price levels for X, descending for O
    start_date: Any
    end_date: Any
    column_index: int

    @property
    def top(self) -> float:
        """Highest box price in this column."""
        return max(self.boxes) if self.boxes else 0.0

    @property
    def bottom(self) -> float:
        """Lowest box price in this column."""
        return min(self.boxes) if self.boxes else 0.0

    @property
    def num_boxes(self) -> int:
        """Number of boxes in this column."""
        return len(self.boxes)


@dataclass(frozen=True)
class PFPriceObjective:
    """Represents a Bruce Fraser Point & Figure horizontal count price objective."""

    count_row_price: float
    num_columns: int
    box_size: float
    reversal: int
    direction: str  # 'bullish' or 'bearish'
    price_objective: float
    formula: str
    columns_counted: list[int]
    supporting_note: str
    used_fallback_count: bool = False
    stale_anchor: bool = False

    def to_dict(self) -> dict[str, Any]:
        """Convert price objective to dict."""
        return {
            "count_row_price": self.count_row_price,
            "num_columns": self.num_columns,
            "box_size": self.box_size,
            "reversal": self.reversal,
            "direction": self.direction,
            "price_objective": round(self.price_objective, 2),
            "formula": self.formula,
            "columns_counted": self.columns_counted,
            "supporting_note": self.supporting_note,
            "used_fallback_count": self.used_fallback_count,
            "stale_anchor": self.stale_anchor,
        }


def calculate_dynamic_box_size(price: float, box_pct: float = DEFAULT_BOX_PCT) -> float:
    """Calculate a clean, rounded dynamic box size based on percentage of price.

    Note on Design Decision:
        A percentage-of-price method (default ~1%) rounded to clean currency increments
        (e.g., 0.50, 1.0, 2.0, 5.0) is used rather than fixed traditional static lookup tables
        to scale dynamically across Indian equities trading from Rs 50 to Rs 50,000+.

    Args:
        price: Reference price level.
        box_pct: Target box size percentage (default 0.01 / 1%).

    Returns:
        float: Rounded box size.
    """
    raw_box = price * box_pct
    if raw_box < 0.5:
        return 0.25
    if raw_box < 1.5:
        return 1.0
    if raw_box < 3.0:
        return 2.0
    if raw_box < 7.5:
        return 5.0
    if raw_box < 15.0:
        return 10.0
    if raw_box < 35.0:
        return 20.0
    return round(raw_box / 10.0) * 10.0


def build_point_and_figure_chart(
    df: pd.DataFrame,
    box_size: Optional[float] = None,
    box_pct: float = DEFAULT_BOX_PCT,
    reversal: int = DEFAULT_REVERSAL,
    high_col: str = DEFAULT_HIGH_COL,
    low_col: str = DEFAULT_LOW_COL,
    close_col: str = DEFAULT_CLOSE_COL,
    date_col: str = DEFAULT_DATE_COL,
) -> tuple[list[PFColumn], float]:
    """Construct an algorithmic Point & Figure chart from OHLC data using High/Low per bar.

    Implements true box-construction per Bruce Fraser / Wyckoff Method:
    - In an X (up) column: tests for continuation up via bar High. If not, tests for N-box reversal down via bar Low.
    - In an O (down) column: tests for continuation down via bar Low. If not, tests for N-box reversal up via bar High.

    Args:
        df: OHLCV DataFrame.
        box_size: Fixed box size in currency units. If None, dynamically calculated from initial close.
        box_pct: Percentage used for dynamic box calculation if box_size is None (default 0.01).
        reversal: Number of boxes required for a column reversal (default 3).
        high_col: High price column name.
        low_col: Low price column name.
        close_col: Close price column name.
        date_col: Date column name.

    Returns:
        tuple[list[PFColumn], float]: (list of P&F columns, box_size used).
    """
    if df.empty:
        return [], 0.0

    for col in (high_col, low_col, close_col):
        if col not in df.columns:
            raise KeyError(f"Required column '{col}' not found in DataFrame.")

    # Determine box size
    if box_size is None or box_size <= 0:
        first_price = float(df[close_col].iloc[0])
        effective_box_size = calculate_dynamic_box_size(first_price, box_pct=box_pct)
    else:
        effective_box_size = float(box_size)

    columns: list[PFColumn] = []

    # Initial column setup from the first bar
    initial_high = float(df[high_col].iloc[0])
    initial_low = float(df[low_col].iloc[0])
    initial_date = df[date_col].iloc[0] if date_col in df.columns else 0

    # Start with base box level aligned to box_size
    base_box = np.floor(initial_low / effective_box_size) * effective_box_size
    current_direction = "X"
    current_boxes = [base_box]

    # Fill initial boxes up to High
    num_initial_boxes = int(np.floor((initial_high - base_box) / effective_box_size))
    for step in range(1, num_initial_boxes + 1):
        current_boxes.append(base_box + step * effective_box_size)

    current_start_date = initial_date
    current_end_date = initial_date

    for i in range(1, len(df)):
        h = float(df[high_col].iloc[i])
        l = float(df[low_col].iloc[i])
        d = df[date_col].iloc[i] if date_col in df.columns else i

        if current_direction == "X":
            top_box = current_boxes[-1]
            # 1. Check for continuation up
            new_top_boxes = int(np.floor((h - top_box) / effective_box_size))
            if new_top_boxes > 0:
                for step in range(1, new_top_boxes + 1):
                    current_boxes.append(top_box + step * effective_box_size)
                current_end_date = d
            else:
                # 2. Check for 3-box reversal down
                reversal_threshold = top_box - (reversal * effective_box_size)
                if l <= reversal_threshold:
                    # Save finished X column
                    columns.append(
                        PFColumn(
                            direction="X",
                            boxes=list(current_boxes),
                            start_date=current_start_date,
                            end_date=current_end_date,
                            column_index=len(columns),
                        )
                    )
                    # Start new O column: begins 1 box below previous X top
                    current_direction = "O"
                    current_start_date = d
                    current_end_date = d
                    first_o_box = top_box - effective_box_size
                    num_o_boxes = int(np.floor((first_o_box - l) / effective_box_size)) + 1
                    current_boxes = [first_o_box - step * effective_box_size for step in range(num_o_boxes)]

        elif current_direction == "O":
            bottom_box = current_boxes[-1]
            # 1. Check for continuation down
            new_bottom_boxes = int(np.floor((bottom_box - l) / effective_box_size))
            if new_bottom_boxes > 0:
                for step in range(1, new_bottom_boxes + 1):
                    current_boxes.append(bottom_box - step * effective_box_size)
                current_end_date = d
            else:
                # 2. Check for 3-box reversal up
                reversal_threshold = bottom_box + (reversal * effective_box_size)
                if h >= reversal_threshold:
                    # Save finished O column
                    columns.append(
                        PFColumn(
                            direction="O",
                            boxes=list(current_boxes),
                            start_date=current_start_date,
                            end_date=current_end_date,
                            column_index=len(columns),
                        )
                    )
                    # Start new X column: begins 1 box above previous O bottom
                    current_direction = "X"
                    current_start_date = d
                    current_end_date = d
                    first_x_box = bottom_box + effective_box_size
                    num_x_boxes = int(np.floor((h - first_x_box) / effective_box_size)) + 1
                    current_boxes = [first_x_box + step * effective_box_size for step in range(num_x_boxes)]

    # Add final in-progress column
    if current_boxes:
        columns.append(
            PFColumn(
                direction=current_direction,
                boxes=list(current_boxes),
                start_date=current_start_date,
                end_date=current_end_date,
                column_index=len(columns),
            )
        )

    return columns, effective_box_size


def count_price_objective(
    pf_columns: list[PFColumn],
    count_row_price: float,
    box_size: float,
    reversal: int = DEFAULT_REVERSAL,
    direction: str = "bullish",
    start_col_idx: Optional[int] = None,
    end_col_idx: Optional[int] = None,
    stale_anchor: bool = False,
    stale_anchor_warning: str = "",
) -> PFPriceObjective:
    """Calculate Point & Figure horizontal count price objective per Bruce Fraser method.

    Formula (AGENTS.md):
        Bullish Price Objective = Count-Row Price + (Columns * Box Size * Reversal)
        Bearish Price Objective = Count-Row Price - (Columns * Box Size * Reversal)

    Args:
        pf_columns: List of constructed P&F columns.
        count_row_price: The horizontal count-row price level (typically at/near LPS or Spring level).
        box_size: Box size in currency units.
        reversal: Reversal box count N (default 3).
        direction: 'bullish' for upside target or 'bearish' for downside target.
        start_col_idx: Optional start column index for the trading range count.
        end_col_idx: Optional end column index for the trading range count.
        stale_anchor: True if the count row anchor event is older than the staleness threshold.
        stale_anchor_warning: Optional warning text to prepend if count row is stale.

    Returns:
        PFPriceObjective: Struct containing target price, counted columns, and full mathematical derivation.
    """
    if not pf_columns:
        raise ValueError("Cannot compute price objective on empty P&F columns.")
    if box_size <= 0:
        raise ValueError(f"box_size must be positive, got {box_size}.")
    if reversal <= 0:
        raise ValueError(f"reversal must be positive, got {reversal}.")

    # Identify columns spanning the count row
    start_idx = 0 if start_col_idx is None else max(0, start_col_idx)
    end_idx = len(pf_columns) - 1 if end_col_idx is None else min(len(pf_columns) - 1, end_col_idx)

    counted_indices: list[int] = []
    for col in pf_columns[start_idx : end_idx + 1]:
        # Check if this column touches/contains the count row (within half a box size tolerance)
        col_min = min(col.boxes)
        col_max = max(col.boxes)
        if col_min - (box_size * 0.5) <= count_row_price <= col_max + (box_size * 0.5):
            counted_indices.append(col.column_index)

    num_columns = len(counted_indices)
    used_fallback_count = False
    warning_prefix = stale_anchor_warning

    if num_columns == 0:
        # Fallback: count total columns in range span if exact row match is empty
        counted_indices = [c.column_index for c in pf_columns[start_idx : end_idx + 1]]
        num_columns = len(counted_indices)
        used_fallback_count = True
        fallback_msg = (
            "WARNING: no column exactly touched the count row — "
            "falling back to counting all columns in the specified range, "
            "which may overstate/understate the true horizontal count. "
        )
        warning_prefix = f"{stale_anchor_warning}{fallback_msg}" if stale_anchor_warning else fallback_msg

    horizontal_count_units = num_columns * box_size * reversal

    if direction.lower() == "bullish":
        target_price = count_row_price + horizontal_count_units
        formula_str = (
            f"Price Objective = {count_row_price:.2f} + ({num_columns} cols * {box_size:.2f} box * {reversal}R) = {target_price:.2f}"
        )
    else:
        target_price = count_row_price - horizontal_count_units
        formula_str = (
            f"Price Objective = {count_row_price:.2f} - ({num_columns} cols * {box_size:.2f} box * {reversal}R) = {target_price:.2f}"
        )

    note = (
        f"{warning_prefix}Bruce Fraser P&F Horizontal Count: {num_columns} columns counted across row {count_row_price:.2f} "
        f"(columns {counted_indices[0]}..{counted_indices[-1]}). "
        f"Projected {direction} target: {target_price:.2f} ({formula_str})"
    )

    return PFPriceObjective(
        count_row_price=count_row_price,
        num_columns=num_columns,
        box_size=box_size,
        reversal=reversal,
        direction=direction,
        price_objective=target_price,
        formula=formula_str,
        columns_counted=counted_indices,
        supporting_note=note,
        used_fallback_count=used_fallback_count,
        stale_anchor=stale_anchor,
    )
