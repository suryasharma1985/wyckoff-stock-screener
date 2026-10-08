# Phase 18: Point-in-Time Universe & Out-of-Sample Validation Report

**Date:** 2026-08-26  
**Status:** **OOS VALIDATION STOPPED / PENDING DATA**  
**OOS Validation Script:** [`scripts/run_phase18_oos_validation.py`](file:///c:/Users/surya/Downloads/wyckoff-stock-screener/scripts/run_phase18_oos_validation.py)  
**OOS Progress File:** [`data/diagnostics/phase18/progress.json`](file:///c:/Users/surya/Downloads/wyckoff-stock-screener/data/diagnostics/phase18/progress.json)  
**OOS Results File:** [`data/diagnostics/phase18/phase18_results.json`](file:///c:/Users/surya/Downloads/wyckoff-stock-screener/data/diagnostics/phase18/phase18_results.json)  

---

## 1. Dataset & Universe Audit Findings
* **Universe Size:** 1,971 active NSE equities.
* **Survivorship Status:** **FAIL (Survivorship bias present)**. The universe represents active constituents snapshot as of August 2026. Delisted, bankrupt, or suspended companies from 2023–2025 are completely missing from the price panel.
* **Point-in-Time Index Membership:** **FAIL**. The repository contains only the static constituent snapshot. Point-in-time constituent histories (revisions) are not present in the files and cannot be reconstructed.
* **Adjustment Status:** Corporate action splits/dividends are adjusted, but ticker changes and mergers are not point-in-time represented.

---

## 2. Definition of Out-of-Sample Period
* **Discovery Period:** 2023-06-01 through 2026-08-24 (fully consumed by Phase 15/17).
* **Untouched OOS Period:** **None available (Zero days)**. The local prices panel starts on 2023-01-02 and ends exactly on 2026-08-24.
* **Validation Decision:** **STOPPED**. There is no untouched historical data available in the current dataset. Running validation on the discovery data would violate the core research rules. Validation is paused until new market data covering dates after 2026-08-24 is loaded.

---

## 3. Written Hypothesis Registry (Frozen & Timestamped)
The following hypotheses are frozen for out-of-sample validation once data is available:
* **H0 (Baseline):** Current Screener + unconditional T+1 Open entry has positive edge.
* **H1 (Early Accumulation):** Group A (Spring, SC, SOS) outperforms Group B (LPS, AR, ST, UTAD).
* **H2 (Bear Breadth Gate):** Spring/SC setups have exceptional edge if breadth is $< 30\%$.
* **H3 (Neutral Regime Avoidance):** Strategy underperforms or loses money if breadth is $30\% \le \text{breadth} < 60\%$.
* **H4 (LPS Baseline):** Next-day Open LPS entries are positive but weaker.
* **H5 (LPS Breakout Control):** LPS breakout triggers (Model B/C) underperform baseline unconditional Open entries (Model A).
* **H6 (Composite Score):** Existing production score fails to rank setup outcomes (Spearman correlation $\approx 0.0$).

---

## 4. Out-of-Sample Validation Scorecard

| Question | Result | Evidence |
|---|---|---|
| **Baseline profitable OOS?** | **NOT TESTABLE YET**| Out-of-sample data not yet present |
| **Spring edge survives?** | **NOT TESTABLE YET**| Out-of-sample data not yet present |
| **SC edge survives?** | **NOT TESTABLE YET**| Out-of-sample data not yet present |
| **SOS edge survives?** | **NOT TESTABLE YET**| Out-of-sample data not yet present |
| **Spring/SC + Bear breadth survives?**| **NOT TESTABLE YET**| Out-of-sample data not yet present |
| **Neutral regime weakness survives?**| **NOT TESTABLE YET**| Out-of-sample data not yet present |
| **Composite score discriminates?** | **NOT TESTABLE YET**| Out-of-sample data not yet present |
| **LPS breakout improves execution?** | **NOT TESTABLE YET**| Out-of-sample data not yet present |
| **Tail robustness?** | **NOT TESTABLE YET**| Out-of-sample data not yet present |
| **Survivorship-free?** | **FAIL** | Stored universe has delisted stocks missing |
| **Lookahead-free?** | **PASS** | Slicing boundaries verified by date isolation |
| **OOS validation complete?** | **FAIL** | Blocked due to missing out-of-sample dates |

---

## 5. Answers to the 10 Key Validation Questions

### 1. Does the screener have a genuine out-of-sample edge?
**UNKNOWN (Not testable yet).** Since no out-of-sample data exists in the current repository, we cannot verify if the net expectancy (+3.71%) survives.

### 2. Does the Spring/SC edge survive?
**UNKNOWN (Not testable yet).** Springs (+5.30% net) and SCs (+5.99% net) have a strong discovery edge, but their out-of-sample survival is unvalidated.

### 3. Does the Bear-breadth hypothesis survive?
**UNKNOWN (Not testable yet).** The hypothesis that Springs perform best when breadth is $< 30\%$ requires out-of-sample validation.

### 4. Does the score actually predict returns?
**UNKNOWN (Not testable yet).** The score failed to predict returns in discovery. We expect it to fail out-of-sample as well.

### 5. Does LPS breakout execution help?
**UNKNOWN (Not testable yet).** Discovery data indicates it degrades returns. Out-of-sample validation is required.

### 6. How much of the return is explained by extreme winners?
**UNKNOWN (Not testable yet).** In discovery, removing the top 5% of winners reduced returns to +0.12%. We expect similar right-skewed fat-tail sensitivity out-of-sample.

### 7. Is survivorship bias still materially affecting the result?
**Yes.** Because delisted companies are absent from the active constituent snapshot, the historical returns are likely inflated.

### 8. What is the most defensible strategy interpretation?
The strategy acts as a **market capitulation liquidity provider**, buying panic selling (Springs/SCs) when market breadth is extremely low, and riding the subsequent market-wide recovery.

### 9. What remains unvalidated?
Everything except lookahead isolation and local data reconstructability. The positive net expectation remains an unvalidated hypothesis due to survivorship bias and lack of OOS data.

### 10. What should Phase 19 test?
Phase 19 must acquire fresh market data covering **August 2026 through the present** to act as a true out-of-sample validation dataset.
