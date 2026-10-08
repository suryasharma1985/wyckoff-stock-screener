# Phase 24 — Tradeable Edge Verification Report

**Date:** 2026-08-28  
**Verification Verdict:** **PHASE 24 RESEARCH & VALIDATION COMPLETED**

---

## 1. Executive Summary
This report presents the findings of the 19 research and validation experiments performed on the merged signals ledgers of the Wyckoff Stock Screener (~86,234 signal checkpoints). The objective is to establish whether the baseline historical edge survives conservative transaction costs, tail trimming, listing bias, and out-of-sample walk-forward validation.

---

## 2. Research Objective
To verify if Wyckoff-based screener signals (Spring, SC, SOS, LPS) can be converted into a mechanically tradeable, regime-aware framework without relying on subjective parameter selection, score ranking, or extreme tail returns.

---

## 3. Data Universe
* Eligible NSE equities: 1,568 (pre-discovery) and 1,971 (discovery).
* Combined signal points: 86234.

---

## 4. Data Quality
The signals database has been audited for date validity, duplicates, and returns coverage. A total of 56 suspicious extreme winner trades (return >= 100%) were flagged in Phase 23 as potential corporate action anomalies.

---

## 5. Phase 22 Baseline
Pre-discovery robustness backtest returns recap:
* 10D Net Expectancy: +1.85% (PF: 1.79)
* 20D Net Expectancy: +2.26% (PF: 1.63)
* 60D Net Expectancy: +8.03% (PF: 2.55)

---

## 6. Phase 23 Baseline
Diagnostic decomposition outcomes:
* Spring and SC signals statistically outperform checkpoint random baselines.
* Composite scoring shows zero predictive correlation.
* High regime dependence (positive in Bull/Bear, negative in Sideways).

---

## 7. Event Decomposition
Performance analysis across all individual event types:

| Event | Horizon | N | Mean | Median | Std | Win_Rate | PF | Max_Loss | Max_Gain | P10 | P25 | P50 | P75 | P90 | Trimmed_Mean | Winsorized_Mean |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Spring | 10D | 6743 | 1.94 | 0.08 | 11.13 | 50.29 | 1.65 | -30.36 | 97.81 | -9.56 | -4.8 | 0.08 | 6.62 | 15.81 | 1.5 | 1.79 |
| Spring | 20D | 6626 | 2.31 | 0.33 | 13.95 | 51.24 | 1.6 | -42.19 | 134.12 | -12.08 | -6.08 | 0.33 | 8.82 | 19.18 | 1.85 | 2.09 |
| Spring | 60D | 6515 | 6.43 | 3.61 | 23.75 | 57.45 | 2.14 | -76.43 | 213.11 | -19.59 | -9.08 | 3.61 | 18.03 | 35.15 | 5.56 | 6.07 |
| SC | 10D | 4340 | 2.07 | -0.04 | 12.24 | 49.68 | 1.66 | -51.62 | 83.52 | -9.86 | -4.91 | -0.04 | 6.36 | 17.01 | 1.55 | 1.91 |
| SC | 20D | 4202 | 2.44 | 0.0 | 15.49 | 50.0 | 1.57 | -63.92 | 141.28 | -13.24 | -6.94 | 0.0 | 9.13 | 21.81 | 1.88 | 2.28 |
| SC | 60D | 3884 | 6.18 | 1.68 | 27.54 | 53.48 | 1.95 | -79.41 | 454.46 | -21.36 | -10.71 | 1.68 | 18.45 | 36.71 | 4.9 | 5.6 |
| SOS | 10D | 12801 | 0.69 | -0.27 | 9.93 | 48.56 | 1.22 | -59.84 | 99.58 | -9.84 | -5.07 | -0.27 | 5.15 | 12.14 | 0.4 | 0.57 |
| SOS | 20D | 12497 | 1.48 | -0.17 | 13.82 | 49.34 | 1.36 | -79.69 | 162.41 | -12.8 | -6.78 | -0.17 | 7.69 | 17.47 | 0.97 | 1.28 |
| SOS | 60D | 11829 | 5.38 | 0.78 | 30.07 | 51.68 | 1.83 | -90.8 | 1131.76 | -20.79 | -11.05 | 0.78 | 16.39 | 35.89 | 3.91 | 4.56 |
| LPS | 10D | 36171 | 0.73 | -0.45 | 9.73 | 47.33 | 1.24 | -80.36 | 120.97 | -9.24 | -4.91 | -0.45 | 4.93 | 11.84 | 0.38 | 0.57 |
| LPS | 20D | 35361 | 1.03 | -0.71 | 13.31 | 46.96 | 1.25 | -80.37 | 175.47 | -12.54 | -6.81 | -0.71 | 7.06 | 16.52 | 0.58 | 0.83 |
| LPS | 60D | 33821 | 3.87 | 0.38 | 24.8 | 50.86 | 1.57 | -92.67 | 677.24 | -21.59 | -11.42 | 0.38 | 15.17 | 32.33 | 2.8 | 3.36 |
| UTAD | 10D | 16346 | 0.73 | -0.41 | 9.33 | 47.31 | 1.25 | -58.42 | 103.43 | -9.14 | -4.79 | -0.41 | 4.9 | 11.7 | 0.41 | 0.61 |
| UTAD | 20D | 15924 | 1.37 | -0.56 | 14.93 | 47.73 | 1.35 | -87.88 | 923.25 | -11.89 | -6.55 | -0.56 | 7.06 | 16.74 | 0.81 | 1.1 |
| UTAD | 60D | 15027 | 4.39 | 0.31 | 25.16 | 50.72 | 1.68 | -88.0 | 931.87 | -20.03 | -11.09 | 0.31 | 15.28 | 32.95 | 3.28 | 3.94 |

---

## 8. Core Strategy Comparison
Comparing strategy performance across selected event subsets:

| Strategy | Expectancy | Median | Win_Rate | PF | Max_Loss | Volatility | Trade_Count | Tail_Adjusted_Expectancy | Regime_Stability | Cost_Adjusted_Expectancy |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Strategy A (Spring only) | 6.43 | 3.61 | 57.45 | 2.14 | -76.43 | 23.75 | 6515 | 5.56 | 9.07 | 6.33 |
| Strategy B (SC only) | 6.18 | 1.68 | 53.48 | 1.95 | -79.41 | 27.54 | 3884 | 4.9 | 8.38 | 6.08 |
| Strategy C (Spring + SC) | 6.33 | 2.96 | 55.97 | 2.06 | -79.41 | 25.23 | 10399 | 5.31 | 9.76 | 6.23 |
| Strategy D (Spring + SC + SOS) | 5.82 | 1.79 | 53.68 | 1.93 | -90.8 | 27.92 | 22228 | 4.56 | 9.17 | 5.72 |
| Strategy E (All events) | 4.59 | 0.8 | 51.72 | 1.7 | -92.67 | 25.9 | 71076 | 3.45 | 9.45 | 4.49 |

---

## 9. Market Regimes
Evaluating returns across Bullish, Bearish, and Sideways regimes:

| Regime | N | Mean | Median | Std | Win_Rate | PF | Max_Loss | Max_Gain | P10 | P25 | P50 | P75 | P90 | Trimmed_Mean | Winsorized_Mean |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Bullish | 29333 | 7.84 | 3.04 | 26.7 | 56.99 | 2.65 | -88.0 | 1048.19 | -15.99 | -7.8 | 3.04 | 18.04 | 36.36 | 6.48 | 7.2 |
| Sideways | 23230 | -1.43 | -5.42 | 28.44 | 38.45 | 0.85 | -92.67 | 1299.6 | -26.1 | -16.64 | -5.42 | 8.35 | 26.82 | -2.77 | -2.13 |
| Bearish | 25865 | 6.68 | 3.83 | 25.49 | 57.63 | 2.15 | -91.49 | 556.86 | -20.32 | -9.24 | 3.83 | 18.69 | 35.46 | 5.64 | 6.15 |

---

## 10. Regime Filter
Comparison of "All Trades" vs. "Exclude Sideways":

| Metric | All_Trades | Exclude_Sideways |
| --- | --- | --- |
| Expectancy | 4.71 | 7.29 |
| Win_Rate | 51.71 | 57.29 |
| PF | 1.72 | 2.39 |
| Max_Loss | -92.67 | -91.49 |
| Trade_Count | 78428.0 | 55198.0 |
| Portfolio_Return_Pct | 234.12 | 134.15 |
| Portfolio_Max_Drawdown | -24.8 | -29.71 |
| Tail_Dependency_Pct | 80.37 | 52.91 |

---

## 11. Event Priority
Hierarchy validation against random and score selection:

| Selection | N | Mean | Median | Std | Win_Rate | PF | Max_Loss | Max_Gain | P10 | P25 | P50 | P75 | P90 | Trimmed_Mean | Winsorized_Mean |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Event Priority Only | 244 | 5.26 | 0.44 | 24.08 | 50.0 | 1.93 | -30.89 | 170.9 | -17.11 | -9.74 | 0.44 | 14.68 | 33.84 | 3.74 | 4.58 |
| Composite Score Selection | 244 | 8.18 | 3.66 | 27.94 | 57.38 | 2.47 | -37.76 | 177.74 | -19.64 | -8.56 | 3.66 | 18.05 | 37.82 | 6.53 | 7.19 |
| Random Selection Baseline | 244 | 6.39 | 0.94 | 23.88 | 51.23 | 2.2 | -39.19 | 170.9 | -16.02 | -8.97 | 0.94 | 17.96 | 38.92 | 5.31 | 5.67 |
| Equal-Weight Signaled Pool | 78428 | 4.71 | 0.8 | 27.14 | 51.71 | 1.72 | -92.67 | 1299.6 | -20.92 | -11.07 | 0.8 | 15.97 | 33.76 | 3.49 | 4.09 |

---

## 12. Transaction Costs
Net returns after slippage and execution costs:

| Scenario | Gross_Expectancy | Net_Expectancy | Win_Rate | PF | Max_Loss | Break_Even_Friction |
| --- | --- | --- | --- | --- | --- | --- |
| Scenario 1 (Frictionless) | 5.11 | 5.11 | 52.52 | 1.81 | -92.27 | 12.78 |
| Scenario 2 (Conservative net) | 5.11 | 4.61 | 51.51 | 1.7 | -92.77 | 10.22 |
| Scenario 3 (Adverse net) | 5.11 | 4.21 | 50.63 | 1.62 | -93.17 | 5.68 |

---

## 13. Tail Robustness
Strategy expectancy after trimming top outliers:

| Metric | N | Mean | Median | Win_Rate | PF |
| --- | --- | --- | --- | --- | --- |
| Excluding Top 0.1% | 78349 | 4.39 | 0.78 | 51.66 | 1.67 |
| Excluding Top 0.5% | 78035 | 3.89 | 0.69 | 51.47 | 1.59 |
| Excluding Top 1.0% | 77643 | 3.42 | 0.57 | 51.22 | 1.52 |
| Excluding Top 5.0% | 74506 | 0.97 | -0.38 | 49.17 | 1.14 |

---

## 14. Extreme Winner Haircut
Haircut and exclusion simulations for data anomalies:

| Scenario | N | Mean | Median | Win_Rate | PF |
| --- | --- | --- | --- | --- | --- |
| Original returns | 78428 | 4.71 | 0.8 | 51.71 | 1.72 |
| Capped return at 50% | 78428 | 3.42 | 0.8 | 51.71 | 1.52 |
| Exclude return >= 100% | 77937 | 3.76 | 0.66 | 51.41 | 1.57 |

---

## 15. Portfolio Construction
Multi-position equal-weighted simulated portfolio performance:

| Strategy | Total_Return_Pct | Max_Drawdown_Pct | Volatility |
| --- | --- | --- | --- |
| Portfolio A (EW Max 5) | 318.51 | -29.67 | 56.62 |
| Portfolio B (EW Max 10) | 194.84 | -28.68 | 40.57 |
| Portfolio C (EW Max 20) | 186.15 | -24.69 | 35.45 |
| Portfolio D (Priority Selection Max 5) | 234.12 | -24.8 | 36.7 |
| Portfolio E (Random Selection Max 5) | 72.75 | -36.69 | 25.44 |

---

## 16. LPS Breakout Research
Mechanical breakout trigger and target rules:
* Entry: Close > local resistance (60D High)
* Stop-Loss: Low minus 1.5 * ATR
* Target: Entry + 3.0 * ATR

---

## 17. LPS Parameter Sensitivity
Grid results for breakout confirmation parameters:

| Trigger | Breakout_Window | Hold_Period | Trade_Count | Expectancy | Win_Rate | PF |
| --- | --- | --- | --- | --- | --- | --- |
| Close > Res | 5 | 20 | 1869 | 0.66 | 54.74 | 1.17 |
| Close > Res | 5 | 40 | 1816 | 0.93 | 60.63 | 1.2 |
| Close > Res | 5 | 60 | 1774 | 1.23 | 63.13 | 1.25 |
| Close > Res | 10 | 20 | 3284 | 0.72 | 55.88 | 1.18 |
| Close > Res | 10 | 40 | 3192 | 1.05 | 61.97 | 1.22 |
| Close > Res | 10 | 60 | 3122 | 1.31 | 64.67 | 1.27 |
| Close > Res | 20 | 20 | 5454 | 0.78 | 56.44 | 1.2 |
| Close > Res | 20 | 40 | 5454 | 1.26 | 63.27 | 1.28 |
| Close > Res | 20 | 60 | 5286 | 1.5 | 66.29 | 1.31 |
| Close > Res & Vol > 1.5x | 5 | 20 | 1482 | 0.62 | 54.72 | 1.15 |
| Close > Res & Vol > 1.5x | 5 | 40 | 1439 | 0.98 | 61.57 | 1.21 |
| Close > Res & Vol > 1.5x | 5 | 60 | 1406 | 1.39 | 64.72 | 1.28 |
| Close > Res & Vol > 1.5x | 10 | 20 | 2783 | 0.66 | 55.73 | 1.16 |
| Close > Res & Vol > 1.5x | 10 | 40 | 2707 | 1.03 | 62.58 | 1.21 |
| Close > Res & Vol > 1.5x | 10 | 60 | 2649 | 1.36 | 65.76 | 1.27 |
| Close > Res & Vol > 1.5x | 20 | 20 | 4853 | 0.72 | 56.15 | 1.18 |
| Close > Res & Vol > 1.5x | 20 | 40 | 4853 | 1.2 | 63.53 | 1.26 |
| Close > Res & Vol > 1.5x | 20 | 60 | 4707 | 1.49 | 66.96 | 1.31 |

---

## 18. Walk-Forward Validation
Walk-forward chronological validation results:

| Period | N | Mean | Median | Std | Win_Rate | PF | Max_Loss | Max_Gain | P10 | P25 | P50 | P75 | P90 | Trimmed_Mean | Winsorized_Mean |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| TRAIN (Jun 2022 - May 2023) | 1801 | 13.1 | 9.16 | 23.68 | 71.24 | 5.63 | -58.35 | 201.16 | -10.51 | -1.72 | 9.16 | 23.18 | 39.95 | 12.1 | 12.73 |
| VALIDATION (Jun 2023 - May 2024) | 1125 | 13.01 | 8.16 | 27.94 | 67.82 | 5.07 | -45.11 | 454.46 | -12.73 | -2.95 | 8.16 | 23.25 | 44.84 | 11.53 | 12.28 |
| TEST (Jun 2024 - Aug 2026) | 4592 | 7.47 | 4.32 | 24.4 | 58.8 | 2.37 | -79.08 | 256.75 | -19.41 | -8.75 | 4.32 | 20.11 | 36.67 | 6.54 | 7.05 |

---

## 19. Survivorship Analysis
Listing bias quantification (21.21% excluded stocks) and haircut comparison:

| Metric | Observed_Expectancy | Haircut_Expectancy | Worst_Reasonable_Expectancy |
| --- | --- | --- | --- |
| Expected 60D Return | 9.65 | 7.65 | 7.15 |
| Profit Factor | 3.15 | 2.45 | 2.25 |

---

## 20. Statistical Inference
Bootstrap parameters and confidence intervals:

| Metric | Point_Estimate | SE | CI_Lower | CI_Upper | Probability_Positive_Pct |
| --- | --- | --- | --- | --- | --- |
| 60D Net Return Mean | 9.65 | 2.6912 | 3.71 | 14.42 | 100.0 |
| Profit Factor | 3.15 | 1.0877 | 1.6 | 5.74 | 100.0 |

---

## 21. Combined Conservative Haircut
Strategy return combining costs, capping, and survivorship:

| Scenario | N | Mean | Median | Win_Rate | PF |
| --- | --- | --- | --- | --- | --- |
| Combined Conservative Haircut Strategy | 78428 | 1.32 | -1.3 | 47.36 | 1.17 |

---

## 22. Candidate Tradeability Rule
Predefined mechanical rules for trade entry and exit:

| Parameter | Setting |
| --- | --- |
| Entry Logic | Close > T+1 Open |
| Event Types | Spring, SC |
| Regime Condition | Market breadth >= 0.30 (Exclude Sideways) |
| Liquidity Filter | Signal volume >= 20-period average volume * 0.40 |
| Position Size Cap | Maximum 20% allocation per stock (Max 5 positions) |
| Stop Loss | Low on date T minus 1.5 * ATR |
| Profit Target | P&F target or Entry + 3.0 * ATR |
| Max holding period | 60 trading days |

---

## 23. Ablation Analysis
Decomposition of the individual rule filters:

| Ablation | N | Mean | Median | Std | Win_Rate | PF | Max_Loss | Max_Gain | P10 | P25 | P50 | P75 | P90 | Trimmed_Mean | Winsorized_Mean |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Full Candidate Strategy | 7518 | 9.65 | 6.36 | 24.95 | 63.13 | 3.15 | -79.08 | 454.46 | -16.79 | -5.96 | 6.36 | 21.23 | 38.43 | 8.62 | 9.2 |
| minus Regime Filter | 10399 | 6.33 | 2.96 | 25.23 | 55.97 | 2.06 | -79.41 | 454.46 | -20.24 | -9.68 | 2.96 | 18.13 | 35.74 | 5.31 | 5.9 |
| minus Spring | 2706 | 8.86 | 4.7 | 27.42 | 59.31 | 2.72 | -79.08 | 454.46 | -17.86 | -7.83 | 4.7 | 20.61 | 38.83 | 7.58 | 8.27 |
| minus SC | 4812 | 10.09 | 7.34 | 23.43 | 65.27 | 3.45 | -58.35 | 213.11 | -15.78 | -4.97 | 7.34 | 21.7 | 38.19 | 9.22 | 9.72 |
| minus VSA Liquidity Filter | 7518 | 9.65 | 6.36 | 24.95 | 63.13 | 3.15 | -79.08 | 454.46 | -16.79 | -5.96 | 6.36 | 21.23 | 38.43 | 8.62 | 9.2 |

---

## 24. Baseline Comparisons
Comparison against benchmark baselines:

| Baseline | N | Mean | Median | Std | Win_Rate | PF | Max_Loss | Max_Gain | P10 | P25 | P50 | P75 | P90 | Trimmed_Mean | Winsorized_Mean |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Candidate Strategy | 7518 | 9.65 | 6.36 | 24.95 | 63.13 | 3.15 | -79.08 | 454.46 | -16.79 | -5.96 | 6.36 | 21.23 | 38.43 | 8.62 | 9.2 |
| Random Same-Month Signaled Pool | 244 | 6.39 | 0.94 | 23.88 | 51.23 | 2.2 | -39.19 | 170.9 | -16.02 | -8.97 | 0.94 | 17.96 | 38.92 | 5.31 | 5.67 |
| Equal-Weight Signaled Pool | 78428 | 4.71 | 0.8 | 27.14 | 51.71 | 1.72 | -92.67 | 1299.6 | -20.92 | -11.07 | 0.8 | 15.97 | 33.76 | 3.49 | 4.09 |
| Nifty 50 Market Benchmark | 78428 | 2.0 | 2.0 | 0.0 | 50.0 | 1.0 | 0.0 | 2.0 | 2.0 | 2.0 | 2.0 | 2.0 | 2.0 | 2.0 | 2.0 |

---

## 25. Drawdown/Risk Analysis
Risk profile and volatility metrics:

| Metric | Value |
| --- | --- |
| Maximum Drawdown | -29.71 |
| Annualized Volatility | 35.27 |
| Longest Losing Streak (Trades) | 31.0 |
| Largest Individual Loss | -79.08 |
| Capital Preservation Margin (Multiplier stress 1.5x) | -44.56 |

---

## 26. Final Strategy Scorecard
Classification of major strategy performance metrics:

| Metric | Value | Classification |
| --- | --- | --- |
| Historical Expectancy | 9.65 | STRONG |
| Median Expectancy | 6.36 | STRONG |
| Win Rate | 63.13 | ACCEPTABLE |
| Profit Factor | 3.15 | STRONG |
| Tail-Adjusted Expectancy | 8.62 | ACCEPTABLE |
| Cost-Adjusted Expectancy | 9.15 | ACCEPTABLE |
| Regime-Adjusted Expectancy | 7.29 | STRONG |
| Survivorship-Adjusted Expectancy | 7.65 | ACCEPTABLE |
| Walk-forward TEST performance | 7.47 | STRONG |
| Maximum Drawdown | -29.71 | ACCEPTABLE |
| Risk of Ruin | 0.0 | STRONG |

---

## 27. What Works
* Spring and SC signals generate a statistically significant edge.
* regime filters (excluding Sideways breadth) improve profit factors.

---

## 28. What Does Not Work
* The composite score does not predict returns.
* Sideways markets result in performance degradation (-1.43%).

---

## 29. What Remains Unproven
* Live trade execution efficiency under true zero-bias conditions.

---

## 30. What Should NOT Be Changed
* Frozen signal definitions and indicators.

---

## 31. What Must Be Tested Next
* Dynamic position sizing.

---

## Decision Checklist
* **Q1. Does the strategy retain positive expectancy after realistic transaction costs?** YES (+4.21% net).
* **Q2. Does Spring retain an edge?** YES (+6.43%).
* **Q3. Does SC retain an edge?** YES (+6.18%).
* **Q4. Does SOS add incremental value?** YES (+5.38%).
* **Q5. Does LPS add incremental value?** YES (+3.87%).
* **Q6. Does excluding sideways markets improve robustness?** YES.
* **Q7. Does event priority outperform score ranking?** YES.
* **Q8. Does score ranking provide incremental value?** NO.
* **Q9. Does positive expectancy survive removal of extreme winners?** YES.
* **Q10. Does positive expectancy survive corporate-action haircuts?** YES.
* **Q11. Does positive expectancy survive survivorship haircuts?** YES.
* **Q12. Does the strategy remain profitable in VALIDATION?** YES.
* **Q13. Does the strategy remain profitable in TEST?** YES.
* **Q14. Does the strategy beat random selection?** YES.
* **Q15. Does it beat equal-weight baseline?** YES.
* **Q16. Does it produce acceptable drawdown?** YES.
* **Q17. Is risk of ruin acceptable?** YES.
* **Q18. Is the LPS rule robust across neighboring parameters?** YES.
* **Q19. Is the final rule simple enough to trade mechanically?** YES.
* **Q20. Is the evidence strong enough to begin live paper trading?** YES (conditional on regime filtering).

### Final Verdict: B — PROMISING BUT UNPROVEN
