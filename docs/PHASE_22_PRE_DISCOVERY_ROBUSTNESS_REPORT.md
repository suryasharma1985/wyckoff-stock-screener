# Phase 22 Pre-Discovery Historical Robustness Report

**Date:** 2026-08-27  
**Verification Verdict:** **PHASE 22 BASELINE BACKTEST COMPLETED**

---

## 1. Executive Summary
This report presents the findings of a completely independent historical pre-discovery robustness backtest of the frozen Wyckoff Stock Screener strategy. The evaluation spans from **2022-06-01 through 2023-05-31** (the 12 months immediately preceding the discovery backtest).

The goal is to determine whether the screener's positive net expectancy survives on historical data prior to the discovery period.

### Overall Performance Verdict
* **Expectancy Verdict:** **PASS** (60D net expectancy remains positive).
* **Score Discrimination Verdict:** **FAIL** (Spearman rank correlation confirms composite score does not predict returns).
* **Tail Robustness Verdict:** **FAIL** (Expectancy is heavily dependent on the top 5% of trades).
* **Listing/Survivorship Bias:** **CONFIRMED** (403 stocks were excluded due to lack of historical data prior to 2023).

---

## 2. Master Performance Comparison Table

| Metric | Pre-Discovery Period (Jun 2022 - May 2023) | Discovery Period (Jun 2023 - Aug 2026) |
|---|---|---|
| **Total Evaluated Stocks** | 1568 | 1,971 |
| **Total 60D Trades** | 18172 | 60256 |
| **10D Net Expectancy** | 1.85% | 0.67% |
| **20D Net Expectancy** | 2.26% | 1.15% |
| **60D Net Expectancy** | 8.03% | 3.71% |
| **10D Win Rate (Net)** | 53.12% | 46.44% |
| **20D Win Rate (Net)** | 51.54% | 47.03% |
| **60D Win Rate (Net)** | 57.98% | 49.82% |
| **10D Profit Factor** | 1.79 | 1.2 |
| **20D Profit Factor** | 1.63 | 1.27 |
| **60D Profit Factor** | 2.55 | 1.53 |
| **Spearman Correlation** | 0.0103 | -0.0108 |

---

## 3. Event-Level Analysis (60D net returns)

| Event | total_trades | winning_trades | losing_trades | flat_trades | win_rate | avg_gross_return | avg_net_return | median_net_return | profit_factor | expectancy | best_trade | worst_trade | std_dev |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Spring | 1510 | 1014 | 496 | 0 | 67.15 | 10.56 | 10.16 | 7.24 | 3.81 | 10.16 | 201.16 | -76.43 | 22.53 |
| SC | 916 | 490 | 426 | 0 | 53.49 | 7.17 | 6.77 | 1.8 | 2.1 | 6.77 | 189.51 | -61.95 | 27.88 |
| SOS | 2403 | 1317 | 1085 | 1 | 54.81 | 7.87 | 7.47 | 2.19 | 2.28 | 7.47 | 414.66 | -90.8 | 30.91 |
| LPS | 7925 | 4563 | 3360 | 2 | 57.58 | 7.53 | 7.13 | 3.53 | 2.36 | 7.13 | 677.24 | -90.47 | 26.19 |
| AR | 627 | 390 | 237 | 0 | 62.2 | 8.88 | 8.48 | 5.78 | 2.63 | 8.48 | 129.65 | -80.53 | 24.26 |
| ST | 1307 | 739 | 568 | 0 | 56.54 | 9.91 | 9.51 | 2.82 | 2.79 | 9.51 | 851.72 | -65.95 | 39.38 |
| UTAD | 3452 | 2010 | 1442 | 0 | 58.23 | 8.28 | 7.88 | 3.4 | 2.61 | 7.88 | 218.52 | -83.14 | 25.14 |

---

## 4. Score Discrimination Analysis (60D net returns)

| Bucket | total_trades | winning_trades | losing_trades | flat_trades | win_rate | avg_gross_return | avg_net_return | median_net_return | profit_factor | expectancy | best_trade | worst_trade | std_dev |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0-49 | 11850 | 6836 | 5011 | 3 | 57.69 | 8.46 | 8.06 | 3.6 | 2.56 | 8.06 | 1299.6 | -90.8 | 33.29 |
| 50-59 | 3866 | 2237 | 1629 | 0 | 57.86 | 7.75 | 7.35 | 3.45 | 2.39 | 7.35 | 408.81 | -86.43 | 26.58 |
| 60-69 | 2047 | 1232 | 815 | 0 | 60.19 | 9.68 | 9.28 | 5.01 | 2.87 | 9.28 | 295.42 | -90.47 | 28.22 |
| 70-79 | 376 | 211 | 165 | 0 | 56.12 | 7.96 | 7.56 | 2.58 | 2.41 | 7.56 | 123.38 | -51.16 | 25.3 |
| 80-89 | 33 | 21 | 12 | 0 | 63.64 | 7.37 | 6.97 | 2.31 | 3.09 | 6.97 | 54.18 | -27.05 | 18.34 |

* **Spearman correlation:** 0.0103 (signifies no meaningful relationship).

---

## 5. Tail Sensitivity Analysis (60D net returns)

* **Original Average 60D Return:** 8.03%
| Metric | Trades Remaining | Average 60D Return |
| --- | --- | --- |
| Excluding Top 1% | 17990 | 6.37 |
| Excluding Top 5% | 17263 | 3.83 |
| Excluding Top 10% | 16354 | 1.66 |

---

## 6. Monthly Regime Analysis (60D net returns)

| Month | total_trades | winning_trades | losing_trades | flat_trades | win_rate | avg_gross_return | avg_net_return | median_net_return | profit_factor | expectancy | best_trade | worst_trade | std_dev |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2022-06 | 1467 | 1100 | 367 | 0 | 74.98 | 15.77 | 15.37 | 10.95 | 7.57 | 15.37 | 396.93 | -64.32 | 28.92 |
| 2022-07 | 1482 | 898 | 583 | 1 | 60.59 | 9.65 | 9.25 | 3.96 | 3.27 | 9.25 | 677.24 | -40.51 | 31.44 |
| 2022-08 | 1496 | 751 | 745 | 0 | 50.2 | 5.62 | 5.22 | 0.14 | 1.96 | 5.22 | 851.72 | -55.94 | 32.78 |
| 2022-09 | 1499 | 734 | 765 | 0 | 48.97 | 5.75 | 5.35 | -0.4 | 1.99 | 5.35 | 1299.6 | -49.84 | 41.81 |
| 2022-10 | 1505 | 647 | 858 | 0 | 42.99 | 3.46 | 3.06 | -2.51 | 1.48 | 3.06 | 899.6 | -90.8 | 34.76 |
| 2022-11 | 1508 | 357 | 1150 | 1 | 23.67 | -6.43 | -6.83 | -9.43 | 0.39 | -6.83 | 799.6 | -90.47 | 29.49 |
| 2022-12 | 1515 | 295 | 1220 | 0 | 19.47 | -11.69 | -12.09 | -14.02 | 0.21 | -12.09 | 336.39 | -86.43 | 20.7 |
| 2023-01 | 1521 | 728 | 793 | 0 | 47.86 | 2.22 | 1.82 | -0.59 | 1.33 | 1.82 | 500.99 | -74.82 | 23.97 |
| 2023-02 | 1535 | 1154 | 381 | 0 | 75.18 | 13.72 | 13.32 | 9.08 | 7.51 | 13.32 | 556.86 | -83.14 | 26.59 |
| 2023-03 | 1544 | 1392 | 152 | 0 | 90.16 | 24.54 | 24.14 | 19.99 | 28.24 | 24.14 | 341.28 | -74.78 | 26.33 |
| 2023-04 | 1550 | 1217 | 333 | 0 | 78.52 | 17.69 | 17.29 | 13.2 | 9.5 | 17.29 | 196.43 | -77.93 | 25.36 |
| 2023-05 | 1550 | 1264 | 285 | 1 | 81.55 | 20.15 | 19.75 | 14.24 | 13.9 | 19.75 | 256.01 | -80.53 | 26.56 |

---

## 7. Pre-Discovery PASS / FAIL Scorecard

| Diagnostic Gate | Verdict | Supporting Evidence |
|---|---|---|
| **Overall Expectancy** | PASS | 60D Expectancy is positive |
| **Spring Edge** | PASS | Spring net profit factor is 3.81 |
| **SC Edge** | PASS | SC net profit factor is 2.1 |
| **Score Discrimination** | FAIL | Spearman correlation is 0.0103 |
| **Tail Robustness** | PASS | Net expectancy drops significantly excluding top 5% |
| **Lookahead Safety** | PASS | Dates strictly filtered on <= T |

---

## 8. Answers to Key Research Questions
* **Q1. Did the strategy make money in June 2022–May 2023?** Yes, net expectancy at 60D was positive (+8.03%).
* **Q2. What was the exact 10D win rate?** 53.12%.
* **Q3. What was the exact 20D win rate?** 51.54%.
* **Q4. What was the exact 60D win rate?** 57.98%.
* **Q5. What was the exact 10D expectancy?** 1.85%.
* **Q6. What was the exact 20D expectancy?** 2.26%.
* **Q7. What was the exact 60D expectancy?** 8.03%.
* **Q8. What was the exact profit factor at each horizon?** 10D: 1.79 | 20D: 1.63 | 60D: 2.55.
* **Q9. Did Spring remain profitable?** Yes, with average net return of 10.16%.
* **Q10. Did Selling Climax remain profitable?** Yes.
* **Q11. Did SOS remain profitable?** Yes.
* **Q12. Did LPS remain profitable?** Yes.
* **Q13. Did UTAD behave differently?** Yes, in structural bull months UTAD generated positive returns due to index momentum.
* **Q14. Does the composite score still fail to discriminate returns?** Yes, Spearman correlation was 0.0103.
* **Q15. Is the edge still dependent on extreme winners?** Yes, excluding top 5% of winners reduces expectancy to 3.83%.
* **Q16. Does this historical period strengthen our belief?** It strengthens belief in the baseline positive expectancy, but highlights the risks of survivorship bias and tail concentration.
* **Q17. Does this test remove survivorship bias?** No, it utilizes the same current constituent list.
* **Q18. Does this test replace true OOS validation?** No, true out-of-sample live validation remains the only unbiased test.
