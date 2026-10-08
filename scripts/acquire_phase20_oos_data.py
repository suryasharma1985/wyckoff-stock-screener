import os
import sys
import time
import hashlib
import json
import pandas as pd
import numpy as np
import yfinance as yf
from pathlib import Path

# Paths
INPUT_DIR = Path("c:/Users/surya/Downloads/wyckoff-stock-screener/data/validation_results/20260826")
HIST_PRICES_CSV = INPUT_DIR / "historical_prices.csv"
OOS_OUT_DIR = Path("c:/Users/surya/Downloads/wyckoff-stock-screener/data/oos/phase20")
OOS_PRICES_CSV = OOS_OUT_DIR / "oos_prices.csv"
OOS_MANIFEST_JSON = OOS_OUT_DIR / "oos_manifest.json"
DOWNLOAD_STATUS_CSV = OOS_OUT_DIR / "download_status.csv"
DATA_QUALITY_CSV = OOS_OUT_DIR / "data_quality.csv"
TICKER_MAPPING_CSV = OOS_OUT_DIR / "ticker_mapping.csv"

def get_sha256(filepath):
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while True:
            chunk = f.read(65536)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()

def main():
    t0 = time.time()
    OOS_OUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # 1. Ingest symbols from historical_prices.csv
    if not HIST_PRICES_CSV.exists():
        print(f"ERROR: Historical prices not found at {HIST_PRICES_CSV}")
        return
        
    print("Ingesting symbols from historical_prices.csv...")
    df_hist = pd.read_csv(HIST_PRICES_CSV, usecols=["Symbol"])
    unique_symbols = sorted(df_hist["Symbol"].unique())
    n_total = len(unique_symbols)
    print(f"Loaded {n_total} unique symbols.")
    
    # 2. Batch download from yfinance
    batch_size = 100
    all_rows = []
    status_rows = []
    mapping_rows = []
    
    # Determine date range (August 25, 2026 onwards)
    start_date = "2026-08-25"
    end_date = "2026-08-27"
    
    count_processed = 0
    count_success = 0
    count_failed = 0
    
    for i in range(0, n_total, batch_size):
        batch_syms = unique_symbols[i : i + batch_size]
        # Append .NS suffix
        yf_syms = [f"{s}.NS" for s in batch_syms]
        yf_sym_str = " ".join(yf_syms)
        
        try:
            df_dl = yf.download(yf_sym_str, start=start_date, end=end_date, group_by="ticker", progress=False)
        except Exception as e:
            print(f"Batch download error: {e}")
            for s in batch_syms:
                status_rows.append({
                    "Ticker": s,
                    "Status": "FAILED",
                    "First Date": "",
                    "Last Date": "",
                    "Rows": 0,
                    "Error": str(e),
                    "Provider": "yfinance"
                })
                count_failed += 1
                count_processed += 1
            continue
            
        for s in batch_syms:
            count_processed += 1
            yf_ticker = f"{s}.NS"
            mapping_rows.append({
                "old_ticker": s,
                "new_ticker": yf_ticker,
                "company": s,
                "effective_date": "2023-01-02",
                "confidence": "HIGH",
                "source": "yfinance"
            })
            
            if yf_ticker not in df_dl.columns.levels[0]:
                status_rows.append({
                    "Ticker": s,
                    "Status": "FAILED",
                    "First Date": "",
                    "Last Date": "",
                    "Rows": 0,
                    "Error": "Ticker missing in download response",
                    "Provider": "yfinance"
                })
                count_failed += 1
                continue
                
            ticker_df = df_dl[yf_ticker].dropna(subset=["Close"])
            n_rows = len(ticker_df)
            
            if n_rows == 0:
                status_rows.append({
                    "Ticker": s,
                    "Status": "FAILED",
                    "First Date": "",
                    "Last Date": "",
                    "Rows": 0,
                    "Error": "No data returned",
                    "Provider": "yfinance"
                })
                count_failed += 1
                continue
                
            ticker_df = ticker_df.reset_index()
            first_dt = str(ticker_df["Date"].min())
            last_dt = str(ticker_df["Date"].max())
            
            for idx, row in ticker_df.iterrows():
                all_rows.append({
                    "Date": str(row["Date"].date()) if hasattr(row["Date"], "date") else str(row["Date"]),
                    "Symbol": s,
                    "Open": float(row["Open"]),
                    "High": float(row["High"]),
                    "Low": float(row["Low"]),
                    "Close": float(row["Close"]),
                    "Volume": int(row["Volume"]) if pd.notna(row["Volume"]) else 0
                })
                
            status_rows.append({
                "Ticker": s,
                "Status": "SUCCESS",
                "First Date": first_dt[:10],
                "Last Date": last_dt[:10],
                "Rows": n_rows,
                "Error": "",
                "Provider": "yfinance"
            })
            count_success += 1
            
        # Display progress every batch
        elapsed = time.time() - t0
        elapsed_str = time.strftime("%H:%M:%S", time.gmtime(elapsed))
        rem_sec = int((elapsed / (count_processed / n_total)) - elapsed) if count_processed > 0 else 0
        rem_str = time.strftime("%H:%M:%S", time.gmtime(rem_sec))
        throughput = round(count_processed / (elapsed / 60.0), 1) if elapsed > 0 else 0
        
        print("\nPHASE 20 DATA ACQUISITION")
        print("-------------------------")
        print(f"Tickers processed: {count_processed} / {n_total}")
        print(f"Completion: {count_processed / n_total:.2%}")
        print(f"Successful: {count_success}")
        print(f"Failed: {count_failed}")
        print(f"Rows downloaded: {len(all_rows)}")
        print(f"Elapsed: {elapsed_str}")
        print(f"Estimated remaining: {rem_str}")
        print(f"Current throughput: {throughput} tickers/min")
        print("Status: RUNNING\n")
        
    # Save CSV files
    df_prices = pd.DataFrame(all_rows)
    df_prices.to_csv(OOS_PRICES_CSV, index=False)
    
    df_status = pd.DataFrame(status_rows)
    df_status.to_csv(DOWNLOAD_STATUS_CSV, index=False)
    
    df_mapping = pd.DataFrame(mapping_rows)
    df_mapping.to_csv(TICKER_MAPPING_CSV, index=False)
    
    # 3. Data Quality Audit
    dq_issues = []
    if len(df_prices) > 0:
        # Check duplicate dates
        dups = df_prices.duplicated(subset=["Symbol", "Date"]).sum()
        dq_issues.append({"Check": "Duplicate dates", "Count": int(dups)})
        
        # Check invalid OHLC (High < Low)
        ohlc_err = (df_prices["High"] < df_prices["Low"]).sum()
        dq_issues.append({"Check": "Invalid OHLC relationships (High < Low)", "Count": int(ohlc_err)})
        
        # Check zero/negative prices
        neg_p = ((df_prices["Open"] <= 0) | (df_prices["High"] <= 0) | (df_prices["Low"] <= 0) | (df_prices["Close"] <= 0)).sum()
        dq_issues.append({"Check": "Zero or negative prices", "Count": int(neg_p)})
        
        # Check missing OHLCV
        missing = df_prices[["Open", "High", "Low", "Close", "Volume"]].isna().sum().sum()
        dq_issues.append({"Check": "Missing OHLCV values", "Count": int(missing)})
        
    df_dq = pd.DataFrame(dq_issues)
    df_dq.to_csv(DATA_QUALITY_CSV, index=False)
    
    # 4. Save Manifest
    first_date_str = str(df_prices["Date"].min()) if len(df_prices) > 0 else ""
    last_date_str = str(df_prices["Date"].max()) if len(df_prices) > 0 else ""
    
    manifest = {
        "acquisition_timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "provider": "yfinance",
        "universe_size": n_total,
        "ticker_count": count_success,
        "first_date": first_date_str,
        "last_date": last_date_str,
        "row_count": len(df_prices),
        "file_hashes": {
            "oos_prices.csv": get_sha256(OOS_PRICES_CSV) if OOS_PRICES_CSV.exists() else "",
            "download_status.csv": get_sha256(DOWNLOAD_STATUS_CSV) if DOWNLOAD_STATUS_CSV.exists() else "",
            "data_quality.csv": get_sha256(DATA_QUALITY_CSV) if DATA_QUALITY_CSV.exists() else "",
            "ticker_mapping.csv": get_sha256(TICKER_MAPPING_CSV) if TICKER_MAPPING_CSV.exists() else ""
        },
        "failed_ticker_count": count_failed,
        "missing_data_count": int(df_dq["Count"].sum()) if len(df_dq) > 0 else 0,
        "DISCOVERY_CUTOFF": "2026-08-24",
        "OOS_START": first_date_str
    }
    with open(OOS_MANIFEST_JSON, "w") as f:
        json.dump(manifest, f, indent=2)
        
    print(f"Data acquisition and audit complete. Manifest written to {OOS_MANIFEST_JSON}")

if __name__ == "__main__":
    main()
