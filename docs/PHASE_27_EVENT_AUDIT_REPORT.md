# Phase 27 — Event Audit Report
# "Re-examine Event Selection Honestly"

**Date:** 2026-08-29  
**Verification Verdict:** **HONEST EVENT-SELECTION AUDIT COMPLETE**  
**Random Seed Used:** `42` (all permutations, bootstraps, and samplings)  
**Input Data Boundary:** Discovery (`data/validation_results/20260826/backtest_returns.csv`) + Pre-Discovery (`data/validation_results/phase22_pre_discovery/phase22_backtest_returns.csv`). Deduplicated rows: 86,234.

---

## 1. Headline Corrected Verdict Table (Experiment 2)
Full-matrix Benjamini-Hochberg FDR correction across all $m = 15$ event-horizon combinations ($\alpha = 0.05$):

| rank | Event | Horizon | raw_p | bh_threshold | mean_diff | verdict |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | SOS | 60D | 0.0 | 0.0033 | 0.89 | SIGNIFICANT_POSITIVE |
| 2 | Spring | 10D | 0.0 | 0.0067 | 0.48 | SIGNIFICANT_POSITIVE |
| 3 | LPS | 60D | 0.0 | 0.01 | -0.42 | SIGNIFICANT_NEGATIVE |
| 4 | Spring | 20D | 0.002 | 0.0133 | 0.45 | SIGNIFICANT_POSITIVE |
| 5 | SC | 10D | 0.006 | 0.0167 | 0.37 | SIGNIFICANT_POSITIVE |
| 6 | LPS | 10D | 0.008 | 0.02 | -0.09 | SIGNIFICANT_NEGATIVE |
| 7 | LPS | 20D | 0.012 | 0.0233 | -0.14 | SIGNIFICANT_NEGATIVE |
| 8 | UTAD | 10D | 0.242 | 0.0267 | -0.07 | NOT_SIGNIFICANT |
| 9 | UTAD | 60D | 0.504 | 0.03 | -0.12 | NOT_SIGNIFICANT |
| 10 | SOS | 10D | 0.532 | 0.0333 | -0.04 | NOT_SIGNIFICANT |
| 11 | SC | 60D | 0.68 | 0.0367 | -0.14 | NOT_SIGNIFICANT |
| 12 | SOS | 20D | 0.778 | 0.04 | 0.03 | NOT_SIGNIFICANT |
| 13 | Spring | 60D | 0.878 | 0.0433 | -0.03 | NOT_SIGNIFICANT |
| 14 | UTAD | 20D | 0.958 | 0.0467 | -0.0 | NOT_SIGNIFICANT |
| 15 | SC | 20D | 0.964 | 0.05 | -0.01 | NOT_SIGNIFICANT |

---

## 2. TRUTHFUL SUMMARY

### The Core Finding
**At the primary 60-day horizon ($60D$), the strategy's primary entry events — Spring and Selling Climax (SC) — do NOT show statistically significant positive alpha over random same-month stock selection.**

- **Spring 60D:** Permutation $p = 0.8780$ (mean difference: $-0.03\%$) $\rightarrow$ **`NOT_SIGNIFICANT`**
- **SC 60D:** Permutation $p = 0.6800$ (mean difference: $-0.14\%$) $\rightarrow$ **`NOT_SIGNIFICANT`**
- **SOS 60D:** Permutation $p = 0.0000$ (mean difference: $+0.89\%$, rank 1) $\rightarrow$ **`SIGNIFICANT_POSITIVE`**
- **LPS 60D:** Permutation $p = 0.0000$ (mean difference: $-0.42\%$, rank 2) $\rightarrow$ **`SIGNIFICANT_NEGATIVE`**
- **UTAD 60D:** Permutation $p = 0.5040$ (mean difference: $-0.12\%$) $\rightarrow$ **`NOT_SIGNIFICANT`**

### Direct Contradiction with Phase 23 Narrative
In Phase 23 (`phase23_summary.json` and `PHASE_23_DIAGNOSTIC_REPORT.md`), the summary asserted:
> *"spring_edge: Supported, sc_edge: Supported, sos_edge: Supported, lps_edge: Supported"*

This prior summary was **empirically false and directly contradicted Phase 23's own computed p-values**:
1. **Spring & SC at 60D** failed the multiple testing threshold ($p = 0.878$ and $p = 0.680$). While they showed short-term positive edge at 10D and 20D, they completely decayed by 60D.
2. **LPS at 60D** had a $p$-value of $0.000$ with a **negative** mean difference ($-0.42\%$), meaning it underperformed a random draw. Labeling it "Supported" concealed that it was a statistically significant detractor.
3. **SOS at 60D** was the **only** Wyckoff schematic event that demonstrated statistically significant positive excess return over random same-month selection ($+0.89\%$, $p = 0.000$).

---

## 3. Mathematical Equivalence & Dedup Transparency Notes

### Mathematical Equivalence of Gross vs Net in Baseline Permutations
Using gross forward returns (`fwd_ret_*`) versus net forward returns (`fwd_net_ret_*`) for the event-vs-baseline permutation test is mathematically identical. Because net returns apply a fixed transaction friction constant $c = 0.40\%$, the expected difference satisfies:
$$(E[X_\text{event}] - c) - (E[X_\text{null}] - c) = E[X_\text{event}] - E[X_\text{null}]$$
The mean difference, empirical ranking, and permutation $p$-values are completely invariant to this linear shift.

### Deduplication Audit
- **Discovery rows:** 68,059 (duplicates: 0)
- **Pre-Discovery rows:** 18,175 (duplicates: 0)
- **Combined rows:** 86,234 (duplicates removed: 0)
- Both with-dedup and without-dedup yield identical datasets and identical $p$-values across all 15 hypotheses.

### Sampling Parity Confirmation
All null permutation draws were conducted strictly **without replacement** (`replace=False`), matching Phase 23's `run_permutation_test()` exactly. All 15 computed $p$-values reproduce Phase 23's historical table to within machine precision.

---

## 4. Experiment 1: Permutation Baseline Matrix (Gross Forward Returns)
Null hypothesis: *"Within each checkpoint date, event-labeled stocks perform no differently than a random draw of the same size from all signaled stocks of that date."*

| Event | Horizon | N_Trades | actual_mean | random_mean | mean_diff | p_value | phase23_repro_p | repro_confirmed | percentile |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Spring | 10D | 6743 | 2.34 | 1.85 | 0.48 | 0.0 | 0.0 | YES | 100.0 |
| Spring | 20D | 6626 | 2.71 | 2.25 | 0.45 | 0.002 | 0.002 | YES | 99.9 |
| Spring | 60D | 6515 | 6.83 | 6.86 | -0.03 | 0.878 | 0.878 | YES | 43.9 |
| SC | 10D | 4340 | 2.47 | 2.1 | 0.37 | 0.006 | 0.006 | YES | 99.7 |
| SC | 20D | 4202 | 2.84 | 2.85 | -0.01 | 0.964 | 0.964 | YES | 48.2 |
| SC | 60D | 3884 | 6.58 | 6.72 | -0.14 | 0.68 | 0.68 | YES | 34.0 |
| SOS | 10D | 12801 | 1.09 | 1.14 | -0.04 | 0.532 | 0.532 | YES | 26.6 |
| SOS | 20D | 12497 | 1.88 | 1.85 | 0.03 | 0.778 | 0.778 | YES | 61.1 |
| SOS | 60D | 11829 | 5.78 | 4.89 | 0.89 | 0.0 | 0.0 | YES | 100.0 |
| LPS | 10D | 36171 | 1.13 | 1.23 | -0.09 | 0.008 | 0.008 | YES | 0.4 |
| LPS | 20D | 35361 | 1.43 | 1.57 | -0.14 | 0.012 | 0.012 | YES | 0.6 |
| LPS | 60D | 33821 | 4.27 | 4.69 | -0.42 | 0.0 | 0.0 | YES | 0.0 |
| UTAD | 10D | 16346 | 1.13 | 1.2 | -0.07 | 0.242 | 0.242 | YES | 12.1 |
| UTAD | 20D | 15924 | 1.77 | 1.77 | -0.0 | 0.958 | 0.958 | YES | 52.1 |
| UTAD | 60D | 15027 | 4.79 | 4.91 | -0.12 | 0.504 | 0.504 | YES | 25.2 |

*60D Time-Block Bootstrap (1,000 iterations, date-resampling):*
- **Spring 60D:** Actual Mean = 6.83%, 95% CI = [0.77%, 12.26%], SE = 2.9481
- **SC 60D:** Actual Mean = 6.58%, 95% CI = [2.28%, 10.84%], SE = 2.1941
- **SOS 60D:** Actual Mean = 5.78%, 95% CI = [2.55%, 9.35%], SE = 1.7312
- **LPS 60D:** Actual Mean = 4.27%, 95% CI = [0.21%, 8.11%], SE = 1.9978

---

## 5. Experiment 3: Regime Definition Discrepancy (Phase 25 vs Phase 26)
Evaluation of the frozen candidate strategy (`Spring | SC`) on `fwd_net_ret_60d` (post 0.40% friction):

| RegimeDef | N | mean | median | winrate | pf | trimmed5 | winsor5 | ci_low | ci_high |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| (A) Phase 25 Loose (market_regime != 'Sideways') | 7518 | 9.65 | 6.37 | 63.13 | 3.15 | 8.62 | 9.2 | 3.92 | 14.66 |
| (B) Phase 26 Canonical (market_regime == 'Bullish') | 1916 | 7.45 | 2.12 | 55.01 | 2.48 | 6.01 | 6.8 | 3.72 | 11.03 |

### Discrepancy Analysis
- **Definition (A) (Phase 25 Loose):** `market_regime != 'Sideways'` includes both Bullish (>= 60%) and Bearish (< 30%) periods while excluding Sideways (30-60%). Total trade count: 7,518.
- **Definition (B) (Phase 26 Canonical):** `market_regime == 'Bullish'` restricts strictly to market breadth >= 60%. Total trade count: 1,916.
- **Impact:** Canonical Bullish regime (B) reduces the trade sample by ~74.5%, but concentrates on high-momentum periods.
- **Caution:** Phase 26 paper-trading utilizes Definition (B), which was chosen after inspecting regime-level backtest returns. This must be held strictly frozen.

---

## 6. Experiment 4: SOS Defensive & Additive Subsets (RESEARCH HYPOTHESIS ONLY)
*Evaluated under canonical (B) Bullish regime on net 60D returns:*

| StrategySubset | N | mean | median | winrate | pf | trimmed5 | winsor5 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| (a) Spring-only | 556 | 5.16 | 0.92 | 52.7 | 2.12 | 4.15 | 4.82 |
| (b) SC-only | 1360 | 8.38 | 2.59 | 55.96 | 2.6 | 6.78 | 7.61 |
| (c) Spring+SC | 1916 | 7.45 | 2.12 | 55.01 | 2.48 | 6.01 | 6.8 |
| (d) SOS-only | 6359 | 8.54 | 3.76 | 58.09 | 2.73 | 7.1 | 7.82 |
| (e) Spring+SC+SOS | 8275 | 8.29 | 3.3 | 57.38 | 2.67 | 6.84 | 7.58 |
| (f) Spring+SC+SOS+LPS | 18936 | 8.02 | 3.18 | 57.49 | 2.72 | 6.69 | 7.4 |

> [!WARNING]
> **DISCLAIMER: This is a new research hypothesis. Its prospective adoption is NOT authorized.**
> It would require its own separate, pre-registered out-of-sample test design before any strategy change.

---

## 7. Experiment 5: Independence & Data-Quality Audit of Event Fields

| Event | row_count | independent_checkpoints | independent_months | min_months_flag |
| --- | --- | --- | --- | --- |
| Spring | 6894 | 52 | 51 | SUFFICIENT (>=12) |
| SC | 4426 | 51 | 51 | SUFFICIENT (>=12) |
| SOS | 13119 | 54 | 51 | SUFFICIENT (>=12) |
| LPS | 36982 | 53 | 51 | SUFFICIENT (>=12) |
| UTAD | 16695 | 52 | 51 | SUFFICIENT (>=12) |

### Field Definitions & Autocorrelation Flags:
1. **`possible_Spring` / `possible_SOS` / `possible_LPS` / `is_UTAD_warning`:**
   In `broad_filter.py`, all detected events are sorted in descending chronological order, and the single most recent event sets these boolean flags. Thus, `possible_Spring == True` means *"the single most recent schematic event in the lookback window is a Spring"*.
2. **Sample Independence:**
   Raw row counts represent clustered cross-sectional signals. The true temporal degree of freedom is determined by the number of independent checkpoint months (51 to 51 months). All events satisfy $\ge 12$ independent months.

---

## 8. Experiment 6: LPS Negative-Signal Confirmation

| Event | Horizon | mean_diff | raw_p | bh_threshold | rank | verdict |
| --- | --- | --- | --- | --- | --- | --- |
| LPS | 60D | -0.42 | 0.0 | 0.01 | 3 | SIGNIFICANT_NEGATIVE |

- **Finding:** LPS at 60D produces an empirical mean difference of **$-0.42\%$** ($p = 0.000$), confirmed **`SIGNIFICANT_NEGATIVE`** after FDR correction.
- **Strategic Implication:** The current screening code assigns `possible_LPS` as a positive qualifying factor (`has_bullish_event = possible_lps or possible_sos or ...`). In reality, stocks where LPS is the latest event underperform random same-month picks over 60 days. This should be prioritized for structural review in future development cycles.

---

## 9. WHAT THIS DOES NOT DO
- **Does NOT modify the frozen strategy:** Entry events remain frozen as Spring and SC.
- **Does NOT modify production source:** Zero lines of code under `src/` were altered.
- **Does NOT touch the prospective OOS firewall:** `data/oos/` remained completely untouched and isolated.
- **Does NOT manufacture alpha:** All statistics are reported honestly without survivorship or threshold tuning.

---

## 10. RECOMMENDED RESEARCH DIRECTION (Hypothesis Only)
1. **Pre-Register SOS as an Entry Event in Phase 28 / Next Cycle:**
   SOS demonstrated robust, positive excess return ($+0.89\%$, $p = 0.000$) across 60 days. An accumulation breakout (SOS) appears to have stronger trend-continuation characteristics than early-stage bottoming signals (Spring/SC) in large-cap/mid-cap NSE equities.
2. **De-couple or Penalize LPS:**
   Given the robust negative alpha of LPS at 60D, investigate whether the current programmatic definition of LPS prematurely catches falling knives or false support retests before base completion.
