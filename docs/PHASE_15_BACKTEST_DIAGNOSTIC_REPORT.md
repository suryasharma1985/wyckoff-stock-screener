# Phase 15/17 Broad NSE EQ Backtest Diagnostic Report

**Date:** 2026-08-26  
**Backtest ID:** `backtest_nse_eq_monthly_20260826`  
**Dataset Analyzed:** [`data/validation_results/20260826/backtest_returns.csv`](file:///c:/Users/surya/Downloads/wyckoff-stock-screener/data/validation_results/20260826/backtest_returns.csv)  
**Manifest File:** [`data/validation_results/20260826/backtest_manifest.json`](file:///c:/Users/surya/Downloads/wyckoff-stock-screener/data/validation_results/20260826/backtest_manifest.json)  

---

## 1. Audit of Stored Results
* **Lead Result Paths:** 
  * Trade ledger: [`data/validation_results/20260826/backtest_returns.csv`](file:///c:/Users/surya/Downloads/wyckoff-stock-screener/data/validation_results/20260826/backtest_returns.csv) (59.4 MB, 68,059 rows, 73 columns)
  * Price panel: [`data/validation_results/20260826/historical_prices.csv`](file:///c:/Users/surya/Downloads/wyckoff-stock-screener/data/validation_results/20260826/historical_prices.csv) (90.0 MB, 1,571,258 rows, 8 columns)
* **Date Range:** 2023-06-01 through 2026-08-24 (39 monthly checkpoints)
* **Unique Securities Evaluated:** 1,971 NSE equities
* **Total Signal Observations:** 68,059
* **Data Sufficiency:** The raw ledger is fully populated with forward returns, excursions (MFE/MAE), drawdown, and setup categories, which are sufficient for all diagnostics. No backtest rerun is required.

---

## 2. Diagnostic 1 — Score Discrimination

### Bucket Performance (Net Returns Net of 0.40% Friction)
| Score Bucket | 10D Net Return | 20D Net Return | 60D Net Return | 60D Profit Factor | 60D Win Rate | Observations |
|---|---|---|---|---|---|---|
| **0–49** | +0.77% | +1.25% | **+3.94%** | 1.58 | 50.47% | 38,350 |
| **50–59** | +0.47% | +0.74% | **+3.33%** | 1.45 | 48.84% | 13,191 |
| **60–69** | +0.49% | +1.19% | **+3.00%** | 1.41 | 47.97% | 7,177 |
| **70–79** | +0.47% | +1.77% | **+4.60%** | 1.68 | 50.63% | 1,418 |
| **80–89** | +2.01% | +3.19% | **+4.19%** | 1.61 | 50.00% | 120 |

### Cohort Comparisons (60D Net Horizon)
* **Top 10%** (Score $\ge 60$, n = 6,713): Net Return **+3.30%** | Win Rate: **48.58%** | Profit Factor: **1.46**
* **Bottom 10%** (Score $\le 35$, n = 6,369): Net Return **+2.66%** | Win Rate: **46.33%** | Profit Factor: **1.36**
* **Top 20%** (Score $\ge 56$, n = 12,053): Net Return **+3.15%** | Win Rate: **48.58%** | Profit Factor: **1.44**
* **Bottom 20%** (Score $\le 40$, n = 12,685): Net Return **+3.13%** | Win Rate: **48.06%** | Profit Factor: **1.45**
* **Top Quartile (Q4)** (Score $\ge 54$, n = 15,172): Net Return **+3.05%** | Win Rate: **47.83%** | Profit Factor: **1.41**
* **Bottom Quartile (Q1)** (Score $\le 42$, n = 15,091): Net Return **+3.30%** | Win Rate: **48.71%** | Profit Factor: **1.48**
* **Qualified** (`is_qualified == True`, n = 5,860): Net Return **+3.41%** | Win Rate: **48.28%** | Profit Factor: **1.48**
* **Non-Qualified** (`is_qualified == False`, n = 54,396): Net Return **+3.74%** | Win Rate: **49.98%** | Profit Factor: **1.54**

### Correlation Analysis
* **Pearson Correlation (Score vs. 60D Net Return):** `-0.0018`
* **Spearman Rank Correlation (Score vs. 60D Net Return):** `-0.0108`
* **Spearman Rank Correlation (Score vs. Binary Win/Loss):** `-0.0054`

> [!IMPORTANT]
> **Finding:** The composite score does **not** rank future outcomes. The correlations are close to zero, and the bottom quartile/non-qualified setups marginally outperformed the top quartile/qualified setups.

---

## 3. Diagnostic 2 — Score Component Analysis
Since individual component scores were not saved in the flat ledger, we analyzed the correlation of raw component inputs with 60D Net Returns:
1. **P&F Upside (`pf_upside_pct`):** Spearman: `-0.0433` (Inverse relationship. Larger targets correspond to slightly worse future returns, indicating extended markups).
2. **Momentum (`rsi_14`):** Spearman: `-0.0313` (Inverse relationship. Lower RSI is slightly better, suggesting earlier entries are preferred).
3. **Volatility Contraction (`atr_contraction_ratio`):** Spearman: `+0.0112` (Neutral/no relationship).
4. **Band Width (`bb_width_20`):** Spearman: `+0.0349` (Weakly positive relationship).
5. **Mechanical Qualification (`is_mechanically_qualified`):** Spearman: `-0.0057` (No relationship).

---

## 4. Diagnostic 3 — Wyckoff Event Performance (60D Net Horizon)

| Event Type | Sample Size | Win Rate | Average Net Return | Median Net Return | Profit Factor | Expectancy |
|---|---|---|---|---|---|---|
| **SC (Selling Climax)** | 2,968 | 53.47% | **+5.99%** | +1.65% | 1.91 | +5.99% |
| **Spring** | 5,005 | 54.53% | **+5.30%** | +2.24% | 1.85 | +5.30% |
| **SOS (Sign of Strength)** | 9,426 | 50.88% | **+4.84%** | +0.46% | 1.72 | +4.84% |
| **ST (Secondary Test)** | 3,685 | 49.82% | **+4.37%** | -0.09% | 1.63 | +4.37% |
| **UTAD (Upthrust)** | 11,575 | 48.48% | **+3.35%** | -0.75% | 1.49 | +3.35% |
| **LPS (Last Point Support)**| 25,896 | 48.81% | **+2.87%** | -0.56% | 1.40 | +2.87% |
| **AR (Automatic Rally)** | 1,674 | 48.21% | **+2.55%** | -0.89% | 1.35 | +2.55% |

> [!TIP]
> **Interpretation:** Climax, shakeout, and support-building events (SC, Spring, ST) show the strongest positive expectancy, while breakout and markup events (SOS, LPS, AR) are weaker but positive.

---

## 5. Diagnostic 4 — UTAD Paradox
The total 60D UTAD average return was positive (**+3.35%**, win rate **48.48%**, n = 11,575). However, a breakdown by year reveals extreme regime dependence:
* **2023 (Bull):** 3,089 trades | Win Rate: **69.21%** | Avg Return: **+13.47%**
* **2024 (Sideways):** 4,370 trades | Win Rate: **41.72%** | Avg Return: **+0.06%**
* **2025 (Consolidation):** 3,331 trades | Win Rate: **35.97%** | Avg Return: **-2.96%** (Highly bearish)
* **2026 (Bull):** 785 trades | Win Rate: **57.71%** | Avg Return: **+8.68%**

> [!NOTE]
> **Conclusion:** UTAD is not a "bad detector" (it generated significant losses in 2025). However, in strong bull markets, the broad index momentum (beta) overrides local distribution setups, converting UTAD candidates into temporary absorption flags rather than macro distribution tops.

---

## 6. Diagnostic 5 — Market Regime Analysis
The performance and score discrimination vary heavily by year:
* **2023 (Bull):** 11,042 trades | Win Rate: **69.28%** | Avg Net Return: **+14.60%** | Score Spearman: `-0.0112`
* **2024 (Sideways):** 20,028 trades | Win Rate: **41.21%** | Avg Net Return: **-0.21%** | Score Spearman: `-0.0071`
* **2025 (Consolidation):** 21,552 trades | Win Rate: **42.10%** | Avg Net Return: **-0.76%** | Score Spearman: `-0.0188`
* **2026 (Bull):** 7,634 trades | Win Rate: **66.05%** | Avg Net Return: **+10.86%** | Score Spearman: `-0.0138`

> [!WARNING]
> **Finding:** The Spearman correlation between composite score and future return is negative across all years, meaning the score fails to discriminate setups under both trending and consolidating regimes.

---

## 7. Diagnostic 6 — LPS-Specific Analysis & Experiment Proposal
* **LPS Baseline (60D):** 25,896 trades | Win Rate: **48.81%** | Avg Net Return: **+2.87%** | Median: **-0.56%** | PF: **1.40**
* Since we have the daily prices panel ([`historical_prices.csv`](file:///c:/Users/surya/Downloads/wyckoff-stock-screener/data/validation_results/20260826/historical_prices.csv)), we can simulate the conditional breakout trigger in a separate experiment.

### Controlled Experiment Proposal: Conditional LPS High Breakout Entry
* **A: Control Group:** Buy T+1 Open unconditionally after an LPS signal on Day T.
* **B: Treatment Group:** Buy only if subsequent daily Highs exceed the Day T High (intraday breakout trigger) within a limit window ($W = 10$ bars).
* **Breakout Safeguards:**
  * **Trigger Price:** Day T High + 1 tick.
  * **No Trigger:** If price does not break out within $W$ bars, the signal is cancelled (no trade executed).
  * **Entry Execution:** Execute at the trigger price if hit, or at T+N Open if it gaps above the trigger price.
  * **Holding Period:** 60 daily bars from the entry bar.
  * **Transaction cost:** 0.40% round-trip friction.

---

## 8. Diagnostic 7 — Distribution of Returns (60D Net Horizon)
* **Percentiles:** 
  * 25th: `-11.92%` | Median (50th): `-0.08%` | 75th: `+15.12%` | 90th: `+32.95%` | 95th: `+46.94%` | 99th: `+84.28%`
  * Mean: `+3.71%`
* **Outlier Sensitivity:**
  * **All trades:** n = 60,256 | Avg Return: **+3.71%** | Win Rate: **49.82%**
  * **No Top 1% (Returns $\le 84.28\%$):** n = 59,653 | Avg Return: **+2.54%** | Win Rate: **49.31%**
  * **No Top 5% (Returns $\le 46.94\%$):** n = 57,244 | Avg Return: **+0.12%** | Win Rate: **47.18%**

> [!NOTE]
> **Interpretation:** The positive average return is highly dependent on extreme winners. Removing the top 5% of trades reduces net returns to near-zero. This is typical of trend-following strategies (fat-tailed right skew), where large winners subsidize smaller losses.

---

## 9. Diagnostic 8 — Concentration Risk
* **Trade Concentration:** Low. The top 1% of winning trades contribute only **6.85%** to total wins profit, and the top 5% contribute **21.12%**.
* **Stock Concentration:** Low. The top-performing stock (`SILVERTUC`) generated a net profit sum of **3,269.00**, which is only 1.4% of the total net profit sum (223,532.09).
* **Date Concentration:** High. Profits are concentrated in checkpoints corresponding to 2023 and 2026 bull phases.

---

## 10. Diagnostic 9 — Survivorship / Universe Audit
* **Current universe size = 1,971:** **PASS** (Correct size matches local files).
* **Universe is current constituents:** **FAIL** (Excludes companies that went bankrupt, were delisted, or suspended during 2023–2025).
* **Ticker changes handled:** **FAIL** (Historical ticker changes are missing).
* **Corporate actions adjusted:** **PASS** (Split/dividend adjustments are handled by yfinance's default `auto_adjust=True`).
* **Historical constituent membership is point-in-time:** **FAIL** (Static constituent list).

---

## 11. Diagnostic 10 — Multiple Testing & Sample Size
* **Sample Size:** 60,256 matured outcomes at 60D.
* **95% Confidence Interval for 60D Win Rate:** `[49.43%, 50.21%]` (Standard error: 0.20%).
* **Dependency Limitation:** Checkpoints are monthly, but holding periods are 60 daily bars (~3 months), leading to a 3-checkpoint overlap. Trade outcomes are highly autocorrelated, and the effective number of independent observations is significantly lower than 60,256.

---

## 12. Final Diagnostic Scorecard

| Area | Result | Evidence | Confidence | Requires Further Testing? |
|---|---|---|---|---|
| **Overall expectancy** | **Positive** | Net expectancy is +3.71% at 60D | High | Yes (across bear markets) |
| **Win rate** | **49.82%** (60D Net) | Standard error is 0.20% | High | Yes |
| **Profit factor** | **1.53** (60D Net) | Gross is 1.61 | High | Yes |
| **Score discrimination** | **Fail** | Spearman correlation is -0.0108 | High | Yes (Score logic needs rework) |
| **Wyckoff event value**| **Spring, SC, SOS best** | Spring (+5.30%), SC (+5.99%) | High | Yes |
| **LPS predictive value**| **Positive but weaker** | LPS (+2.87%) expectancy | High | Yes (Breakout trigger study) |
| **Market regime value**| **High dependence** | Net returns negative in 2025 | High | Yes (Complete bear cycle) |
| **UTAD behavior** | **Regime dependent** | Bearish in 2025 (-2.96%), bullish in 2023 | High | Yes |
| **Outlier dependence** | **High** | Removing top 5% drops return to +0.12% | High | No (standard for momentum) |
| **Stock concentration** | **Low** | Top stock represents 1.4% of profits | High | No |
| **Survivorship bias** | **Present** | Constituents are from Aug 2026 | High | Yes (Point-in-time snapshot) |
| **Statistical robustness**| **High autocorrelation** | Trades overlap due to holding period | High | Yes |
