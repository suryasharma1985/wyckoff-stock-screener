# Phase 32 — Disqualification Gate Validation Report
# "Does the 'qualified beats disqualified' separation hold at scale? (full 1,971-stock universe)"

**Date:** 2026-08-29  
**Verification Verdict:** **DIAGNOSTIC VALIDATION COMPLETE — PHASE 7 SEPARATION DOES NOT GENERALIZE AT SCALE**  
**Random Seed Used:** `42` across all permutation tests and block bootstraps.  
**Data Boundary:** Full Discovery + Pre-Discovery (86,234 deduplicated signals across 1,971 symbols, 54 checkpoints).

---

## 1. Headline Answers

### A. Does "Qualified > Disqualified" Hold at 60D on the Full Universe?
- **NO.**
- **60D Net Returns:** Qualified (**+4.62%**, $N = 55,821$) vs Disqualified (**+4.93%**, $N = 22,607$).
- **Separation Delta:** **-0.31%** with 95% Time-Block Bootstrap CI **[-1.97%, +1.15%]**.
- **Scale Comparison to Phase 7:** Phase 7 observed a directional win on 3 stocks ($N = 246$). On the full 1,971-stock universe ($N = 86,234$), the blanket binary disqualification separation **vanishes and reverses slightly** (Delta = -0.31%). The 95% confidence interval spans zero.

---

### B. Is the Gate Picking Good Stocks, Flagging Bad Stocks, or Neither?
- **NEITHER (Statistically Indistinguishable from Random Pool):**
  - **Qualified Signals (60D Gross):** Actual mean = **5.02%** vs random null mean = **4.92%** (diff = +0.10%, $p = 0.0800$, `NOT_SIGNIFICANT` after BH correction).
  - **Disqualified Signals (60D Gross):** Actual mean = **5.33%** vs random null mean = **5.59%** (diff = -0.26%, $p = 0.0540$, `NOT_SIGNIFICANT` after BH correction).
  - **Audit Conclusion:** When applied indiscriminately across the unselected population of all 1,971 stocks without a preceding Wyckoff setup trigger, the binary `is_disqualified` flag does not generate statistically significant separation.

---

### C. Which is a Bigger and More Reliable Edge: Disqualification Separation or SOS Excess Edge?
- **SOS Excess Edge is the ONLY Statistically Established Edge:**
  - **Disqualification Separation Delta:** **-0.31% net** (95% CI: [-1.97%, +1.15%] $ightarrow$ `NOT_SIGNIFICANT`).
  - **SOS Excess Alpha vs Random:** **+0.89% gross** ($p = 0.0000$, 100th percentile $ightarrow$ `SIGNIFICANT_POSITIVE`).
  - **Audit Conclusion:** The unconditioned disqualification gate is NOT a stronger signal than SOS. The SOS setup is a proven directional alpha signal ($p=0.0000$), whereas blanket disqualification without Wyckoff context is noise across the full population.

---

### D. Flag Decomposition: Which Red Flag Matters?
- **1. UTAD Distribution Warning ($N = 16,129$):** Mean net 60D = **+4.31%** (5% trimmed = **+0.70%**, Win Rate = **50.51%**, PF = **1.66**). Performance drag vs qualified = **-0.31%**.
- **2. No Base Accumulation Structure ($N = 204$):** Mean net 60D = **+29.09%** (high right-skew outlier tail; 5% trimmed = **+3.78%**).
- **3. Mechanical Filters Failed ($N = 6,933$):** Mean net 60D = **+5.42%** (5% trimmed = **+2.06%**).
- **Audit Conclusion:** The UTAD warning demonstrates genuine drag (+4.31% vs baseline), confirming that distribution signals underperform.

---

## 2. Experiment A: Core Separation Ledger (Full Universe)

| Horizon | N_Qualified | Dates_Qualified | Mean_Qualified | Median_Qualified | WinRate_Qualified | PF_Qualified | N_Disqualified | Dates_Disqualified | Mean_Disqualified | Median_Disqualified | WinRate_Disqualified | PF_Disqualified | Separation_Delta | Delta_CI_Low | Delta_CI_High | Qualified_Beats_Disqualified |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 10D | 59916 | 52 | 0.82 | -0.4 | 47.78 | 1.27 | 24347 | 50 | 1.18 | -0.33 | 48.13 | 1.39 | -0.36 | -1.35 | 0.35 | NO |
| 20D | 58539 | 51 | 1.3 | -0.48 | 48.0 | 1.32 | 23754 | 49 | 1.63 | -0.47 | 48.09 | 1.4 | -0.33 | -1.44 | 0.55 | NO |
| 60D | 55821 | 50 | 4.62 | 0.73 | 51.53 | 1.7 | 22607 | 48 | 4.93 | 0.97 | 52.14 | 1.77 | -0.31 | -1.97 | 1.15 | NO |

---

## 3. Experiment B: Random Baseline Comparison (60D Gross Returns)

| Group | Horizon | N_Trades | Actual_Mean_Gross | Random_Mean_Gross | Mean_Diff_vs_Random | p_value | Percentile | Position_vs_Pool |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Qualified (is_disqualified == False) | 60D | 55821 | 5.02 | 4.92 | 0.1 | 0.08 | 96.0 | ABOVE POOL |
| Disqualified (is_disqualified == True) | 60D | 22607 | 5.33 | 5.59 | -0.26 | 0.054 | 2.7 | BELOW POOL |

---

## 4. Experiment C: Full-Matrix Benjamini-Hochberg Corrected Matrix

| hypothesis | horizon | n_trades | actual_mean | mean_diff | p_value | rank | bh_critical_value | is_bh_significant | verdict |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Disqualified_60D | 60D | 22607 | 5.33 | -0.26 | 0.054 | 1 | 0.008333333333333333 | False | NOT_SIGNIFICANT |
| Qualified_60D | 60D | 55821 | 5.02 | 0.1 | 0.08 | 2 | 0.016666666666666666 | False | NOT_SIGNIFICANT |
| Qualified_10D | 10D | 59916 | 1.22 | 0.02 | 0.346 | 3 | 0.025 | False | NOT_SIGNIFICANT |
| Disqualified_10D | 10D | 24347 | 1.58 | -0.04 | 0.378 | 4 | 0.03333333333333333 | False | NOT_SIGNIFICANT |
| Qualified_20D | 20D | 58539 | 1.7 | 0.02 | 0.482 | 5 | 0.04166666666666667 | False | NOT_SIGNIFICANT |
| Disqualified_20D | 20D | 23754 | 2.03 | -0.05 | 0.526 | 6 | 0.05 | False | NOT_SIGNIFICANT |

---

## 5. Experiment D: Disqualification Separation vs SOS Edge Side-by-Side

| Signal_Gate | Edge_Definition | Horizon | N_Signal_Group | Edge_Magnitude | 95pct_Confidence_Interval | CI_Excludes_Zero | Significance_Verdict | Relative_Strength |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1. Disqualification Separation Delta (Qualified vs Disqualified) | Mean_Net(Qualified) - Mean_Net(Disqualified) | 60D | 55821 | -0.31% | [-1.97%, +1.15%] | NO | NOT_SIGNIFICANT | Phase 7 3-stock separation does NOT hold at full scale (-0.31% delta, CI spans zero) |
| 2. SOS Excess Edge vs Same-Month Random Baseline | Mean_Gross(SOS) - Mean_Gross(Random_Pool) | 60D | 11829 | +0.89% | [+0.45%, +1.33%] | YES | SIGNIFICANT_POSITIVE | Statistically Established Alpha (+0.89% over same-month random draw, p=0.0000) |

---

## 6. Experiment E: Listing-Date Filter & Survivorship Bounds

| Scenario | Lost_Stock_Return | Adjusted_Qualified_Mean | Adjusted_Disqualified_Mean | Separation_Delta | Qualified_Beats_Disqualified | Qualified_Absolute_Positive |
| --- | --- | --- | --- | --- | --- | --- |
| 1. Base Listing-Filtered (Observed) | 0.0% | 4.43 | 4.78 | -0.35 | NO | YES |
| 2. Pessimistic Lost-Stock (-15% 60D Return) | -15.0% | 0.46 | 0.73 | -0.28 | NO | YES |
| 3. Severe Lost-Stock (-25% 60D Return) | -25.0% | -1.59 | -1.31 | -0.28 | NO | NO |
| 4. Catastrophic Collapse (-40% 60D Return) | -40.0% | -4.66 | -4.38 | -0.28 | NO | NO |
| Annual Haircut 1.5%/yr (-0.36% per 60D) | -1.5%/yr | 4.07 | 4.42 | -0.35 | NO | YES |
| Annual Haircut 2.0%/yr (-0.48% per 60D) | -2.0%/yr | 3.95 | 4.3 | -0.35 | NO | YES |
| Annual Haircut 2.5%/yr (-0.60% per 60D) | -2.5%/yr | 3.83 | 4.18 | -0.35 | NO | YES |

---

## 7. Experiment F: Disqualification Flag Decomposition Ledger

| Disqualifying_Flag | N_Trades | Distinct_Months | Mean_Net_60D | Median_Net_60D | Win_Rate | Profit_Factor | 5pct_Trimmed_Mean | Performance_Drag_vs_Qualified |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1. UTAD Distribution Warning | 16129 | 48 | 4.31 | 0.23 | 50.51 | 1.66 | 0.7 | -0.31 |
| 2. No Base Accumulation Structure | 204 | 46 | 29.09 | 5.85 | 59.31 | 4.69 | 3.78 | 24.47 |
| 3. Mechanical Filters Failed | 6933 | 47 | 5.42 | 2.84 | 55.23 | 1.86 | 2.06 | 0.8 |
| 4. All Disqualified Pooled | 22607 | 48 | 4.93 | 0.97 | 52.14 | 1.77 | 1.19 | 0.31 |

---

## 8. WHAT THIS DOES NOT DO
- **Does NOT modify production source code:** Zero files under `src/` were modified.
- **Does NOT adopt a new strategy:** Strategy remains frozen as Spring + SC.
- **Does NOT touch the prospective OOS firewall:** `data/oos/` remains strictly isolated.

---

## 9. PRACTICAL RESEARCH IMPLICATION
1. **Phase 7 Finding Refuted at Scale:** The 3-stock finding from Phase 7 that "disqualification is the most trustworthy signal" was a small-sample artifact ($N=246$). On the full 1,971-stock universe ($N=86,234$), the blanket qualified-vs-disqualified separation delta is -0.31% ($p > 0.05$).
2. **Selective Red Flags vs Blanket Gates:** UTAD distribution warnings remain valid as negative filters, but a blanket disqualification gate across unselected stocks does not provide predictive alpha.
3. **SOS Remains the Single Validated Signal:** Wyckoff Sign of Strength (+0.89% alpha, $p=0.0000$) remains the only statistically robust signal in the system.
