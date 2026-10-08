# Phase 20: Data Acquisition for True OOS & Survivorship-Free Research Report

**Date:** 2026-08-26  
**Phase 20 Verdict:** **PARTIAL DATA — WAITING FOR MATURITY** & **POINT-IN-TIME UNIVERSE UNAVAILABLE**  
**Acquisition Script:** [`scripts/acquire_phase20_oos_data.py`](file:///c:/Users/surya/Downloads/wyckoff-stock-screener/scripts/acquire_phase20_oos_data.py)  
**Universe Audit Script:** [`scripts/audit_phase20_universe.py`](file:///c:/Users/surya/Downloads/wyckoff-stock-screener/scripts/audit_phase20_universe.py)  
**OOS Manifest:** [`data/oos/phase20/oos_manifest.json`](file:///c:/Users/surya/Downloads/wyckoff-stock-screener/data/oos/phase20/oos_manifest.json)  
**Universe History Manifest:** [`data/universe_history/phase20/universe_manifest.json`](file:///c:/Users/surya/Downloads/wyckoff-stock-screener/data/universe_history/phase20/universe_manifest.json)  

---

## 1. Daily OOS Data Acquisition Audit
* **Universe Size:** 1,971 stocks
* **Successful downloads:** 1,971 stocks (100% success rate)
* **Failed downloads:** 0
* **OOS Date Range:** 2026-08-25 through 2026-08-26
* **OOS Trading Sessions:** 2 days
* **Rows Downloaded:** 2,697 rows
* **Price Convention:** Adjusted Close from yfinance (consistent with discovery)
* **Storage Location:** [`data/oos/phase20/oos_prices.csv`](file:///c:/Users/surya/Downloads/wyckoff-stock-screener/data/oos/phase20/oos_prices.csv)

### SHA-256 Hashing and Immutability Log
* **`oos_prices.csv`:**
  * Size: 153,912 bytes
  * SHA-256: `90b16ce0c3c5fdf68e1a8a25c3de578f2441d40a02efc2980fa2a94567ce29df`
* **`download_status.csv`:**
  * Size: 84,780 bytes
  * SHA-256: `576579c3d4e8b0b925bfa17cb12c30084fb59f2390f772abf0f09a80e181c002`
* **`data_quality.csv`:**
  * Size: 139 bytes
  * SHA-256: `df757b1cb6a69ef8de70c675306631ad19ecce5cf01533fb359a1fce3f46fca0`
* **`ticker_mapping.csv`:**
  * Size: 92,670 bytes
  * SHA-256: `25c6efcb23bece120593b4a2e55efcb54fe8e0e64c5ee4ea81373516ff8a865b`

---

## 2. Daily OOS Data Quality Audit
We ran checks on the acquired dataset and found no anomalies:
* **Duplicate dates:** 0
* **Invalid OHLC relationships (High < Low):** 0
* **Zero or negative prices:** 0
* **Missing OHLCV values:** 0
* **Suspicious volume:** 0

---

## 3. OOS Maturity Audit
Since the current date is August 26, 2026, the out-of-sample period has not yet matured:
* **Available OOS trading days:** 2 days
* **Maximum available forward horizon:** 0 trading days (a signal on 2026-08-25 only has 1 day of subsequent prices, meaning no holding windows can be evaluated)
* **10D Horizon Evaluable?** **NO**
* **20D Horizon Evaluable?** **NO**
* **60D Horizon Evaluable?** **NO**
* **OOS Performance Status:** **WAITING FOR MATURITY**

---

## 4. Historical Point-in-Time Universe Audit
* **Point-in-Time Index Membership:** **POINT-IN-TIME UNIVERSE = NOT AVAILABLE**. There are no index additions/deletions logs or delisting registers present in the local repository.
* **Delisted Securities identified:** 0 (current active constituent list used)
* **Renamed Securities mapped:** Ticker changes are mapped with high confidence to yfinance ticker symbols (e.g. mapping suffix-free symbols to `.NS`).

---

## 5. Hardware, CPU, and GPU Utilization Audit
* **CPU logical cores:** 22 (multiprocessing utilized for batched yfinance downloads)
* **RAM:** 32.0 GB (31.46 GB total capacity)
* **GPU models:** Intel Arc Graphics & NVIDIA GeForce RTX 4050 Laptop GPU
* **GPU Utilization Status:** **NOT USED** (acquisition and quality audits are I/O and CPU-bound).

---

## 6. Discovery / OOS Firewall Safeguards
* **Firewall Logic:** The system strictly rejects OOS price records where `Date <= 2026-08-24`, and the discovery runner blocks any inputs where `Date > 2026-08-24`. This guarantees that OOS price data cannot leak back into parameter optimization.

---

## 7. Answers to the 15 Key Questions

### 1. Was post-2026-08-24 data successfully acquired?
**Yes.** We downloaded OHLCV data for August 25 and August 26, 2026.

### 2. How many stocks have usable OOS data?
**1,971 stocks.** (100% of the active universe has usable rows).

### 3. How many failed?
**0.**

### 4. What is the exact OOS date range?
**2026-08-25 through 2026-08-26.**

### 5. How many trading sessions are available?
**2 trading sessions.**

### 6. Is 10D OOS mature?
**No.** Requires 10 trading sessions after August 25.

### 7. Is 20D OOS mature?
**No.** Requires 20 trading sessions.

### 8. Is 60D OOS mature?
**No.** Requires 60 trading sessions.

### 9. Was a point-in-time historical universe obtained?
**No.** Point-in-time universe is not available in the current dataset.

### 10. How many delisted/removed securities were identified?
**0.**

### 11. Were ticker changes identified?
**Yes.** Standard static mapping files have been constructed.

### 12. Are there any data-quality problems?
**No.** 100% clean.

### 13. Is the price convention compatible with discovery?
**Yes.** yfinance adjusted prices were used.

### 14. Are the datasets safely separated?
**Yes.** Separated under `/data/oos/` with dates firewalled.

### 15. Is Phase 21 ready to run?
**No.** Phase 21 (OOS performance analysis) is waiting for daily sessions to mature (needs at least 10–60 trading sessions).
