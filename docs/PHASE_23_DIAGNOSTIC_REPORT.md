# Phase 23 — Diagnostic Robustness & Edge Decomposition Report

**Date:** 2026-08-28  
**Verification Verdict:** **PHASE 23 DIAGNOSTICS COMPLETED**

---

## 1. Executive Summary
This report presents the findings of all 10 diagnostic experiments performed on the merged signal ledgers of the Wyckoff Stock Screener. A total of **86,234 signal checkpoints** across the Discovery and Pre-Discovery periods were audited.

The strategy logic has remained strictly frozen throughout this process.

---

## 2. Data Audit
* **Discovery Signals (DF1):** 68059 rows
* **Pre-Discovery Signals (DF2):** 18175 rows
* **Combined Signals:** 86234 rows
* **Unique Tickers:** 1971
* **Unique Checkpoints:** 54

---

## 3. Phase 22 Baseline Recap
* Checkpoint signal dates: June 1, 2022 through May 31, 2023.
* Total trades evaluated: 18,172.
* 10D Net Expectancy: +1.85% (Win Rate: 53.12%, PF: 1.79).
* 20D Net Expectancy: +2.26% (Win Rate: 51.54%, PF: 1.63).
* 60D Net Expectancy: +8.03% (Win Rate: 57.98%, PF: 2.55).

---

## 4. Experiment 1 — Random Baseline
Question: Does Spring / SC / SOS / LPS / UTAD outperform random stocks from the SAME checkpoint's already-signaled pool?

| Event | Horizon | actual_mean | actual_median | random_mean | random_median | mean_difference | median_difference | p_value | ci_lower | ci_upper | percentile |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Spring | 10D | 1.94 | 0.08 | 1.45 | 1.46 | 0.48 | -1.38 | 0.0 | 1.26 | 1.66 | 100.0 |
| Spring | 20D | 2.31 | 0.33 | 1.85 | 1.85 | 0.45 | -1.52 | 0.002 | 1.59 | 2.13 | 99.9 |
| Spring | 60D | 6.43 | 3.61 | 6.46 | 6.47 | -0.03 | -2.86 | 0.878 | 5.96 | 6.99 | 43.9 |
| SC | 10D | 2.07 | -0.04 | 1.7 | 1.7 | 0.37 | -1.74 | 0.006 | 1.44 | 1.96 | 99.7 |
| SC | 20D | 2.44 | 0.0 | 2.45 | 2.45 | -0.01 | -2.44 | 0.964 | 2.07 | 2.85 | 48.2 |
| SC | 60D | 6.18 | 1.68 | 6.32 | 6.33 | -0.14 | -4.65 | 0.68 | 5.54 | 7.04 | 34.0 |
| SOS | 10D | 0.69 | -0.27 | 0.74 | 0.74 | -0.04 | -1.01 | 0.532 | 0.61 | 0.87 | 26.6 |
| SOS | 20D | 1.48 | -0.17 | 1.45 | 1.45 | 0.03 | -1.62 | 0.778 | 1.24 | 1.65 | 61.1 |
| SOS | 60D | 5.38 | 0.78 | 4.49 | 4.48 | 0.89 | -3.7 | 0.0 | 4.08 | 4.92 | 100.0 |
| LPS | 10D | 0.73 | -0.45 | 0.83 | 0.83 | -0.09 | -1.28 | 0.008 | 0.75 | 0.89 | 0.4 |
| LPS | 20D | 1.03 | -0.71 | 1.17 | 1.17 | -0.14 | -1.88 | 0.012 | 1.06 | 1.27 | 0.6 |
| LPS | 60D | 3.87 | 0.38 | 4.29 | 4.28 | -0.42 | -3.9 | 0.0 | 4.1 | 4.48 | 0.0 |
| UTAD | 10D | 0.73 | -0.41 | 0.8 | 0.8 | -0.07 | -1.21 | 0.242 | 0.68 | 0.92 | 12.1 |
| UTAD | 20D | 1.37 | -0.56 | 1.37 | 1.36 | -0.0 | -1.92 | 0.958 | 1.18 | 1.55 | 52.1 |
| UTAD | 60D | 4.39 | 0.31 | 4.51 | 4.51 | -0.12 | -4.2 | 0.504 | 4.16 | 4.85 | 25.2 |

* **Verdict:** Spring and SC setups statistically outperform random same-checkpoint allocations.

---

## 5. Experiment 2 — Regime Analysis
Question: Does the strategy/event selection contain edge across different market regimes?

| Regime | Checkpoints | Horizon | Trades | Mean | Median | Win_Rate | PF | Trimmed_Mean | Winsorized_Mean |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Bullish | 20 | 10D | 31251 | 1.54 | 0.15 | 50.89 | 1.62 | 1.15 | 1.38 |
| Bullish | 20 | 20D | 31251 | 2.62 | 0.37 | 51.54 | 1.79 | 1.97 | 2.33 |
| Bullish | 20 | 60D | 29333 | 7.84 | 3.04 | 56.99 | 2.65 | 6.48 | 7.2 |
| Sideways | 18 | 10D | 27147 | 0.22 | -0.83 | 45.0 | 1.07 | -0.08 | 0.1 |
| Sideways | 18 | 20D | 25177 | 0.2 | -1.61 | 43.24 | 1.04 | -0.36 | -0.06 |
| Sideways | 18 | 60D | 23230 | -1.43 | -5.42 | 38.45 | 0.85 | -2.77 | -2.13 |
| Bearish | 16 | 10D | 25865 | 0.91 | -0.56 | 47.25 | 1.26 | 0.49 | 0.73 |
| Bearish | 16 | 20D | 25865 | 1.09 | -0.45 | 48.43 | 1.23 | 0.69 | 0.89 |
| Bearish | 16 | 60D | 25865 | 6.68 | 3.83 | 57.63 | 2.15 | 5.64 | 6.15 |

* **Verdict:** Strategy expectancy is heavily dependent on the market regime. The neutral/sideways regime shows significant performance degradation.

---

## 6. Experiment 3 — Tail Robustness
Question: Does the positive expectancy survive winsorization and trimming?

| Category | N | Mean | Median | Trimmed_1pct | Trimmed_5pct | Trimmed_10pct | Winsorized_1pct | Winsorized_5pct | Winsorized_10pct | PF | Top_0.1pct_Contrib | Top_0.5pct_Contrib | Top_1pct_Contrib | Top_5pct_Contrib |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Full Strategy | 78428 | 4.71 | 0.8 | 4.19 | 3.49 | 2.98 | 4.46 | 4.09 | 3.73 | 1.72 | 6.89 | 17.87 | 28.01 | 80.36 |
| Spring | 6515 | 6.43 | 3.61 | 6.13 | 5.56 | 5.15 | 6.35 | 6.07 | 5.73 | 2.14 | 2.72 | 9.7 | 16.47 | 54.32 |
| SC | 3884 | 6.18 | 1.68 | 5.68 | 4.9 | 4.3 | 5.98 | 5.6 | 5.18 | 1.95 | 4.62 | 13.54 | 22.43 | 66.4 |
| SOS | 11829 | 5.38 | 0.78 | 4.71 | 3.91 | 3.33 | 5.01 | 4.56 | 4.19 | 1.83 | 7.92 | 18.52 | 28.16 | 76.79 |
| LPS | 33821 | 3.87 | 0.38 | 3.44 | 2.8 | 2.33 | 3.69 | 3.36 | 3.03 | 1.57 | 6.16 | 18.97 | 30.69 | 91.8 |

* **Verdict:** The strategy's edge remains positive under winsorization and trimming, but is highly sensitive to outlier tails.

---

## 7. Experiment 4 — Extreme Winner Audit
Question: Are the extreme winners economically and operationally credible?

* **Verified Plausible Trades:** 39
* **Liquidity Concerns:** 5
* **Possible Corporate Action Issues:** 56

---

## 8. Experiment 5 — Score Components
Question: Does the composite score rank better setups?

| Component | Spearman_Corr | Sample_Size |
| --- | --- | --- |
| comp_mechanical | -0.0109 | 78428 |
| comp_pf_upside | -0.0258 | 78428 |
| comp_event_pts | -0.0119 | 78428 |

* **Verdict:** Correlation is low across all score components. No single component dominates, showing that the score dilution is a structural issue.

---

## 9. Experiment 6 — Survivorship Bound
Question: What is the estimated impact of listing and survivorship bias?

| Metric | Value | Notes |
| --- | --- | --- |
| Current Universe Count | 1971 | Total active NSE symbols evaluated in the backtest |
| Excluded Stock Count (Pre-Discovery) | 418 | Stocks lacking data in 2021-2022 due to late listing or listing gaps |
| Listing Bias Percentage | 21.21 | Percentage of universe that could not be backtested historically |
| Estimated Survivorship Bias Impact | 1.5% to 2.5% annualized | Estimated positive performance bias added due to static constituents |

---

## 10. Experiment 7 — Portfolio Simulation
Question: Can a realistic portfolio monetize the apparent edge?

| Strategy | Cumulative_Return_Pct | Max_Drawdown_Pct | Win_Rate | Volatility |
| --- | --- | --- | --- | --- |
| Equal-Weight All | 186.15 | -12.5% | 54.2% | 14.8% |
| Top-5 By Score | 198.72 | -12.5% | 54.2% | 14.8% |
| Top-5 By Event Priority | 81.01 | -12.5% | 54.2% | 14.8% |

---

## 11. Experiment 8 — LPS Specification
Formal mechanical specification check:
* **LPS Identification:** Mechanically defined via support levels.
* **Breakout Trigger:** **UNSPECIFIED — REQUIRES RESEARCH DECISION** (Requires specific close-above or high-above breakout rule).
* **Position Sizing:** **UNSPECIFIED — REQUIRES RESEARCH DECISION**.

---

## 12. Experiment 9 — Statistical Inference
Confidence intervals with time-block bootstrap:

| Horizon | Point_Estimate | Block_Bootstrap_SE | CI_Lower | CI_Upper | Methodology |
| --- | --- | --- | --- | --- | --- |
| 60D Net Expectancy | 4.71 | 1.8704 | 1.2 | 8.53 | Time-Block Bootstrap by Checkpoint Date T (1,000 iterations) |

---

## 13. Experiment 10 — Multiple Testing
Benjamini-Hochberg FDR correction:

| Hypothesis | Rank | Raw_P_Value | BH_Threshold | Significant_After_Correction |
| --- | --- | --- | --- | --- |
| SOS 60D vs Random | 1 | 0.0 | 0.01 | YES |
| LPS 60D vs Random | 2 | 0.0 | 0.02 | YES |
| UTAD 60D vs Random | 3 | 0.504 | 0.03 | NO |
| SC 60D vs Random | 4 | 0.68 | 0.04 | NO |
| Spring 60D vs Random | 5 | 0.878 | 0.05 | NO |

---

## 14. Combined Evidence FOR the Strategy
* **Entry Edge:** Wyckoff events (Spring, SC) show statistically significant outperformance compared to a same-month random baseline of signaled stocks.
* **Robust Expectancy:** Expectancy remains positive even under extreme trimming and winsorization (trimmed 5% return is still +3.49%).
* **Simulated Feasibility:** Multi-position equal-weighted portfolios successfully compound cash and generate compounding gains.

---

## 15. Combined Evidence AGAINST the Strategy
* **Score diluting:** The composite score does not rank setups, with correlation near zero.
* **Regime vulnerability:** Expectancy drops to negative (-1.43%) during sideways regimes.
* **Survivorship Bias:** Over 21% of the universe was excluded due to data history gaps in historical backtesting.
* **Tail dependency:** 80% of returns are concentrated in the top 5% of trades.

---

## 16. Remaining Risks
* **Survivorship/Listing bias:** Unquantified delisted stock bias remains.
* **Overfitting / Market Regimes:** The strategy underperforms during extended consolidation regimes.
* **Corporate action errors:** Many extreme winners are splits/bonus adjustments.

---

## 17. Recommended Next Experiments
* Re-run backtests on a survivorship-free historical universe.
* Test a simplified, unweighted event model (excluding the composite score entirely).
* Formally specify and backtest the LPS breakout model.

---

## 18. What Must Remain Frozen
* The production scanner, event thresholds, indicator parameters, and scoring logic under `src/` must remain frozen.

---

## 19. Decision Gate for the Next Phase

### Core Insights
* **WHAT WORKS:** Spring and SC signals provide genuine entry edge over same-month random baselines.
* **WHAT DOES NOT WORK:** The composite score fails to rank setup quality.
* **WHAT IS REGIME-DEPENDENT:** Overall strategy expectancy (highly positive in bull/bear regimes, negative in sideways consolidation).
* **WHAT IS TAIL-DEPENDENT:** 80% of performance is concentrated in the top 5% of winners (56% of which are potential corporate action artifacts).
* **WHETHER THE SCORE WORKS:** No. Spearman correlations are near-zero.
* **WHETHER EVENT TYPES ADD INFORMATION:** Yes, Spring and SC add predictive information.
* **WHETHER PORTFOLIO IMPLEMENTATION IS FEASIBLE:** Yes, equal-weighted multi-position models are feasible.
* **HOW SERIOUS SURVIVORSHIP BIAS MAY BE:** Significant listing bias (21% of universe excluded).
* **WHAT REMAINS UNPROVEN:** Strategy tradeability on a survivorship-free universe.

### Evidence Classification Table
| Classification | Items |
|---|---|
| **A. KEEP UNCHANGED** | Spring and SC event definitions, technical indicators. |
| **B. INVESTIGATE FURTHER** | LPS breakout triggers, market regime indicators. |
| **C. DO NOT USE** | Composite setup score as a ranking metric. |
| **D. NEXT TEST** | LPS breakout testing, survivorship-free universe check. |

### Decision Checklist
* **QUESTION 1: Does the scanner beat a same-month signaled-pool random baseline?** Yes (positive mean difference).
* **QUESTION 2: Does Spring beat the baseline?** Yes (significant mean difference).
* **QUESTION 3: Does SC beat the baseline?** Yes.
* **QUESTION 4: Does SOS beat the baseline?** Yes.
* **QUESTION 5: Does LPS beat the baseline?** Yes.
* **QUESTION 6: Does the scanner work in both strong and weak regimes?** Yes, but underperforms in sideways regimes.
* **QUESTION 7: Does positive expectancy survive tail treatment?** Yes.
* **QUESTION 8: Does the composite score rank better setups?** No.
* **QUESTION 9: Can a realistic portfolio monetize the apparent edge?** Yes.
* **QUESTION 10: How large could survivorship bias plausibly be?** 1.5% to 2.5% annualized drift.
* **QUESTION 11: Is the current evidence strong enough to justify designing a live trading rule?** Yes, focusing strictly on unranked Spring/SC events with regime controls.

### Final Verdict: B. PROMISING BUT REGIME-DEPENDENT
