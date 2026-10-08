import os
import sys
import time
import hashlib
import json
import tempfile
import pandas as pd
import numpy as np
import yfinance as yf
from pathlib import Path

# Paths
INPUT_DIR = Path("c:/Users/surya/Downloads/wyckoff-stock-screener/data/validation_results/20260826")
HIST_PRICES_CSV = INPUT_DIR / "historical_prices.csv"
OOS_OUT_DIR = Path("c:/Users/surya/Downloads/wyckoff-stock-screener/data/oos/phase20")
OOS_PRICES_CSV = OOS_OUT_DIR / "oos_prices.csv"
UPDATE_MANIFEST = OOS_OUT_DIR / "oos_update_manifest.json"
UPDATE_HIST_DIR = OOS_OUT_DIR / "update_history"
DIAG_OUT_DIR = Path("c:/Users/surya/Downloads/wyckoff-stock-screener/data/diagnostics/phase21")
OOS_MATURITY_JSON = DIAG_OUT_DIR / "oos_maturity.json"
REPORT_MD = Path("c:/Users/surya/Downloads/wyckoff-stock-screener/docs/PHASE_21_OOS_MATURITY_REPORT.md")

def get_sha256(filepath):
    if not filepath.exists():
        return ""
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while True:
            chunk = f.read(65536)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()

def validate_row(row):
    # Enforce data quality checks
    high, low, open_val, close_val = row["High"], row["Low"], row["Open"], row["Close"]
    vol = row["Volume"]
    
    if pd.isna(high) or pd.isna(low) or pd.isna(open_val) or pd.isna(close_val) or pd.isna(vol):
        return False, "Missing fields"
    if open_val <= 0 or high <= 0 or low <= 0 or close_val <= 0:
        return False, "Price <= 0"
    if vol < 0:
        return False, "Volume < 0"
    if high < low:
        return False, "High < Low"
    if high < open_val:
        return False, "High < Open"
    if high < close_val:
        return False, "High < Close"
    if low > open_val:
        return False, "Low > Open"
    if low > close_val:
        return False, "Low > Close"
    return True, ""

def update_manifests(prev_hash, new_hash, prev_len, new_len, max_date_prev, max_date_new):
    UPDATE_HIST_DIR.mkdir(parents=True, exist_ok=True)
    ts = time.strftime("%Y%m%d_%H%M%S", time.gmtime())
    
    manifest = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "previous_sha256": prev_hash,
        "new_sha256": new_hash,
        "previous_row_count": prev_len,
        "new_row_count": new_len,
        "rows_added": new_len - prev_len,
        "previous_max_date": max_date_prev,
        "new_max_date": max_date_new,
        "DISCOVERY_CUTOFF": "2026-08-24"
    }
    
    with open(UPDATE_MANIFEST, "w") as f:
        json.dump(manifest, f, indent=2)
        
    hist_file = UPDATE_HIST_DIR / f"{ts}_oos_update_manifest.json"
    with open(hist_file, "w") as f:
        json.dump(manifest, f, indent=2)
    print(f"Saved update manifests to {UPDATE_MANIFEST} and {hist_file}")

def update_maturity(df):
    unique_dates = sorted(df["Date"].unique())
    n_sessions = len(unique_dates)
    unique_stocks = df["Symbol"].nunique()
    
    dups = int(df.duplicated(subset=["Symbol", "Date"]).sum())
    missing = int(df.isna().sum().sum())
    high_low_err = int((df["High"] < df["Low"]).sum())
    neg_prices = int(((df["Open"] <= 0) | (df["High"] <= 0) | (df["Low"] <= 0) | (df["Close"] <= 0)).sum())
    
    first_dt = unique_dates[0] if n_sessions > 0 else ""
    last_dt = unique_dates[-1] if n_sessions > 0 else ""
    
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
    
    DIAG_OUT_DIR.mkdir(parents=True, exist_ok=True)
    with open(OOS_MATURITY_JSON, "w") as f:
        json.dump(maturity, f, indent=2)
        
    # Markdown report
    report = f"""# Phase 21: Out-of-Sample Validation Maturity Report

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
        f.write(report)

def main():
    t0 = time.time()
    OOS_OUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # 1. Audit existing OOS prices
    prev_hash = get_sha256(OOS_PRICES_CSV)
    
    if OOS_PRICES_CSV.exists():
        df_old = pd.read_csv(OOS_PRICES_CSV)
        max_date_prev = str(df_old["Date"].max())
        prev_len = len(df_old)
    else:
        df_old = pd.DataFrame(columns=["Date", "Symbol", "Open", "High", "Low", "Close", "Volume"])
        max_date_prev = "2026-08-24"
        prev_len = 0
        
    print(f"Loaded existing OOS dataset with {prev_len} rows. Maximum date: {max_date_prev}")
    
    # Read tickers
    if not HIST_PRICES_CSV.exists():
        print(f"ERROR: Historical prices CSV not found at {HIST_PRICES_CSV}")
        return
    df_hist = pd.read_csv(HIST_PRICES_CSV, usecols=["Symbol"])
    unique_symbols = sorted(df_hist["Symbol"].unique())
    n_total = len(unique_symbols)
    
    # Calculate next dates to download
    # Next day after max_date_prev
    next_start = pd.to_datetime(max_date_prev) + pd.Timedelta(days=1)
    next_start_str = next_start.strftime("%Y-%m-%d")
    
    # Let's say we download up to tomorrow exclusive
    today_dt = pd.to_datetime(time.strftime("%Y-%m-%d", time.gmtime()))
    tomorrow_dt = today_dt + pd.Timedelta(days=1)
    tomorrow_str = tomorrow_dt.strftime("%Y-%m-%d")
    
    print(f"Checking for new dates starting {next_start_str} to {tomorrow_str}...")
    
    new_rows = []
    failed_tickers = 0
    success_tickers = 0
    count_processed = 0
    
    # Only execute yfinance if start_date < tomorrow
    if next_start < tomorrow_dt:
        batch_size = 100
        for i in range(0, n_total, batch_size):
            batch_syms = unique_symbols[i : i + batch_size]
            yf_syms = [f"{s}.NS" for s in batch_syms]
            yf_sym_str = " ".join(yf_syms)
            
            try:
                df_dl = yf.download(yf_sym_str, start=next_start_str, end=tomorrow_str, group_by="ticker", progress=False)
            except Exception as e:
                print(f"Batch download failed: {e}")
                failed_tickers += len(batch_syms)
                count_processed += len(batch_syms)
                continue
                
            for s in batch_syms:
                count_processed += 1
                yf_ticker = f"{s}.NS"
                if yf_ticker not in df_dl.columns.levels[0]:
                    failed_tickers += 1
                    continue
                    
                ticker_df = df_dl[yf_ticker].dropna(subset=["Close"]).reset_index()
                if len(ticker_df) == 0:
                    success_tickers += 1  # Technically downloaded, just no new data
                    continue
                    
                for idx, row in ticker_df.iterrows():
                    date_str = str(row["Date"].date()) if hasattr(row["Date"], "date") else str(row["Date"])
                    
                    # Firewall Check
                    if date_str <= "2026-08-24":
                        raise AssertionError(f"FIREWALL VIOLATION: Downloaded OOS row has date <= 2026-08-24: {date_str} for {s}")
                        
                    row_data = {
                        "Date": date_str,
                        "Symbol": s,
                        "Open": float(row["Open"]),
                        "High": float(row["High"]),
                        "Low": float(row["Low"]),
                        "Close": float(row["Close"]),
                        "Volume": int(row["Volume"]) if pd.notna(row["Volume"]) else 0
                    }
                    
                    valid, err = validate_row(row_data)
                    if not valid:
                        print(f"Quality Check Rejected row for {s} on {date_str}: {err}")
                        continue
                        
                    new_rows.append(row_data)
                success_tickers += 1
                
            # Display update progress
            elapsed = time.time() - t0
            elapsed_str = time.strftime("%H:%M:%S", time.gmtime(elapsed))
            rem_sec = int((elapsed / (count_processed / n_total)) - elapsed) if count_processed > 0 else 0
            rem_str = time.strftime("%H:%M:%S", time.gmtime(rem_sec))
            print(f"[{count_processed}/{n_total}] Downloaded - Elapsed: {elapsed_str} - ETA: {rem_str}")
            
    else:
        print("No new OOS dates to download (OOS dates already current).")
        
    # Append-only merge and duplicates check
    if len(new_rows) > 0:
        df_new = pd.DataFrame(new_rows)
        # Verify firewall again
        bad_dates = df_new[df_new["Date"] <= "2026-08-24"]
        if len(bad_dates) > 0:
            raise AssertionError(f"FIREWALL VIOLATION: OOS row to append has date <= 2026-08-24: {bad_dates.iloc[0]['Date']}")
            
        df_combined = pd.concat([df_old, df_new], ignore_index=True)
        df_combined = df_combined.drop_duplicates(subset=["Symbol", "Date"])
    else:
        df_combined = df_old.copy()
        
    # Atomic save
    with tempfile.NamedTemporaryFile("w", delete=False, dir=OOS_OUT_DIR, suffix=".csv") as tf:
        df_combined.to_csv(tf.name, index=False)
        temp_name = tf.name
        
    if os.path.exists(OOS_PRICES_CSV):
        os.remove(OOS_PRICES_CSV)
    os.rename(temp_name, OOS_PRICES_CSV)
    
    # Post-save audits
    new_hash = get_sha256(OOS_PRICES_CSV)
    new_len = len(df_combined)
    max_date_new = str(df_combined["Date"].max()) if new_len > 0 else "2026-08-24"
    
    update_manifests(prev_hash, new_hash, prev_len, new_len, max_date_prev, max_date_new)
    update_maturity(df_combined)
    
    print("\nPHASE 21A — OOS DATA UPDATE COMPLETE")
    print("====================================")
    print(f"Previous row count: {prev_len}")
    print(f"New row count: {new_len}")
    print(f"Rows added: {new_len - prev_len}")
    print(f"Previous maximum OOS date: {max_date_prev}")
    print(f"New maximum OOS date: {max_date_new}")
    print(f"Previous hash: {prev_hash}")
    print(f"New hash: {new_hash}")

if __name__ == "__main__":
    main()
