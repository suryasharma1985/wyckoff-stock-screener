import os
import sys
import time
import json
import pandas as pd
import numpy as np
import yfinance as yf
from pathlib import Path

# Paths
REPO_ROOT = Path("c:/Users/surya/Downloads/wyckoff-stock-screener")
SYMBOLS_CSV = REPO_ROOT / "data/research_datasets/20260824/symbols.csv"
PHASE22_DIR = REPO_ROOT / "data/validation_results/phase22_pre_discovery"
PHASE22_DATA_DIR = PHASE22_DIR / "data"

START_DATE = "2021-06-01"
END_DATE = "2023-08-31"

def validate_row(row):
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

def main():
    t0 = time.time()
    PHASE22_DATA_DIR.mkdir(parents=True, exist_ok=True)
    
    if not SYMBOLS_CSV.exists():
        print(f"ERROR: symbols.csv not found at {SYMBOLS_CSV}")
        sys.exit(1)
        
    df_symbols = pd.read_csv(SYMBOLS_CSV)
    unique_symbols = sorted(df_symbols["symbol"].unique())
    n_total = len(unique_symbols)
    print(f"Acquiring data for {n_total} stocks from {START_DATE} to {END_DATE}...")
    
    batch_size = 100
    success_count = 0
    fail_count = 0
    total_downloaded_rows = 0
    
    for i in range(0, n_total, batch_size):
        batch = unique_symbols[i : i + batch_size]
        yf_syms = [f"{s}.NS" for s in batch]
        yf_sym_str = " ".join(yf_syms)
        
        try:
            df_dl = yf.download(yf_sym_str, start=START_DATE, end=END_DATE, group_by="ticker", progress=False)
        except Exception as e:
            print(f"Batch {i//batch_size} download failed: {e}")
            fail_count += len(batch)
            continue
            
        for s in batch:
            yf_ticker = f"{s}.NS"
            if yf_ticker not in df_dl.columns.levels[0]:
                fail_count += 1
                continue
                
            ticker_df = df_dl[yf_ticker].dropna(subset=["Close"]).reset_index()
            if len(ticker_df) == 0:
                fail_count += 1
                continue
                
            valid_rows = []
            for idx, row in ticker_df.iterrows():
                date_str = str(row["Date"].date()) if hasattr(row["Date"], "date") else str(row["Date"])
                
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
                    # Print or log warnings, but filter it out
                    continue
                valid_rows.append(row_data)
                
            if len(valid_rows) >= 60:  # Minimum requirements for indicator history
                df_out = pd.DataFrame(valid_rows)
                df_out = df_out.sort_values("Date").drop_duplicates(subset=["Date"])
                df_out.to_csv(PHASE22_DATA_DIR / f"{s}.NS.csv", index=False)
                success_count += 1
                total_downloaded_rows += len(df_out)
            else:
                fail_count += 1
                
        elapsed = time.time() - t0
        elapsed_str = time.strftime("%H:%M:%S", time.gmtime(elapsed))
        rem_sec = int((elapsed / ((i + len(batch)) / n_total)) - elapsed) if i > 0 else 0
        rem_str = time.strftime("%H:%M:%S", time.gmtime(rem_sec))
        print(f"[{i + len(batch)}/{n_total}] Downloaded - Success: {success_count} - Failed: {fail_count} - Elapsed: {elapsed_str} - ETA: {rem_str}")
        
    # Write updated symbols.csv
    df_symbols_new = df_symbols.copy()
    df_symbols_new["canonical_file_path"] = df_symbols_new["symbol"].apply(
        lambda s: f"data/validation_results/phase22_pre_discovery/data/{s}.NS.csv"
    )
    
    # Save the updated symbols.csv in the Phase 22 folder
    df_symbols_new.to_csv(PHASE22_DIR / "symbols.csv", index=False)
    
    print("\nPHASE 22 DATA ACQUISITION COMPLETE")
    print("==================================")
    print(f"Success: {success_count}")
    print(f"Failed/Excluded: {fail_count}")
    print(f"Total rows: {total_downloaded_rows}")
    print(f"Updated symbols.csv exported to: {PHASE22_DIR / 'symbols.csv'}")

if __name__ == "__main__":
    main()
