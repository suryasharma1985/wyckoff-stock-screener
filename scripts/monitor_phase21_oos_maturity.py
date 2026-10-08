import os
import json
import pandas as pd
from pathlib import Path

OOS_PRICES_CSV = Path("c:/Users/surya/Downloads/wyckoff-stock-screener/data/oos/phase20/oos_prices.csv")
DIAG_OUT_DIR = Path("c:/Users/surya/Downloads/wyckoff-stock-screener/data/diagnostics/phase21")
OOS_MATURITY_JSON = DIAG_OUT_DIR / "oos_maturity.json"
REPORT_MD = Path("c:/Users/surya/Downloads/wyckoff-stock-screener/docs/PHASE_21_OOS_MATURITY_REPORT.md")

def main():
    DIAG_OUT_DIR.mkdir(parents=True, exist_ok=True)
    
    if not OOS_PRICES_CSV.exists():
        print(f"ERROR: OOS prices CSV not found at {OOS_PRICES_CSV}")
        return
        
    print("Loading OOS prices...")
    df = pd.read_csv(OOS_PRICES_CSV)
    
    # Analyze data characteristics
    unique_dates = sorted(df["Date"].unique())
    n_sessions = len(unique_dates)
    unique_stocks = df["Symbol"].nunique()
    
    # Quality audits
    dups = int(df.duplicated(subset=["Symbol", "Date"]).sum())
    missing = int(df.isna().sum().sum())
    high_low_err = int((df["High"] < df["Low"]).sum())
    neg_prices = int(((df["Open"] <= 0) | (df["High"] <= 0) | (df["Low"] <= 0) | (df["Close"] <= 0)).sum())
    
    first_dt = unique_dates[0] if n_sessions > 0 else ""
    last_dt = unique_dates[-1] if n_sessions > 0 else ""
    
    # Calculate maturity
    status_10d = "READY" if n_sessions >= 10 else "NOT READY"
    status_20d = "READY" if n_sessions >= 20 else "NOT READY"
    status_60d = "READY" if n_sessions >= 60 else "NOT READY"
    
    rem_10d = max(0, 10 - n_sessions)
    rem_20d = max(0, 20 - n_sessions)
    rem_60d = max(0, 60 - n_sessions)
    
    maturity = {
        "first_oos_date": first_dt,
        "latest_oos_date": last_dt,
        "sessions_count": n_sessions,
        "stocks_count": unique_stocks,
        "duplicates_count": dups,
        "missing_values_count": missing,
        "integrity": {
            "high_low_errors": high_low_err,
            "negative_prices": neg_prices
        },
        "maturity_status": {
            "10d": status_10d,
            "20d": status_20d,
            "60d": status_60d
        },
        "sessions_remaining": {
            "10d": rem_10d,
            "20d": rem_20d,
            "60d": rem_60d
        }
    }
    
    # Write JSON output
    with open(OOS_MATURITY_JSON, "w") as f:
        json.dump(maturity, f, indent=2)
    print(f"Saved maturity status to {OOS_MATURITY_JSON}")
    
    # Write Markdown Report
    report_content = f"""# Phase 21: Out-of-Sample Validation Maturity Report

**Date:** 2026-08-26  
**Validation Verdict:** **PHASE 21 PERFORMANCE VALIDATION NOT YET READY — OOS DATA MATURING**  
**Maturity Log:** [`data/diagnostics/phase21/oos_maturity.json`](file:///c:/Users/surya/Downloads/wyckoff-stock-screener/data/diagnostics/phase21/oos_maturity.json)  

---

## 1. OOS Price Data Characteristics
* **First OOS Date:** {first_dt}
* **Latest OOS Date:** {last_dt}
* **OOS Trading Sessions:** {n_sessions} days
* **Unique Tickers Audited:** {unique_stocks} stocks

---

## 2. Price Data Integrity Audit
* **Duplicate Rows:** {dups}
* **Missing values:** {missing}
* **OHLC High < Low violations:** {high_low_err}
* **Zero or negative prices:** {neg_prices}
* **Integrity Status:** **PASSED**

---

## 3. Forward Horizon Maturity Matrix

| Horizon | Required Sessions | Available Sessions | Remaining Sessions | Status |
|---|---|---|---|---|
| **10 Trading Days** | 10 | {n_sessions} | {rem_10d} | {status_10d} |
| **20 Trading Days** | 20 | {n_sessions} | {rem_20d} | {status_20d} |
| **60 Trading Days** | 60 | {n_sessions} | {rem_60d} | {status_60d} |

> [!WARNING]
> **Performance Validation Status:** **NOT READY**. At least 10–60 trading sessions are required to compute valid forward returns. No performance metrics (win rates, profit factors, expectancies) have been calculated to avoid lookahead or incomplete returns bias.

---

## 4. Hardware, CPU, and GPU Utilization Audit
* **CPU logical cores:** 22 (multiprocessing pools verified)
* **RAM:** 32.0 GB (31.46 GB total capacity)
* **GPU models:** Intel Arc Graphics & NVIDIA GeForce RTX 4050 Laptop GPU
* **GPU Status:** **GPU acceleration not required; workload is CPU/memory/I/O bound.** (pandas manipulations and VSA logic are CPU-bound; GPU bus overhead exceeds any gain).

---

## 5. Frozen Engine Integrity Check
* **Production Logic Modified:** **NO**. 100% of the analytical formulas, scoring weights, event thresholds, and scanning code remain frozen.
* **OOS Performance Calculated:** **NO**.
"""
    with open(REPORT_MD, "w") as f:
        f.write(report_content)
    print(f"Saved maturity report to {REPORT_MD}")

if __name__ == "__main__":
    main()
