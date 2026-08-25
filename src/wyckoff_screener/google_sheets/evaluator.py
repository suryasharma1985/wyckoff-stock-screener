"""Trade Outcome Evaluation Engine for Google Sheets Validation System.

Evaluates trade outcomes against daily OHLC data with exact support for:
- Next-day Open (T+1) entry
- Target hit detection (High >= target_price)
- Stop hit detection (Low <= stop_price)
- Same-day target & stop ambiguity handling (CONSERVATIVE, TARGET_FIRST, STOP_FIRST, EXCLUDE)
- Maximum Favorable Excursion (MFE) and Maximum Adverse Excursion (MAE)
- Fixed horizon forward returns (5D, 10D, 20D, 30D, 60D)
- Realized R-multiples and holding duration.
"""

from dataclasses import dataclass, field
from typing import Any, Final, Optional
import numpy as np
import pandas as pd

DEFAULT_ROUND_TRIP_FRICTION_PCT: Final[float] = 0.40
DEFAULT_MAX_HOLDING_DAYS: Final[int] = 60


@dataclass
class TradeOutcome:
    """Detailed record of a signal's realized post-entry trade outcome."""

    signal_id: str
    symbol: str
    signal_date: str
    entry_date: Optional[str]
    entry_price: float
    stop_price: float
    target_price: float
    risk_per_share: float
    initial_risk_pct: float

    # Realized Exit
    exit_date: Optional[str] = None
    exit_price: Optional[float] = None
    exit_reason: str = "PENDING"  # TARGET_HIT, STOP_HIT, TIME_HORIZON, AMBIGUOUS_SAME_DAY, PENDING
    holding_days: int = 0
    gross_return_pct: float = 0.0
    net_return_pct: float = 0.0
    r_multiple: float = 0.0
    outcome: str = "PENDING"  # WIN, LOSS, BREAKEVEN, PENDING, EXCLUDED

    # Excursions
    mfe_pct: float = 0.0
    mae_pct: float = 0.0

    # Fixed Horizon Mark-to-Market Net Returns
    fwd_net_5d: Optional[float] = None
    fwd_net_10d: Optional[float] = None
    fwd_net_20d: Optional[float] = None
    fwd_net_30d: Optional[float] = None
    fwd_net_60d: Optional[float] = None

    # Flags
    target_hit: bool = False
    stop_hit: bool = False
    target_before_stop: bool = False
    stop_before_target: bool = False
    is_ambiguous_same_day: bool = False
    days_to_target: Optional[int] = None
    days_to_stop: Optional[int] = None

    def to_dict(self) -> dict[str, Any]:
        """Convert outcome to dictionary for tabular export."""
        return {
            "Signal_ID": self.signal_id,
            "Symbol": self.symbol,
            "Signal_Date": self.signal_date,
            "Entry_Date": self.entry_date,
            "Entry_Price": round(self.entry_price, 2),
            "Stop_Price": round(self.stop_price, 2),
            "Target_Price": round(self.target_price, 2),
            "Risk_Per_Share": round(self.risk_per_share, 2),
            "Initial_Risk_Pct": round(self.initial_risk_pct, 2),
            "Exit_Date": self.exit_date,
            "Exit_Price": round(self.exit_price, 2) if self.exit_price is not None else None,
            "Exit_Reason": self.exit_reason,
            "Holding_Days": self.holding_days,
            "Net_Return_Pct": round(self.net_return_pct, 2),
            "R_Multiple": round(self.r_multiple, 2),
            "Outcome": self.outcome,
            "MFE_Pct": round(self.mfe_pct, 2),
            "MAE_Pct": round(self.mae_pct, 2),
            "5D_Return": round(self.fwd_net_5d, 2) if self.fwd_net_5d is not None else None,
            "10D_Return": round(self.fwd_net_10d, 2) if self.fwd_net_10d is not None else None,
            "20D_Return": round(self.fwd_net_20d, 2) if self.fwd_net_20d is not None else None,
            "30D_Return": round(self.fwd_net_30d, 2) if self.fwd_net_30d is not None else None,
            "60D_Return": round(self.fwd_net_60d, 2) if self.fwd_net_60d is not None else None,
            "Target_Hit": self.target_hit,
            "Stop_Hit": self.stop_hit,
            "Target_Before_Stop": self.target_before_stop,
            "Stop_Before_Target": self.stop_before_target,
            "Ambiguous_Same_Day": self.is_ambiguous_same_day,
            "Days_To_Target": self.days_to_target,
            "Days_To_Stop": self.days_to_stop,
        }


def evaluate_trade_outcome(
    symbol: str,
    signal_date: str,
    post_signal_df: pd.DataFrame,
    entry_price: Optional[float] = None,
    stop_price: Optional[float] = None,
    target_price: Optional[float] = None,
    max_holding_days: int = DEFAULT_MAX_HOLDING_DAYS,
    ambiguity_handling: str = "CONSERVATIVE",
    friction_pct: float = DEFAULT_ROUND_TRIP_FRICTION_PCT,
    date_col: str = "Date",
    open_col: str = "Open",
    high_col: str = "High",
    low_col: str = "Low",
    close_col: str = "Close",
) -> TradeOutcome:
    """Evaluate post-signal price action against entry, target, and stop rules.

    Args:
        symbol: Stock ticker symbol.
        signal_date: Point-in-time date of signal generation (YYYY-MM-DD).
        post_signal_df: DataFrame containing price bars occurring STRICTLY AFTER signal date.
        entry_price: Entry price. If None, defaults to the Open of the first bar (T+1 Open).
        stop_price: Stop loss price. If None, defaults to entry_price * 0.95 (-5%).
        target_price: Profit target price. If None, defaults to entry_price * 1.15 (+15%).
        max_holding_days: Maximum trading days to hold before time-based exit.
        ambiguity_handling: "CONSERVATIVE", "TARGET_FIRST", "STOP_FIRST", "EXCLUDE".
        friction_pct: Percentage friction deducted for round-trip execution (default 0.40%).
        date_col: Date column name.
        open_col: Open price column name.
        high_col: High price column name.
        low_col: Low price column name.
        close_col: Close price column name.

    Returns:
        TradeOutcome object populated with realized trade metrics.
    """
    signal_id = f"{symbol}_{signal_date}"

    if post_signal_df.empty:
        # No future bars available yet (e.g. forward live signal)
        ep = entry_price or 0.0
        sp = stop_price or (ep * 0.95)
        tp = target_price or (ep * 1.15)
        risk = max(ep - sp, 0.01 * ep if ep > 0 else 1.0)
        return TradeOutcome(
            signal_id=signal_id,
            symbol=symbol,
            signal_date=signal_date,
            entry_date=None,
            entry_price=ep,
            stop_price=sp,
            target_price=tp,
            risk_per_share=risk,
            initial_risk_pct=(risk / ep * 100.0) if ep > 0 else 5.0,
            exit_reason="PENDING",
            outcome="PENDING",
        )

    bars = post_signal_df.copy().reset_index(drop=True)
    first_bar = bars.iloc[0]

    # Entry is T+1 Open by default
    actual_entry_price = float(entry_price) if entry_price is not None else float(first_bar[open_col])
    entry_date = str(first_bar[date_col])[:10]

    # Default stops and targets if omitted
    actual_stop_price = float(stop_price) if stop_price is not None else (actual_entry_price * 0.95)
    actual_target_price = float(target_price) if target_price is not None else (actual_entry_price * 1.15)

    risk_per_share = max(actual_entry_price - actual_stop_price, 0.001 * actual_entry_price)
    initial_risk_pct = (risk_per_share / actual_entry_price) * 100.0 if actual_entry_price > 0 else 5.0

    mfe = 0.0
    mae = 0.0

    target_hit = False
    stop_hit = False
    target_before_stop = False
    stop_before_target = False
    is_ambiguous = False

    exit_date = None
    exit_price = None
    exit_reason = "PENDING"
    exit_day_idx = None

    days_to_target = None
    days_to_stop = None

    # Track mark-to-market returns at horizons
    fwd_returns: dict[int, Optional[float]] = {5: None, 10: None, 20: None, 30: None, 60: None}

    eval_len = min(len(bars), max_holding_days)

    for i in range(eval_len):
        day_num = i + 1
        bar = bars.iloc[i]
        b_date = str(bar[date_col])[:10]
        b_high = float(bar[high_col])
        b_low = float(bar[low_col])
        b_close = float(bar[close_col])

        # Update excursions
        day_mfe = ((b_high - actual_entry_price) / actual_entry_price) * 100.0
        day_mae = ((b_low - actual_entry_price) / actual_entry_price) * 100.0
        if day_mfe > mfe:
            mfe = day_mfe
        if day_mae < mae:
            mae = day_mae

        # Record fixed horizon return
        if day_num in fwd_returns:
            gross_h = ((b_close - actual_entry_price) / actual_entry_price) * 100.0
            fwd_returns[day_num] = gross_h - friction_pct

        # Check target & stop triggers on this candle
        hit_t = b_high >= actual_target_price
        hit_s = b_low <= actual_stop_price

        if hit_t and days_to_target is None:
            days_to_target = day_num
            target_hit = True

        if hit_s and days_to_stop is None:
            days_to_stop = day_num
            stop_hit = True

        # Check if trade already exited
        if exit_date is not None:
            continue

        if hit_t and hit_s:
            # Both hit on the same daily candle
            is_ambiguous = True
            if ambiguity_handling == "CONSERVATIVE" or ambiguity_handling == "STOP_FIRST":
                exit_date = b_date
                exit_price = actual_stop_price
                exit_reason = "AMBIGUOUS_SAME_DAY_STOP"
                exit_day_idx = day_num
                stop_before_target = True
            elif ambiguity_handling == "TARGET_FIRST":
                exit_date = b_date
                exit_price = actual_target_price
                exit_reason = "AMBIGUOUS_SAME_DAY_TARGET"
                exit_day_idx = day_num
                target_before_stop = True
            elif ambiguity_handling == "EXCLUDE":
                exit_date = b_date
                exit_price = actual_entry_price
                exit_reason = "EXCLUDED_AMBIGUOUS"
                exit_day_idx = day_num

        elif hit_t:
            target_hit = True
            target_before_stop = True
            exit_date = b_date
            exit_price = actual_target_price
            exit_reason = "TARGET_HIT"
            exit_day_idx = day_num

        elif hit_s:
            stop_hit = True
            stop_before_target = True
            exit_date = b_date
            exit_price = actual_stop_price
            exit_reason = "STOP_HIT"
            exit_day_idx = day_num

    # If holding period expired without target or stop
    if exit_date is None and eval_len > 0:
        final_bar = bars.iloc[eval_len - 1]
        exit_date = str(final_bar[date_col])[:10]
        exit_price = float(final_bar[close_col])
        exit_reason = "TIME_HORIZON_REACHED"
        exit_day_idx = eval_len

    # Calculate returns and R-multiple
    if exit_price is not None:
        gross_ret = ((exit_price - actual_entry_price) / actual_entry_price) * 100.0
        net_ret = gross_ret - friction_pct
        r_mult = (exit_price - actual_entry_price) / risk_per_share if risk_per_share > 0 else 0.0
        holding_days = exit_day_idx or eval_len

        if exit_reason == "EXCLUDED_AMBIGUOUS":
            outcome_label = "EXCLUDED"
        elif net_ret > 0:
            outcome_label = "WIN"
        elif net_ret < 0:
            outcome_label = "LOSS"
        else:
            outcome_label = "BREAKEVEN"
    else:
        gross_ret = 0.0
        net_ret = 0.0
        r_mult = 0.0
        holding_days = 0
        outcome_label = "PENDING"

    return TradeOutcome(
        signal_id=signal_id,
        symbol=symbol,
        signal_date=signal_date,
        entry_date=entry_date,
        entry_price=actual_entry_price,
        stop_price=actual_stop_price,
        target_price=actual_target_price,
        risk_per_share=risk_per_share,
        initial_risk_pct=initial_risk_pct,
        exit_date=exit_date,
        exit_price=exit_price,
        exit_reason=exit_reason,
        holding_days=holding_days,
        gross_return_pct=gross_ret,
        net_return_pct=net_ret,
        r_multiple=r_mult,
        outcome=outcome_label,
        mfe_pct=mfe,
        mae_pct=mae,
        fwd_net_5d=fwd_returns.get(5),
        fwd_net_10d=fwd_returns.get(10),
        fwd_net_20d=fwd_returns.get(20),
        fwd_net_30d=fwd_returns.get(30),
        fwd_net_60d=fwd_returns.get(60),
        target_hit=target_hit,
        stop_hit=stop_hit,
        target_before_stop=target_before_stop,
        stop_before_target=stop_before_target,
        is_ambiguous_same_day=is_ambiguous,
        days_to_target=days_to_target,
        days_to_stop=days_to_stop,
    )
