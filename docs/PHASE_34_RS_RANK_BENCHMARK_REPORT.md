# Phase 34 -- RS-Rank Benchmark Report
# "Does a cross-sectional Relative Strength rank close the Minervini RS-Rating gap and add alpha over SOS?"

**Date:** 2026-08-30
**Verification Verdict:** **B. PROMISING BUT UNRESOLVED -- C6c (SOS + RS_short(63d)>=70) beats C1 after BH correction AND survives a direct difference-test (Section 8), the first candidate to do so since SOS itself. Regime-robustness (loose vs canonical) and sub-period stability are the required next check before any adoption consideration.**
**Random Seed Used:** `42` across all permutation tests and block bootstraps.
**RS Thresholds (pre-registered before execution):** [70.0, 90.0]

---

> [!CAUTION]
> ### 1. MANDATORY HONESTY STATEMENT & BENCHMARKING BOUNDS
> - **Zero Winner-Picking:** RS thresholds (70, 90) were fixed before this script ran; both are reported regardless of outcome.
> - **Zero Strategy Adoption:** Production source code under `src/` and the frozen strategy remain 100% untouched.
> - **Reference Baseline:** All RS-augmented candidates are measured against **C1 (SOS-Only + Bullish)**, the validated reference from Phases 27-32.
> - **Methodology fix vs Phase 31:** RS rank here is computed cross-sectionally against the FULL 1,971-stock universe on each of the 54 checkpoint dates (not just signal-firing stocks) -- this is what Phase 31 explicitly flagged as omitted ("Cross-sectional RS Rating omitted due to universe-wide dynamic calculation limits").

---

## 2. Headline Answer

### Does RS-Rank Add Incremental Alpha Over Validated SOS (C1)?
- **YES, PROVISIONALLY -> C6c: SOS + RS_short(63d)>=70**, and unlike the Phase 28 "SOS beats frozen" claim (which was later corrected in Phase 29 for resting on overlapping confidence intervals with no direct difference-test), this result **was checked against that exact trap in Phase 34b (Section 8) and survived it**: a direct paired-by-date difference test between the RS>=70 subset and its own RS<70 complement excludes zero under both unpaired bootstrap, paired-by-date bootstrap, AND a within-date label-permutation test (p=0.0000).
- Best candidate evaluated: **C6c: SOS + RS_short(63d)>=70** (60D Net Mean = 10.27% vs C1's 8.35%; N=3,169, Distinct_Months=18 vs C1's own 20).
- **Important negative finding (preserved, not buried):** The longer-horizon RS composite filters (C6a, C6b -- the IBD-style 3/6/9/12-month blend) are considerably WORSE than plain SOS (mean 3.88-4.37% vs 8.35%, win rate below 50%, median negative) and collapse the sample to only 9 distinct months. Requiring a long-horizon RS blend on top of SOS actively hurts; only the short-horizon (63-trading-day, ~3-month) RS filter helps. This should not be read as "RS rank is validated" -- it is specifically the short-horizon variant, at the pre-registered >=70 threshold, layered on SOS.

### Data Coverage Honesty
- Missing/unreadable cache symbols: 0
- Signal-date x symbol pairs with insufficient history for the 252-bar composite: 20,721
- Signal-date x symbol pairs with insufficient history for the 63-bar short RS: 30,161

---

## 3. Benjamini-Hochberg Full-Matrix Corrected Ranking (Listing-Filtered, m=15)

| candidate | horizon | n_trades | mean_net | mean_diff | p_value | rank | bh_critical_value | is_bh_significant | verdict |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| C1: SOS-Only (Validated Reference, no RS) | 60D | 6286 | 8.35 | 1.21 | 0.0 | 1 | 0.0033333333333333335 | True | SIGNIFICANT_POSITIVE |
| C6a: SOS + RS_composite>=70 | 60D | 1443 | 3.88 | 1.9 | 0.0 | 2 | 0.006666666666666667 | True | SIGNIFICANT_POSITIVE |
| C6d: RS_composite>=90 ALONE (no Wyckoff event) | 60D | 1284 | 4.37 | 2.01 | 0.0 | 3 | 0.010000000000000002 | True | SIGNIFICANT_POSITIVE |
| C6c: SOS + RS_short(63d)>=70 | 60D | 3169 | 10.27 | 2.74 | 0.0 | 4 | 0.013333333333333334 | True | SIGNIFICANT_POSITIVE |
| C6b: SOS + RS_composite>=90 | 60D | 577 | 4.35 | 2.09 | 0.014 | 5 | 0.016666666666666666 | True | SIGNIFICANT_POSITIVE |
| C6a: SOS + RS_composite>=70 | 20D | 1611 | 1.21 | 0.65 | 0.024 | 6 | 0.020000000000000004 | False | NOT_SIGNIFICANT |
| C6c: SOS + RS_short(63d)>=70 | 20D | 3379 | 3.09 | 0.49 | 0.034 | 7 | 0.023333333333333334 | False | NOT_SIGNIFICANT |
| C6d: RS_composite>=90 ALONE (no Wyckoff event) | 20D | 1460 | 1.23 | 0.59 | 0.052 | 8 | 0.02666666666666667 | False | NOT_SIGNIFICANT |
| C1: SOS-Only (Validated Reference, no RS) | 10D | 6602 | 1.41 | -0.12 | 0.208 | 9 | 0.03 | False | NOT_SIGNIFICANT |
| C6a: SOS + RS_composite>=70 | 10D | 1611 | -0.1 | 0.21 | 0.276 | 10 | 0.03333333333333333 | False | NOT_SIGNIFICANT |
| C6b: SOS + RS_composite>=90 | 20D | 646 | 1.02 | 0.48 | 0.306 | 11 | 0.03666666666666667 | False | NOT_SIGNIFICANT |
| C6d: RS_composite>=90 ALONE (no Wyckoff event) | 10D | 1460 | -0.11 | 0.16 | 0.438 | 12 | 0.04000000000000001 | False | NOT_SIGNIFICANT |
| C6c: SOS + RS_short(63d)>=70 | 10D | 3379 | 1.34 | 0.08 | 0.568 | 13 | 0.043333333333333335 | False | NOT_SIGNIFICANT |
| C1: SOS-Only (Validated Reference, no RS) | 20D | 6602 | 2.64 | 0.08 | 0.592 | 14 | 0.04666666666666667 | False | NOT_SIGNIFICANT |
| C6b: SOS + RS_composite>=90 | 10D | 646 | -0.27 | 0.09 | 0.774 | 15 | 0.05 | False | NOT_SIGNIFICANT |

---

## 4. Comprehensive Candidate Metrics Ledger (Listing-Filtered Primary)

| Candidate | Horizon | N_Trades | Distinct_Months | Mean_Net | Median_Net | Win_Rate | Profit_Factor | Trimmed5 | Winsor5 | Bootstrap_CI_Low | Bootstrap_CI_High | Random_Mean_Gross | Mean_Diff_Gross | p_value_raw |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| C1: SOS-Only (Validated Reference, no RS) | 10D | 6602 | 20 | 1.41 | 0.24 | 51.29 | 1.53 | 0.01 | 1.27 | 0.12 | 2.62 | 1.93 | -0.12 | 0.208 |
| C1: SOS-Only (Validated Reference, no RS) | 20D | 6602 | 20 | 2.64 | 0.61 | 52.53 | 1.76 | 0.68 | 2.46 | 0.95 | 4.24 | 2.96 | 0.08 | 0.592 |
| C1: SOS-Only (Validated Reference, no RS) | 60D | 6286 | 20 | 8.35 | 3.66 | 57.92 | 2.69 | 4.47 | 7.66 | 4.33 | 12.56 | 7.54 | 1.21 | 0.0 |
| C6a: SOS + RS_composite>=70 | 10D | 1611 | 9 | -0.1 | -1.21 | 43.33 | 0.97 | -1.51 | -0.24 | -1.57 | 1.32 | 0.09 | 0.21 | 0.276 |
| C6a: SOS + RS_composite>=70 | 20D | 1611 | 9 | 1.21 | -0.66 | 48.29 | 1.27 | -0.8 | 1.12 | -0.67 | 3.08 | 0.97 | 0.65 | 0.024 |
| C6a: SOS + RS_composite>=70 | 60D | 1443 | 9 | 3.88 | -0.47 | 49.13 | 1.56 | 0.21 | 3.47 | 0.17 | 8.34 | 2.38 | 1.9 | 0.0 |
| C6b: SOS + RS_composite>=90 | 10D | 646 | 9 | -0.27 | -1.58 | 43.34 | 0.93 | -1.72 | -0.41 | -1.9 | 1.27 | 0.04 | 0.09 | 0.774 |
| C6b: SOS + RS_composite>=90 | 20D | 646 | 9 | 1.02 | -0.97 | 46.9 | 1.2 | -1.12 | 0.95 | -1.11 | 3.05 | 0.94 | 0.48 | 0.306 |
| C6b: SOS + RS_composite>=90 | 60D | 577 | 9 | 4.35 | 0.29 | 50.43 | 1.57 | 0.56 | 4.3 | -0.24 | 9.38 | 2.67 | 2.09 | 0.014 |
| C6c: SOS + RS_short(63d)>=70 | 10D | 3379 | 18 | 1.34 | 0.0 | 49.96 | 1.45 | -0.15 | 1.19 | -0.04 | 2.55 | 1.67 | 0.08 | 0.568 |
| C6c: SOS + RS_short(63d)>=70 | 20D | 3379 | 18 | 3.09 | 0.89 | 53.18 | 1.83 | 0.98 | 2.93 | 1.22 | 5.0 | 2.99 | 0.49 | 0.034 |
| C6c: SOS + RS_short(63d)>=70 | 60D | 3169 | 18 | 10.27 | 4.92 | 59.64 | 3.02 | 5.94 | 9.4 | 5.22 | 15.02 | 7.93 | 2.74 | 0.0 |
| C6d: RS_composite>=90 ALONE (no Wyckoff event) | 10D | 1460 | 9 | -0.11 | -1.37 | 43.77 | 0.97 | -1.57 | -0.3 | -1.63 | 1.15 | 0.12 | 0.16 | 0.438 |
| C6d: RS_composite>=90 ALONE (no Wyckoff event) | 20D | 1460 | 9 | 1.23 | -0.89 | 47.05 | 1.25 | -0.87 | 1.08 | -0.85 | 3.02 | 1.04 | 0.59 | 0.052 |
| C6d: RS_composite>=90 ALONE (no Wyckoff event) | 60D | 1284 | 9 | 4.37 | -0.7 | 48.75 | 1.55 | 0.43 | 4.11 | -0.05 | 9.55 | 2.76 | 2.01 | 0.0 |

---

## 5. Survivorship Worst-Case Stress on Top Candidate (C6c: SOS + RS_short(63d)>=70)

| Scenario | Assumed_Lost_Return | Adjusted_Mean | Positive_Expectancy |
| --- | --- | --- | --- |
| Base Observed Filtered Mean | 0.0% | 10.27 | YES |
| Pessimistic (-15% 60D Return) | -15.0% | 5.1 | YES |
| Severe (-25% 60D Return) | -25.0% | 3.06 | YES |
| Catastrophic (-40% 60D Return) | -40.0% | -0.01 | NO |

---

## 8. Phase 34b -- Direct Difference-Test Addendum (the check Phase 28 skipped)

**Why this section exists:** C6c's 60D bootstrap CI [5.22%, 15.02%] overlaps heavily with C1's own CI [4.33%, 12.56%]. Reporting the point-estimate gap (10.27% vs 8.35%) without a direct test would repeat the exact mistake Phase 28 made claiming "SOS beats frozen" -- later corrected in Phase 29. Because C6c is a strict SUBSET of C1 (SOS+Bullish+RS>=70 vs SOS+Bullish alone), the scientifically correct test is a direct comparison of the RS>=70 subset against its own RS<70 complement (both still SOS+Bullish), not a comparison of two overlapping CIs against a random-pool baseline. Script: `scripts/run_phase34b_rs_diff_test.py`.

| Metric | Group A (SOS+RS>=70) | Group B (SOS+RS<70, complement) |
| --- | --- | --- |
| N | 3,169 | 2,611 |
| Mean (60D net) | 10.27% | 6.14% |
| Median (60D net) | 4.92% | 2.43% |

- **Raw mean difference (A-B):** +4.14%
- **Unpaired bootstrap CI on the difference:** [+2.73%, +5.57%] -- EXCLUDES 0 -> SIGNIFICANT
- **Paired-by-date block-bootstrap CI on the difference:** [+2.36%, +6.08%] -- EXCLUDES 0 -> SIGNIFICANT (17 common checkpoint months)
- **Within-date label-permutation test:** p = 0.0000 -> SIGNIFICANT

**Honest caveats (do not skip):**
- **Independence base is thin:** only 17-18 distinct months carry this comparison (both are already restricted to the "canonical Bullish" regime, same constraint C1 itself already carries at 20 months -- this is not a new weakness introduced by RS, it is inherited from the existing regime filter, but it is still a small number of effectively-independent time clusters and the result has NOT been checked against the "loose" (not-Sideways) regime definition the way Phase 29 checked SOS itself (where the sign flipped between regimes). **This regime-robustness check is the required next step before any adoption.**
- **Tail dependence exists but is milder than usual for this project:** trimming the top 5% of winners still leaves C6c (5.94%) above C1's own trimmed mean (4.47%), and winsorizing leaves C6c (9.40%) above C1's winsorized mean (7.66%) -- the edge does not evaporate under the standard tail-robustness check the way several past candidates did.
- **Survivorship worst-case** (Section 5): still positive expectancy through a -25% catastrophic lost-stock assumption; only flips negative at the most extreme -40% scenario -- the same fragility pattern every other candidate in this project (including SOS itself) already shows.

**Verdict for this addendum:** the RS-short(63d)>=70 overlay on SOS is the first candidate since SOS itself that survives a formal head-to-head difference test against the established baseline. It is NOT yet validated to adoption standard -- regime robustness (loose vs canonical) and a look at whether it holds in the pre-discovery vs discovery sub-periods separately are the required Phase 34c follow-ups per this project's standing protocol.

---

## 6. WHAT THIS DOES NOT DO
- **Does NOT adopt any candidate:** The production strategy remains frozen as Spring + SC; this is diagnostic research only.
- **Does NOT modify production source code:** Zero files under `src/` were modified.
- **Does NOT touch the prospective OOS firewall:** `data/oos/` remains strictly isolated.
- **Does NOT introduce a Nifty benchmark series:** No new external data was downloaded; RS is computed relative to the existing screened universe (this is also how IBD's own RS Rating is defined -- percentile vs all stocks, not vs a single index).

---

## 7. RECOMMENDED NEXT STEP
1. **Phase 34c (not yet designed/run): regime-robustness check.** Re-run the C6c vs complement difference test under the "loose" (not-Sideways) regime definition, matching how Phase 29 discovered SOS itself flips sign across regime definitions. Do NOT adopt C6c until this is checked.
2. Check sub-period stability: does the +4.14% (A-B) difference hold separately in the discovery (Jun 2023-Aug 2026) and pre-discovery (Jun 2022-May 2023) windows, or is it concentrated in one?
3. Operator decision required before any adoption regardless of (1)-(2): this is still historical/backtested evidence, not prospective OOS evidence. The live prospective firewall (`data/oos/`) remains the only bias-free validator per standing project policy.
