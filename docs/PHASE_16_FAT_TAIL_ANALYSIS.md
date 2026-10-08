# Phase 16G: Fat-Tail & Concentration Analysis Report

**Date:** 2026-08-26  
**Backtest ID:** `backtest_nse_eq_monthly_20260826`  

---

## 1. Outlier Sensitivity Analysis (60D Net Horizon)
We evaluated the impact of removing the top-performing trades on the overall net return profile:
* **All Trades:** n = 60,256 | Average Net Return: **`+3.71%`** | Win Rate: **49.82%**
* **Excluding Top 0.1% of Trades:** n = 60,195 | Average Net Return: **`+3.46%`** | Win Rate: **49.77%**
* **Excluding Top 0.5% of Trades:** n = 59,954 | Average Net Return: **`+2.99%`** | Win Rate: **49.56%**
* **Excluding Top 1.0% of Trades:** n = 59,653 | Average Net Return: **`+2.54%`** | Win Rate: **49.31%**
* **Excluding Top 2.0% of Trades:** n = 59,050 | Average Net Return: **`+1.81%`** | Win Rate: **48.79%**
* **Excluding Top 5.0% of Trades:** n = 57,243 | Average Net Return: **`+0.12%`** | Win Rate: **47.18%** (Expectancy falls to near-zero)

---

## 2. Trade Concentration (Wins Profit Share)
We analyzed how much of the positive trade returns were driven by specific outlier trades:
* **Top 10 Trades:** Combined Profit: **`5,502.57%`** (representing **2.46%** of total net strategy profit)
* **Top 50 Trades:** Combined Profit: **`13,329.85%`** (representing **5.96%** of total net strategy profit)
* **Top 100 Trades:** Combined Profit: **`20,604.72%`** (representing **9.22%** of total net strategy profit)
* **Top 1% Wins Share:** The top 1% of winning trades accounted for **`6.85%`** of total positive profit.
* **Top 5% Wins Share:** The top 5% of winning trades accounted for **`21.12%`** of total positive profit.
* **Top 10% Wins Share:** The top 10% of winning trades accounted for **`33.66%`** of total positive profit.

---

## 3. Stock-Level Concentration
The top 5 individual symbols contributing to the total net strategy profit (60D):
1. `SILVERTUC`: **+3,269.00%** (1.46% of total profit)
2. `CUPID`: **+1,899.97%** (0.85% of total profit)
3. `SKYGOLD`: **+1,399.52%** (0.63% of total profit)
4. `SIGMAADV`: **+1,239.64%** (0.55% of total profit)
5. `INDOTHAI`: **+1,114.23%** (0.50% of total profit)

---

## 4. Edge Profile Classification

> [!NOTE]
> **Classification:** **MODERATE CONCENTRATION (Right-Skewed Trend Edge)**

The strategy's positive expectancy (+3.71% net) is **not** caused by 1 or 2 lottery-like stocks (the top stock contributes only 1.46%, and the top 100 trades represent less than 10% of total net profits). Rather, it relies on a broad right-skewed distribution where the top 5% of trades account for a significant portion (21.12%) of positive returns. This is a standard and healthy profile for trend-following and momentum strategies.
