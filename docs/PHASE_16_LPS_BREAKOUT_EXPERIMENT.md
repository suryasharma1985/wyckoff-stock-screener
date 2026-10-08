# Phase 16D: LPS Breakout Experiment Report

**Date:** 2026-08-26  
**Backtest ID:** `backtest_nse_eq_monthly_20260826`  

---

## 1. LPS Execution Models
We evaluated three historical execution rules for the **29,057** detected LPS signals:
* **Model A (Baseline):** Entry is executed unconditionally on the next trading day Open (T+1 Open).
* **Model B (Breakout):** Entry is executed strictly if the daily High on any day within a 10-day window ($T+1$ to $T+10$) exceeds the signal bar's High (Day T High). Execution occurs at `max(Open_{T+k}, High_T)` to handle opening gaps.
* **Model C (Conservative Close Breakout):** Entry is executed strictly if the daily Close on any day within the 10-day window exceeds the signal bar's High. Execution occurs at the Open of the following day ($T+k+1$ Open).

---

## 2. Experimental Results (Net of Friction)

### 10-Day Horizon (10D Net)
* **Model A:** 28,246 trades | Participation: **97.21%** | Win Rate: **45.91%** | Avg Net Return: **+0.47%** | Median: **-0.74%** | PF: **1.15** | Expectancy: **+0.47%**
* **Model B:** 23,613 trades | Participation: **81.26%** | Win Rate: **44.09%** | Avg Net Return: **+0.14%** | Median: **-1.11%** | PF: **1.04** | Expectancy: **+0.14%**
* **Model C:** 18,114 trades | Participation: **62.34%** | Win Rate: **43.54%** | Avg Net Return: **+0.02%** | Median: **-1.30%** | PF: **1.00** | Expectancy: **+0.02%**

### 20-Day Horizon (20D Net)
* **Model A:** 27,436 trades | Participation: **94.42%** | Win Rate: **45.60%** | Avg Net Return: **+0.68%** | Median: **-1.08%** | PF: **1.15** | Expectancy: **+0.68%**
* **Model B:** 22,882 trades | Participation: **78.75%** | Win Rate: **44.13%** | Avg Net Return: **+0.39%** | Median: **-1.49%** | PF: **1.08** | Expectancy: **+0.39%**
* **Model C:** 17,610 trades | Participation: **60.61%** | Win Rate: **45.13%** | Avg Net Return: **+0.65%** | Median: **-1.37%** | PF: **1.14** | Expectancy: **+0.65%**

### 60-Day Horizon (60D Net)
* **Model A:** 25,896 trades | Participation: **89.12%** | Win Rate: **48.82%** | Avg Net Return: **+2.87%** | Median: **-0.56%** | PF: **1.40** | Expectancy: **+2.87%**
* **Model B:** 21,723 trades | Participation: **74.76%** | Win Rate: **47.01%** | Avg Net Return: **+2.12%** | Median: **-1.37%** | PF: **1.28** | Expectancy: **+2.12%**
* **Model C:** 16,829 trades | Participation: **57.92%** | Win Rate: **48.02%** | Avg Net Return: **+2.49%** | Median: **-1.05%** | PF: **1.34** | Expectancy: **+2.49%**

---

## 3. Analysis & Key Insights

> [!CAUTION]
> **Key Finding:** The conditional breakout entry models (Model B & C) **underperformed** the simple unconditional next-day Open entry model (Model A) across all horizons.

### Why Breakout Triggers Underperformed:
1. **Entry Price Drag:** Waiting for the breakout forces the entry at a higher price level (exceeding the Day T High). This structural entry price markup degrades the remaining upside compared to buying at the lower range.
2. **False Breakout Whipsaws:** Intraday or close-based breakouts are frequently brief spikes that pull back immediately, trapping breakout buyers at local swing highs.
3. **Missed Opportunity Cost:** Models B & C skip 11% to 42% of trades due to missing triggers. In an upward-trending market, skipping these trades degrades average expectancy.
