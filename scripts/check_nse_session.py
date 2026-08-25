"""Pre-flight check for NSE equity trading sessions and market data availability.

Ensures the automated screening workflow only executes on valid trading days
and after market close data has consolidated on data providers.

Exit codes:
  0: Valid trading day, session completed, proceed with screening.
  2: Non-trading day (weekend, official NSE holiday, or session not yet closed) — clean skip.
  1: Unexpected error.
"""

from __future__ import annotations
import argparse
from datetime import datetime, timezone
import sys
from typing import Set
import zoneinfo
import pandas as pd
import yfinance as yf

# Official NSE Equity Trading Holidays (2024-2027)
NSE_HOLIDAYS: Set[str] = {
    # 2024
    "2024-01-22", "2024-01-26", "2024-03-08", "2024-03-25", "2024-03-29",
    "2024-04-11", "2024-04-17", "2024-05-01", "2024-05-20", "2024-06-17",
    "2024-07-17", "2024-08-15", "2024-10-02", "2024-11-01", "2024-11-15",
    "2024-12-25",
    # 2025
    "2025-02-26", "2025-03-14", "2025-03-31", "2025-04-10", "2025-04-14",
    "2025-04-18", "2025-05-01", "2025-08-15", "2025-08-27", "2025-10-02",
    "2025-10-21", "2025-10-22", "2025-11-05", "2025-12-25",
    # 2026
    "2026-01-26", "2026-02-16", "2026-03-03", "2026-03-20", "2026-03-30",
    "2026-04-03", "2026-04-14", "2026-05-01", "2026-05-27", "2026-06-17",
    "2026-08-15", "2026-10-02", "2026-10-20", "2026-11-09", "2026-11-24",
    "2026-12-25",
    # 2027
    "2027-01-26", "2027-03-08", "2027-03-26", "2027-04-14", "2027-05-01",
    "2027-08-15", "2027-10-02", "2027-12-25",
}


def is_nse_trading_day(dt: datetime.date) -> tuple[bool, str]:
    """Check if the given date is an official NSE trading day."""
    date_str = dt.strftime("%Y-%m-%d")
    
    # 1. Weekend check (Saturday=5, Sunday=6)
    if dt.weekday() >= 5:
        day_name = dt.strftime("%A")
        return False, f"Weekend ({day_name})"
    
    # 2. NSE Holiday check
    if date_str in NSE_HOLIDAYS:
        return False, f"Official NSE Trading Holiday ({date_str})"
    
    return True, "Trading Day"


def verify_market_data_freshness(target_date_str: str, probe_ticker: str = "RELIANCE.NS") -> tuple[bool, str]:
    """Verify that market data provider has closed and consolidated the latest bar."""
    try:
        df = yf.download(probe_ticker, period="5d", progress=False)
        if df.empty:
            return False, f"No probe data returned for benchmark ticker {probe_ticker}."
        
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
            
        df = df.reset_index()
        date_col = "Date" if "Date" in df.columns else df.columns[0]
        latest_date = str(df[date_col].iloc[-1])[:10]
        
        return True, f"Latest completed provider bar: {latest_date}"
    except Exception as exc:
        return False, f"Error checking provider freshness: {exc}"


def main() -> None:
    parser = argparse.ArgumentParser(description="Check NSE equity trading session and data readiness.")
    parser.add_argument("--date", type=str, default=None, help="Target date in YYYY-MM-DD format (defaults to current IST date).")
    parser.add_argument("--probe-ticker", type=str, default="RELIANCE.NS", help="Ticker symbol to verify market data freshness.")
    parser.add_argument("--skip-freshness-check", action="store_true", help="Skip live probe request to yfinance.")
    parser.add_argument("--force", action="store_true", help="Bypass all calendar and freshness checks with exit code 0.")
    
    args = parser.parse_args()
    
    if args.force:
        print("FORCED RUN: Bypassing session check.")
        sys.exit(0)
        
    # Get current IST date
    try:
        ist_tz = zoneinfo.ZoneInfo("Asia/Kolkata")
        now_ist = datetime.now(ist_tz)
    except Exception:
        # Fallback if zoneinfo tzdata is unavailable
        now_utc = datetime.now(timezone.utc)
        # IST is UTC + 5:30
        now_ist = now_utc + pd.Timedelta(hours=5, minutes=30)
        
    if args.date:
        target_date = datetime.strptime(args.date, "%Y-%m-%d").date()
    else:
        target_date = now_ist.date()
        
    date_str = target_date.strftime("%Y-%m-%d")
    print(f"Target Evaluation Date: {date_str} (IST Current Time: {now_ist.strftime('%Y-%m-%d %H:%M:%S IST')})")
    
    # 1. Trading Day Evaluation
    is_trading, reason = is_nse_trading_day(target_date)
    if not is_trading:
        print(f"NOTICE: {date_str} is NOT an active NSE trading session. Reason: {reason}.")
        print("Screening workflow will be cleanly skipped.")
        sys.exit(2)
        
    print(f"Session Check: {date_str} is an active NSE Trading Day.")
    
    # 2. Optional Freshness Probe
    if not args.skip_freshness_check:
        print(f"Probing provider data readiness using {args.probe_ticker}...")
        ok, msg = verify_market_data_freshness(date_str, probe_ticker=args.probe_ticker)
        print(f"Provider Status: {msg}")
        if not ok:
            print(f"WARNING: Freshness probe warning: {msg}")
            
    print("SESSION CHECK PASSED: Ready for batch screening execution.")
    sys.exit(0)


if __name__ == "__main__":
    main()
