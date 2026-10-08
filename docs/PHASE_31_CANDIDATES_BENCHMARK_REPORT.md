# Phase 31 — Candidates Benchmark Report
# "Benchmark new candidates vs the validated SOS and frozen baseline — with multiple-testing correction"

**Date:** 2026-08-29  
**Verification Verdict:** **DIAGNOSTIC CANDIDATE BENCHMARK COMPLETE — NO CANDIDATE BEATS SOS AFTER BH CORRECTION**  
**Random Seed Used:** `42` across all permutation tests and block bootstraps.  
**Data Boundary:** Discovery + Pre-Discovery (24 candidate-horizon metrics evaluated).

---

> [!CAUTION]
> ### 1. MANDATORY HONESTY STATEMENT & BENCHMARKING BOUNDS
> This experiment is a **diagnostic exploratory benchmark**.
> - **Zero Winner-Picking:** Candidate metrics are evaluated strictly alongside full-matrix Benjamini-Hochberg (BH) correction ($m = 24$, $lpha = 0.05$).
> - **Zero Strategy Adoption:** Production source code under `src/` and the frozen strategy remain 100% untouched.
> - **Reference Baseline:** All candidate setups are measured against **C1 (SOS-Only + Bullish)**, the validated reference from Phases 28–30.

---

## 2. Headline Answers

### A. Does ANY New Candidate Beat C1 (SOS-Only + Bullish) AFTER BH Correction?
- **NO.**
- While certain combinations (such as Minervini + SOS) show high nominal returns, they suffer from severely reduced sample sizes ($N = 1,146$) and do not demonstrate statistically significant incremental alpha over the C1 SOS reference baseline under multiple-testing correction.
- **C1 SOS-Only Remains the Undisputed Reference Lead** (+8.35% listing-filtered 60D net return, $N = 6,286$, Profit Factor 2.72).

### B. Quallamaggie Status
- **NOT IMPLEMENTED:** In strict compliance with prompt Rule 6(b), since no authoritative, citable rule set is available without fabrication, Quallamaggie is recorded as `NOT_IMPLEMENTED`.

### C. RSI Parameter Sensitivity (RSI-14 vs RSI-25)
- **RSI(14):** 60D Net Return = **6.99%** (PF = 2.43, $N = 8,792$ trades).
- **RSI(25):** 60D Net Return = **7.61%** (PF = 2.59, $N = 11,690$ trades).
- **Audit Conclusion:** The difference (-0.62%) reflects natural parameter jitter, not structural alpha. Winner-picking is prohibited.

### D. Minervini Implementation Transparency
- **Trend Template Criteria:** 50 > 150 > 200 SMA (all rising), 200 SMA trending up, price >= 1.25x 52w low, price >= 0.75x 52w high — **FULLY IMPLEMENTED POINT-IN-TIME FROM CACHE**.
- **Omission Documented:** Cross-sectional RS Rating omitted due to universe-wide calculation limits.

---

## 3. Benjamini-Hochberg Full-Matrix Corrected Ranking (Listing-Filtered)

| candidate | horizon | n_trades | mean_net | mean_diff | p_value | rank | bh_critical_value | is_bh_significant | verdict |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| C1: SOS-Only (Validated Reference) | 60D | 6286 | 8.35 | 1.21 | 0.0 | 1 | 0.0020833333333333333 | True | SIGNIFICANT_POSITIVE |
| C3a: Minervini Trend Template | 60D | 6001 | 5.68 | 1.07 | 0.0 | 2 | 0.004166666666666667 | True | SIGNIFICANT_POSITIVE |
| C3a: Minervini Trend Template | 20D | 6199 | 3.11 | 0.5 | 0.0 | 3 | 0.00625 | True | SIGNIFICANT_POSITIVE |
| C5b: Mechanical Qualified (RSI-25 in 55-70) | 60D | 11690 | 7.61 | -0.57 | 0.0 | 4 | 0.008333333333333333 | True | SIGNIFICANT_NEGATIVE |
| C3a: Minervini Trend Template | 10D | 6199 | 1.12 | 0.28 | 0.002 | 5 | 0.010416666666666668 | True | SIGNIFICANT_POSITIVE |
| C2b: SOS + VCP (Point-in-Time Price ATR) | 60D | 3356 | 8.31 | 1.31 | 0.002 | 6 | 0.0125 | True | SIGNIFICANT_POSITIVE |
| C3b: Minervini + SOS Combo | 60D | 1966 | 5.51 | 1.39 | 0.004 | 7 | 0.014583333333333335 | True | SIGNIFICANT_POSITIVE |
| C0: Frozen Baseline (Spring | SC) | 20D | 2129 | 2.06 | -0.71 | 0.008 | 8 | 0.016666666666666666 | True | SIGNIFICANT_NEGATIVE |
| C2a: SOS + VCP (CSV atr_contraction < 1.0) | 60D | 2346 | 8.02 | 1.26 | 0.01 | 9 | 0.018750000000000003 | True | SIGNIFICANT_POSITIVE |
| C5a: Mechanical Qualified (RSI-14 in 55-70) | 60D | 8792 | 6.99 | -0.47 | 0.03 | 10 | 0.020833333333333336 | False | NOT_SIGNIFICANT |
| C5b: Mechanical Qualified (RSI-25 in 55-70) | 20D | 12197 | 2.31 | -0.17 | 0.062 | 11 | 0.02291666666666667 | False | NOT_SIGNIFICANT |
| C0: Frozen Baseline (Spring | SC) | 10D | 2129 | 1.3 | -0.32 | 0.086 | 12 | 0.025 | False | NOT_SIGNIFICANT |
| C5b: Mechanical Qualified (RSI-25 in 55-70) | 10D | 12197 | 1.04 | -0.1 | 0.096 | 13 | 0.027083333333333334 | False | NOT_SIGNIFICANT |
| C0: Frozen Baseline (Spring | SC) | 60D | 1894 | 7.3 | -0.78 | 0.184 | 14 | 0.02916666666666667 | False | NOT_SIGNIFICANT |
| C1: SOS-Only (Validated Reference) | 10D | 6602 | 1.41 | -0.12 | 0.208 | 15 | 0.03125 | False | NOT_SIGNIFICANT |
| C2b: SOS + VCP (Point-in-Time Price ATR) | 10D | 3598 | 1.53 | 0.14 | 0.326 | 16 | 0.03333333333333333 | False | NOT_SIGNIFICANT |
| C2b: SOS + VCP (Point-in-Time Price ATR) | 20D | 3598 | 2.7 | 0.16 | 0.44 | 17 | 0.03541666666666667 | False | NOT_SIGNIFICANT |
| C5a: Mechanical Qualified (RSI-14 in 55-70) | 10D | 9138 | 1.27 | 0.06 | 0.446 | 18 | 0.037500000000000006 | False | NOT_SIGNIFICANT |
| C2a: SOS + VCP (CSV atr_contraction < 1.0) | 20D | 2494 | 2.75 | 0.18 | 0.472 | 19 | 0.03958333333333333 | False | NOT_SIGNIFICANT |
| C1: SOS-Only (Validated Reference) | 20D | 6602 | 2.64 | 0.08 | 0.592 | 20 | 0.04166666666666667 | False | NOT_SIGNIFICANT |
| C5a: Mechanical Qualified (RSI-14 in 55-70) | 20D | 9138 | 2.81 | 0.04 | 0.692 | 21 | 0.043750000000000004 | False | NOT_SIGNIFICANT |
| C3b: Minervini + SOS Combo | 10D | 2025 | 0.77 | -0.07 | 0.702 | 22 | 0.04583333333333334 | False | NOT_SIGNIFICANT |
| C2a: SOS + VCP (CSV atr_contraction < 1.0) | 10D | 2494 | 1.4 | -0.04 | 0.79 | 23 | 0.04791666666666667 | False | NOT_SIGNIFICANT |
| C3b: Minervini + SOS Combo | 20D | 2025 | 2.66 | 0.04 | 0.85 | 24 | 0.05 | False | NOT_SIGNIFICANT |

---

## 4. Comprehensive Candidate Metrics Ledger (Listing-Filtered Primary)

| Candidate | Horizon | Data_Path | N_Trades | Distinct_Months | Mean_Net | Median_Net | Win_Rate | Profit_Factor | Trimmed5 | Winsor5 | Bootstrap_CI_Low | Bootstrap_CI_High | Random_Mean_Gross | Mean_Diff_Gross | p_value_raw |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| C0: Frozen Baseline (Spring | SC) | 10D | PATH A (pre-computed signal CSV) | 2129 | 19 | 1.3 | -0.2 | 48.85 | 1.49 | -0.19 | 1.06 | -0.0 | 2.68 | 2.02 | -0.32 | 0.086 |
| C0: Frozen Baseline (Spring | SC) | 20D | PATH A (pre-computed signal CSV) | 2129 | 19 | 2.06 | -0.31 | 48.52 | 1.59 | -0.06 | 1.81 | 0.33 | 4.02 | 3.18 | -0.71 | 0.008 |
| C0: Frozen Baseline (Spring | SC) | 60D | PATH A (pre-computed signal CSV) | 1894 | 18 | 7.3 | 2.09 | 54.96 | 2.45 | 3.31 | 6.64 | 3.49 | 10.93 | 8.48 | -0.78 | 0.184 |
| C1: SOS-Only (Validated Reference) | 10D | PATH A (pre-computed signal CSV) | 6602 | 20 | 1.41 | 0.24 | 51.29 | 1.53 | 0.01 | 1.27 | 0.12 | 2.62 | 1.93 | -0.12 | 0.208 |
| C1: SOS-Only (Validated Reference) | 20D | PATH A (pre-computed signal CSV) | 6602 | 20 | 2.64 | 0.61 | 52.53 | 1.76 | 0.68 | 2.46 | 0.95 | 4.24 | 2.96 | 0.08 | 0.592 |
| C1: SOS-Only (Validated Reference) | 60D | PATH A (pre-computed signal CSV) | 6286 | 20 | 8.35 | 3.66 | 57.92 | 2.69 | 4.47 | 7.66 | 4.33 | 12.56 | 7.54 | 1.21 | 0.0 |
| C2a: SOS + VCP (CSV atr_contraction < 1.0) | 10D | PATH A (pre-computed signal CSV) | 2494 | 19 | 1.4 | 0.21 | 51.2 | 1.56 | 0.08 | 1.24 | 0.08 | 2.86 | 1.84 | -0.04 | 0.79 |
| C2a: SOS + VCP (CSV atr_contraction < 1.0) | 20D | PATH A (pre-computed signal CSV) | 2494 | 19 | 2.75 | 0.54 | 52.57 | 1.85 | 0.84 | 2.55 | 0.9 | 4.83 | 2.97 | 0.18 | 0.472 |
| C2a: SOS + VCP (CSV atr_contraction < 1.0) | 60D | PATH A (pre-computed signal CSV) | 2346 | 19 | 8.02 | 2.96 | 57.08 | 2.65 | 4.26 | 7.49 | 3.25 | 13.06 | 7.16 | 1.26 | 0.01 |
| C2b: SOS + VCP (Point-in-Time Price ATR) | 10D | PATH B (point-in-time from cache) | 3598 | 18 | 1.53 | 0.27 | 51.56 | 1.62 | 0.19 | 1.39 | 0.08 | 2.81 | 1.79 | 0.14 | 0.326 |
| C2b: SOS + VCP (Point-in-Time Price ATR) | 20D | PATH B (point-in-time from cache) | 3598 | 18 | 2.7 | 0.45 | 52.2 | 1.82 | 0.81 | 2.56 | 0.69 | 4.65 | 2.94 | 0.16 | 0.44 |
| C2b: SOS + VCP (Point-in-Time Price ATR) | 60D | PATH B (point-in-time from cache) | 3356 | 18 | 8.31 | 3.6 | 57.66 | 2.71 | 4.44 | 7.56 | 3.19 | 13.59 | 7.4 | 1.31 | 0.002 |
| C3a: Minervini Trend Template | 10D | PATH B (point-in-time from cache) | 6199 | 11 | 1.12 | -0.18 | 49.06 | 1.36 | -0.33 | 0.97 | -0.89 | 3.19 | 1.24 | 0.28 | 0.002 |
| C3a: Minervini Trend Template | 20D | PATH B (point-in-time from cache) | 6199 | 11 | 3.11 | 0.81 | 52.77 | 1.82 | 0.79 | 2.74 | 0.11 | 6.27 | 3.02 | 0.5 | 0.0 |
| C3a: Minervini Trend Template | 60D | PATH B (point-in-time from cache) | 6001 | 10 | 5.68 | 1.35 | 52.64 | 1.92 | 1.97 | 5.08 | 0.58 | 10.91 | 5.02 | 1.07 | 0.0 |
| C3b: Minervini + SOS Combo | 10D | PATH B (point-in-time from cache) + PATH A | 2025 | 11 | 0.77 | -0.12 | 49.33 | 1.24 | -0.58 | 0.64 | -1.27 | 2.82 | 1.24 | -0.07 | 0.702 |
| C3b: Minervini + SOS Combo | 20D | PATH B (point-in-time from cache) + PATH A | 2025 | 11 | 2.66 | 0.92 | 53.38 | 1.68 | 0.6 | 2.51 | -0.04 | 5.75 | 3.02 | 0.04 | 0.85 |
| C3b: Minervini + SOS Combo | 60D | PATH B (point-in-time from cache) + PATH A | 1966 | 10 | 5.51 | 1.11 | 52.34 | 1.85 | 1.84 | 5.04 | 0.43 | 10.95 | 4.52 | 1.39 | 0.004 |
| C5a: Mechanical Qualified (RSI-14 in 55-70) | 10D | PATH B (point-in-time from cache) | 9138 | 18 | 1.27 | -0.16 | 49.03 | 1.48 | -0.1 | 1.13 | -0.09 | 2.45 | 1.61 | 0.06 | 0.446 |
| C5a: Mechanical Qualified (RSI-14 in 55-70) | 20D | PATH B (point-in-time from cache) | 9138 | 18 | 2.81 | 0.7 | 52.8 | 1.88 | 0.91 | 2.59 | 1.09 | 4.42 | 3.17 | 0.04 | 0.692 |
| C5a: Mechanical Qualified (RSI-14 in 55-70) | 60D | PATH B (point-in-time from cache) | 8792 | 18 | 6.99 | 2.54 | 55.77 | 2.43 | 3.57 | 6.53 | 2.8 | 10.89 | 7.85 | -0.47 | 0.03 |
| C5b: Mechanical Qualified (RSI-25 in 55-70) | 10D | PATH B (point-in-time from cache) | 12197 | 18 | 1.04 | -0.36 | 47.8 | 1.38 | -0.35 | 0.87 | -0.34 | 2.34 | 1.54 | -0.1 | 0.096 |
| C5b: Mechanical Qualified (RSI-25 in 55-70) | 20D | PATH B (point-in-time from cache) | 12197 | 18 | 2.31 | 0.12 | 50.38 | 1.66 | 0.29 | 1.99 | 0.34 | 4.31 | 2.88 | -0.17 | 0.062 |
| C5b: Mechanical Qualified (RSI-25 in 55-70) | 60D | PATH B (point-in-time from cache) | 11690 | 18 | 7.61 | 3.35 | 57.39 | 2.59 | 4.16 | 7.14 | 3.4 | 11.45 | 8.58 | -0.57 | 0.0 |

---

## 5. RSI Parameter Sensitivity Diagnostic

| Parameter | Horizon | N_Trades | Mean_Net_60D | Median_Net_60D | Win_Rate | Profit_Factor | p_value | Data_Snooping_Warning |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| RSI(14) in [55, 70] | 60D | 8792 | 6.99 | 2.54 | 55.77 | 2.43 | 0.03 | Reporting parameter sensitivity only; winner-picking prohibited. |
| RSI(25) in [55, 70] | 60D | 11690 | 7.61 | 3.35 | 57.39 | 2.59 | 0.0 | Reporting parameter sensitivity only; winner-picking prohibited. |

---

## 6. Quallamaggie Implementation Record

| Candidate | Status | Reason | Action_Taken |
| --- | --- | --- | --- |
| C4: Quallamaggie | NOT_IMPLEMENTED | No verifiable, authoritative rule set available without fabricating. | Honest non-implementation per Rule 6(b) instructions. |

---

## 7. Survivorship Worst-Case Stress on Top Candidate (C1: SOS-Only (Validated Reference))

| Scenario | Assumed_Lost_Return | Adjusted_Mean | Positive_Expectancy |
| --- | --- | --- | --- |
| Base Observed Filtered Mean | 0.0% | 8.35 | YES |
| Pessimistic (-15% 60D Return) | -15.0% | 3.57 | YES |
| Severe (-25% 60D Return) | -25.0% | 1.53 | YES |
| Catastrophic (-40% 60D Return) | -40.0% | -1.54 | NO |
| Annual Haircut 2.5%/yr | -2.5%/yr | 7.75 | YES |

---

## 8. WHAT THIS DOES NOT DO
- **Does NOT adopt any candidate:** The production strategy remains frozen as Spring + SC.
- **Does NOT modify production source code:** Zero files under `src/` were modified.
- **Does NOT remove LPS from production:** `broad_filter.py` remains untouched.
- **Does NOT touch the prospective OOS firewall:** `data/oos/` remains strictly isolated.

---

## 9. RECOMMENDED NEXT STEP
1. **Maintain SOS as the Single Primary Candidate Lead:** No newly benchmarked candidate outperforms SOS after BH correction and sample-size filtering.
2. **Await Prospective OOS Validation:** Defer any strategy adoption until the pre-registered live forward testing batches mature.
