# Phase 16F: Market Regime Breadth Analysis Report

**Date:** 2026-08-26  
**Backtest ID:** `backtest_nse_eq_monthly_20260826`  

---

## 1. Breadth-Based Regime Classification
We classified checkpoints using **Market Breadth** (percentage of universe stocks trading above their 50-day DMA):
* **Bull Regime (Breadth $\ge 60\%$):** 25,170 signal observations.
* **Neutral/Sideways Regime ($30\% \le \text{Breadth} < 60\%$):** 23,091 signal observations.
* **Bear/Correction Regime (Breadth $< 30\%$):** 19,798 signal observations (representing market-wide corrections or capitulations).

---

## 2. Event Performance by Breadth Regime (60D Net Horizon)

### Spring (Shakeout)
* **Bear Regime (Capitulation):** n = 3,225 | Average Net Return: **`+9.36%`** | Win Rate: **63.22%**
* **Bull Regime (Uptrend):** n = 428 | Average Net Return: **`+4.35%`** | Win Rate: **50.00%**
* **Neutral Regime (Sideways):** n = 1,352 | Average Net Return: **`-4.09%`** | Win Rate: **35.21%** (Loss-making)

### SC (Selling Climax)
* **Bear Regime (Capitulation):** n = 1,030 | Average Net Return: **`+5.72%`** | Win Rate: **58.74%**
* **Bull Regime (Uptrend):** n = 1,244 | Average Net Return: **`+0.84%`** | Win Rate: **45.58%**
* **Neutral Regime (Sideways):** n = 1,011 | Average Net Return: **`+0.51%`** | Win Rate: **44.91%**

### LPS (Last Point of Support)
* **Bear Regime:** n = 10,336 | Average Net Return: **`+3.49%`** | Win Rate: **51.34%**
* **Bull Regime:** n = 8,032 | Average Net Return: **`+6.44%`** | Win Rate: **54.25%**
* **Neutral Regime:** n = 7,528 | Average Net Return: **`-1.80%`** | Win Rate: **39.53%** (Loss-making)

---

## 3. Analysis & Key Insights

> [!TIP]
> **Key Finding:** Springs and Selling Climaxes demonstrate extreme edge during **Bear breadth regimes (capitulations)**, while they suffer severe whipsaws during **Neutral/Sideways consolidations**.

### Strategic Implications:
1. **Wyckoff Core Logic Confirmed:** Springs (shakeouts under support) and Selling Climaxes (panic selling exhaustion) perform exactly as designed: they capture the absorption of supply during broad market panic. Buying into these events during bear breadth phases yields a **+9.36%** net expectancy (Spring) and **+5.72%** (SC).
2. **Neutral Regime Hazard:** During sideways, choppy index conditions (Neutral breadth), support levels are frequently broken and tested repeatedly, leading to whipsaws and negative expectancy (Spring: -4.09%).
3. **Execution Filter Hypothesis:** A market breadth filter (e.g., restricted buying of Springs to Bear/Correction regimes, and SOS/LPS to Bull regimes) would dramatically improve strategy performance.
