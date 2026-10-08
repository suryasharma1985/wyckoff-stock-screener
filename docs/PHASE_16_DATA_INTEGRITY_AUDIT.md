# Phase 16A: Data & Backtest Integrity Audit Report

**Date:** 2026-08-26  
**Backtest ID:** `backtest_nse_eq_monthly_20260826`  

---

## 1. Backtest Metadata & Configurations
* **Universe Size:** 1,971 NSE equities (EQ Series)
* **Checkpoint Frequency:** Monthly signal checkpoints (39 dates from 2023-06-01 to 2026-08-24)
* **Total Signal Observations:** 68,059 signals generated
* **Exit Horizons:** 10-day, 20-day, and 60-day holding windows
* **Entry Model:** Next-day Open price execution (unconditional T+1 Open)
* **Friction Model:** 0.40% round-trip transaction costs subtracted from gross returns (representing 10 bps slippage + 10 bps brokerage each way)
* **Missing-Data Handling:** In `validate_ohlcv_dataframe()`, columns with missing OHLC data are skipped or dropped.
* **Duplicate Handling:** No duplicate signals exist for the same stock-date pair.

---

## 2. Reconstructability & Lookahead Safety
* **Reconstructability:** Every trade recorded in the ledger can be independently reconstructed using the daily price panel ([`historical_prices.csv`](file:///c:/Users/surya/Downloads/wyckoff-stock-screener/data/validation_results/20260826/historical_prices.csv)) and the signal parameters in [`backtest_returns.csv`](file:///c:/Users/surya/Downloads/wyckoff-stock-screener/data/validation_results/20260826/backtest_returns.csv).
* **Lookahead Isolation:** Confirmed. The signal engine strictly filters incoming data to `Date <= T` (where $T$ is the checkpoint signal date) before calculating moving averages, RSI, ATR, and Wyckoff event triggers. Forward returns are calculated strictly from $T+1$ onward.

---

## 3. Survivorship Bias & Requirements for Point-in-Time Testing
* **Current Status:** **FAIL (Survivorship bias present)**. The backtest universe consists of active NSE equities as of August 2026. Companies that went bankrupt, were delisted, or suspended during 2023–2025 are missing from the history.
* **Requirements for a Bias-Free Test:**
  1. **Historical Index Revision Data:** Monthly or quarterly historical constituent lists of indices (e.g., Nifty 50, Nifty 500) from 2023 to 2026.
  2. **Delisted/Acquired Stock Data:** Historical price series for delisted companies (e.g., RELIANCE POWER, etc., if delisted) to capture the returns of bankrupt/liquidated holdings.
  3. **Corporate Actions Database:** Accurate mapping of ticker changes (e.g., `ADANITR` to `ADANIENSOL`) and mergers to prevent false data omissions.
