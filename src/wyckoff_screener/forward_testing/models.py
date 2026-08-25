"""Data models for Phase 18 Google Sheets Forward-Testing System."""

from dataclasses import dataclass, field
from typing import Any, Final, Optional
import pandas as pd

SCHEMA_VERSION: Final[str] = "1.0.0"
DEFAULT_TARGET_1_PCT: Final[float] = 10.0
DEFAULT_TARGET_2_PCT: Final[float] = 20.0
DEFAULT_TARGET_3_PCT: Final[float] = 30.0
DEFAULT_STOP_LOSS_PCT: Final[float] = 5.0


@dataclass(frozen=True)
class ForwardSignal:
    """Immutable representation of a screener candidate signal.
    
    Once created from a screening run, signal properties are permanent and immutable.
    """
    signal_id: str
    run_id: str
    signal_date: str
    symbol: str
    company_name: str
    exchange: str
    priority: str
    score: float
    signal_type: str
    wyckoff_event: str
    wyckoff_phase: str
    vsa_status: str
    p_and_f_score: str
    entry_price: float
    close_price: float
    broad_setup_status: bool
    mechanically_qualified: bool
    tradingview_url: str
    screening_date: str
    source_run_date: str
    notes: str

    def to_dict(self) -> dict[str, Any]:
        """Serialize signal metadata to dictionary."""
        return {
            "Signal_ID": self.signal_id,
            "Run_ID": self.run_id,
            "Signal_Date": self.signal_date,
            "Symbol": self.symbol,
            "Company_Name": self.company_name,
            "Exchange": self.exchange,
            "Priority": self.priority,
            "Score": self.score,
            "Signal_Type": self.signal_type,
            "Wyckoff_Event": self.wyckoff_event,
            "Wyckoff_Phase": self.wyckoff_phase,
            "VSA_Status": self.vsa_status,
            "P&F_Score": self.p_and_f_score,
            "Entry_Price": round(self.entry_price, 2),
            "Close_Price": round(self.close_price, 2),
            "Broad_Setup_Status": self.broad_setup_status,
            "Mechanically_Qualified": self.mechanically_qualified,
            "TradingView_URL": self.tradingview_url,
            "Screening_Date": self.screening_date,
            "Source_Run_Date": self.source_run_date,
            "Notes": self.notes,
        }


@dataclass
class ForwardTradeResult:
    """Evaluation of post-signal forward performance against target & stop rules."""
    signal_id: str
    symbol: str
    signal_date: str
    entry_price: float

    current_price: Optional[float] = None
    current_return_pct: Optional[float] = None
    days_since_signal: int = 0
    status: str = "OPEN"  # OPEN, COMPLETED, DATA_UNAVAILABLE

    # Forward Horizon Mark-to-Market Returns
    ret_5d: Optional[float] = None
    ret_10d: Optional[float] = None
    ret_20d: Optional[float] = None
    ret_30d: Optional[float] = None
    ret_60d: Optional[float] = None

    # Excursions
    max_gain_pct: Optional[float] = None
    max_drawdown_pct: Optional[float] = None

    # Target & Stop Reached Flags (YES, NO, DATA_UNAVAILABLE)
    target_10_reached: str = "NO"
    target_20_reached: str = "NO"
    target_30_reached: str = "NO"
    stop_5_reached: str = "NO"

    # Final Classification: WIN, LOSS, OPEN, AMBIGUOUS, DATA_UNAVAILABLE
    result: str = "OPEN"
    result_reason: str = "ACTIVE_MONITORING"
    exit_date: Optional[str] = None
    exit_price: Optional[float] = None
    days_held: Optional[int] = None
    notes: str = ""

    def to_signals_tab_row(self, signal: ForwardSignal) -> dict[str, Any]:
        """Merge immutable signal with forward performance for master SIGNALS tab."""
        return {
            "Signal_ID": signal.signal_id,
            "Signal_Date": signal.signal_date,
            "Symbol": signal.symbol,
            "Company_Name": signal.company_name,
            "Priority": signal.priority,
            "Score": signal.score,
            "Signal_Type": signal.signal_type,
            "Wyckoff_Event": signal.wyckoff_event,
            "Wyckoff_Phase": signal.wyckoff_phase,
            "VSA_Status": signal.vsa_status,
            "P&F_Score": signal.p_and_f_score,
            "Entry_Price": round(signal.entry_price, 2),
            "Current_Price": round(self.current_price, 2) if self.current_price is not None else "DATA_UNAVAILABLE",
            "Current_Return_%": round(self.current_return_pct, 2) if self.current_return_pct is not None else "DATA_UNAVAILABLE",
            "Days_Since_Signal": self.days_since_signal,
            "Status": self.status,
            "+5D_Return": round(self.ret_5d, 2) if self.ret_5d is not None else "",
            "+10D_Return": round(self.ret_10d, 2) if self.ret_10d is not None else "",
            "+20D_Return": round(self.ret_20d, 2) if self.ret_20d is not None else "",
            "+30D_Return": round(self.ret_30d, 2) if self.ret_30d is not None else "",
            "+60D_Return": round(self.ret_60d, 2) if self.ret_60d is not None else "",
            "Max_Gain_%": round(self.max_gain_pct, 2) if self.max_gain_pct is not None else "",
            "Max_Drawdown_%": round(self.max_drawdown_pct, 2) if self.max_drawdown_pct is not None else "",
            "Target_10%": self.target_10_reached,
            "Target_20%": self.target_20_reached,
            "Target_30%": self.target_30_reached,
            "Stop_Loss_5%": self.stop_5_reached,
            "Result": self.result,
            "Notes": signal.notes,
            "TradingView_URL": signal.tradingview_url,
        }
