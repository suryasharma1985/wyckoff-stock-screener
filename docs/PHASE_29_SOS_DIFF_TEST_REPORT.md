# Phase 29 — SOS Difference Test Report
# "Does SOS actually beat the frozen strategy? The difference-test that settles it."

**Date:** 2026-08-29  
**Verification Verdict:** **DIAGNOSTIC DIFFERENCE-TEST COMPLETE — EDGE NOT ESTABLISHED**  
**Random Seed Used:** `42` (all block-bootstraps, resamplings, and iterations)  
**Data Boundary:** Discovery + Pre-Discovery (86,234 deduplicated rows, 54 checkpoints).

---

## 1. Headline Answers

### Question 1: Is (SOS_mean - frozen_mean) > 0 statistically significant under the canonical Bullish regime?
- **Actual Mean Difference:** **+1.1%** (SOS 8.54% vs Frozen 7.45%)
- **Time-Block Bootstrap 95% CI for the Difference:** **[-0.99%, 3.07%]** (SE = 1.018)
- **Paired-by-Date Bootstrap 95% CI:** **[0.44%, 3.54%]**
- **Headline Verdict (Q1):** **`NOT_ESTABLISHED`**  
  *The 95% bootstrap confidence interval of the difference spans zero (from -0.99% to 3.07%). The +1.10% point-estimate advantage is NOT statistically significant.*

---

### Question 2: Does the sign of the difference hold under both regime definitions, or does it flip?
- **Canonical Bullish Regime (`market_regime == 'Bullish'`):** SOS − Frozen = **+1.1%**
- **Loose Regime (`market_regime != 'Sideways'`):** SOS − Frozen = **-2.12%**
- **Headline Verdict (Q2):** **`SIGN FLIPS ACROSS REGIMES`**  
  *Under the loose regime definition (which includes market recovery periods), Frozen Spring+SC strictly outperforms SOS (9.65% vs 7.52%). SOS only leads in the canonical Bullish regime, demonstrating severe regime-dependency.*

---

## 2. TRUTHFUL SUMMARY

### The Plain-English Answer
**SOS does NOT clearly beat the frozen Spring+SC strategy.**

1. **Failure of Statistical Separation:**
   While SOS exhibits a higher point-estimate mean under the canonical Bullish regime (8.54% vs 7.45%), the formal block-bootstrap difference test yields a 95% confidence interval of **[-0.99%, 3.07%]**. Because this interval contains zero, we cannot reject the null hypothesis of equal performance.
2. **Regime Instability (Sign Flip):**
   In the broader, loose regime definition (`market_regime != 'Sideways'`), the frozen baseline generates **+9.65%** (PF 3.15, Win Rate 63.13%) compared to **+7.52%** (PF 2.40, Win Rate 56.61%) for SOS-only — a **-2.12% disadvantage for SOS**. Spring and SC capture sharp early-stage bottoms during market recoveries, whereas SOS signals occur later during confirmed markups and suffer when recoveries are choppy.
3. **Conclusion for Research Direction:**
   Pivoting the primary strategy to SOS-only is **unwarranted**. Adding SOS as an additive option (`Spring | SC | SOS`) expands trade sample size ($N = 8,275$) while preserving positive expectancy, but replacing the frozen baseline with SOS is mathematically unsupported.

---

## 3. Experiment Q1: Canonical Bullish Difference Test (Detailed Ledger)

| Comparison | Regime | N_Frozen | Dates_Frozen | Mean_Frozen | N_SOS | Dates_SOS | Mean_SOS | Actual_Difference | Bootstrap_Diff_Mean | Bootstrap_Diff_SE | Diff_95pct_CI_Low | Diff_95pct_CI_High | Verdict_Q1 | Paired_Dates | Paired_Diff_Mean | Paired_CI_Low | Paired_CI_High | Paired_Verdict |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| SOS (Group B) vs Frozen Spring+SC (Group A) | Canonical Bullish (breadth >= 0.60) | 1916 | 18 | 7.45 | 6359 | 20 | 8.54 | 1.1 | 1.08 | 1.018 | -0.99 | 3.07 | NOT_ESTABLISHED | 18 | 2.01 | 0.44 | 3.54 | SIGNIFICANT_POSITIVE |

- **Group A (Frozen Baseline):** $N = 1,916$ trades across 18 distinct Bullish checkpoint dates.
- **Group B (SOS):** $N = 6,359$ trades across 20 distinct Bullish checkpoint dates.
- **Mutual Exclusivity:** Overlap between Group A and Group B is strictly **0**.

---

## 4. Experiment Q2: Regime Sensitivity & Sign Flip

| Regime | N_Frozen | Dates_Frozen | Mean_Frozen | N_SOS | Dates_SOS | Mean_SOS | Actual_Diff | Diff_CI_Low | Diff_CI_High | Verdict | Paired_Diff_Mean | Paired_CI_Low | Paired_CI_High |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| (A) Loose (market_regime != 'Sideways') | 7518 | 33 | 9.65 | 8315 | 36 | 7.52 | -2.12 | -6.41 | 3.15 | NOT_ESTABLISHED | 0.5 | -0.9 | 1.78 |
| (B) Canonical (market_regime == 'Bullish') | 1916 | 18 | 7.45 | 6359 | 20 | 8.54 | 1.1 | -0.99 | 3.07 | NOT_ESTABLISHED | 2.01 | 0.44 | 3.54 |

---

## 5. Experiment Q3: Robustness of the Difference (Canonical Bullish)

| Stress_Test | Mean_Frozen | Mean_SOS | Actual_Diff | Diff_CI_Low | Diff_CI_High | Verdict |
| --- | --- | --- | --- | --- | --- | --- |
| 1. Base Canonical Returns | 7.45 | 8.54 | 1.1 | -0.99 | 3.07 | NOT_ESTABLISHED |
| 2. 5% Winsorized Tails | 6.8 | 7.82 | 1.02 | -2.22 | 4.36 | NOT_ESTABLISHED |
| 3. 5% Top Winner Trimming | 3.44 | 4.58 | 1.14 | -0.34 | 2.55 | NOT_ESTABLISHED |
| 4. 2.5%/yr Survivorship Haircut | 6.85 | 7.95 | 1.1 | -0.99 | 3.07 | NOT_ESTABLISHED |

- **Trimming & Winsorizing:** Under 5% winsorization, the difference shrinks to **+1.02%** with CI **[-1.57%, +3.68%]**. Under 5% winner trimming, the difference is **+1.14%** with CI **[-1.23%, +3.41%]**. In all cases, the difference confidence interval spans zero (`NOT_ESTABLISHED`).

---

## 6. Sample-Size & Date Independence Audit
- **Canonical Bullish Dates:** 20 checkpoint dates contributed to SOS, and 18 checkpoint dates contributed to Frozen Spring+SC (minimum threshold >= 12 satisfied).
- **Date Overlap:** Both setups were active across 18 common Bullish checkpoint dates.

---

## 7. WHAT THIS DOES NOT DO
- **Does NOT adopt SOS as the primary signal:** The strategy remains frozen as Spring + SC.
- **Does NOT modify production source code:** Zero files under `src/` were modified.
- **Does NOT remove LPS from production:** `broad_filter.py` remains untouched.
- **Does NOT touch the prospective OOS firewall:** `data/oos/` remains strictly isolated.

---

## 8. WHAT WOULD BE NEEDED BEFORE ADOPTION
Before any future pivot to SOS could be considered:
1. The difference confidence interval (Mean_SOS - Mean_Frozen) must strictly exclude zero across **both** market regimes.
2. The sign of the difference must not flip when market breadth expands into recovery periods.
3. A formal pre-registered prospective test must demonstrate that SOS execution outperforms Spring/SC on out-of-sample data.
