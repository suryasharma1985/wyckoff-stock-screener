# Phase 16: Controlled Edge Validation & Execution Experiments Final Report

**Date:** 2026-08-26  
**Backtest ID:** `backtest_nse_eq_monthly_20260826`  

---

## 1. Executive Summary
This report summarizes the experimental diagnostics and simulations conducted on the Phase 15/17 backtest outcomes (68,059 signals across 1,971 stocks from 2023-06-01 to 2026-08-24). The frozen analytical engine was strictly respected throughout.

### Key Discoveries:
1. **Event-Level Edge Confirmed:** Bottom capitulation setups (Spring and Selling Climax) show strong positive net expectancy (+5.30% and +5.99% net) with profit factors $\ge 1.85$.
2. **Breadth Regime Selectivity:** Springs and SCs perform exceptionally well during **Bear market breadth regimes (capitulations)** (+9.36% and +5.72% net return), but lose money during sideways chop (Neutral breadth).
3. **Composite Score Failure:** The scoring weights fail to discriminate setup quality (Spearman `-0.0108` correlation). Qualified setups (+3.41%) underperform non-qualified ones (+3.74%).
4. **LPS Breakout Execution Destroys Value:** Simulating the proposed conditional breakout entry rules (Model B & C) degraded performance compared to a simple, next-day Open entry (Model A) due to entry price drag (markup) and whipsaws.

---

## 2. Final Diagnostic Scorecard

| Area | Result | Evidence | Confidence | Requires Further Testing? |
|---|---|---|---|---|
| **Data integrity** | **GREEN** | Exact match with local CSV files; 100% reconstructable | High | No |
| **Lookahead safety** | **GREEN** | Slit-by-date operations prevent future data leakage | High | No |
| **Survivorship bias** | **RED** | Static August 2026 constituent snapshot used; delisted stocks missing | High | Yes (Point-in-time universe) |
| **Overall expectancy** | **GREEN** | Net 60D return of +3.71% with profit factor of 1.53 | High | Yes (Across a bear cycle) |
| **Event robustness** | **GREEN** | Spring (+5.30% net) and SC (+5.99% net) are highly robust | High | Yes |
| **Score discrimination** | **RED** | Spearman correlation of -0.0108; score bucket returns non-monotonic | High | Yes (Re-weight scoring formula) |
| **Regime robustness** | **YELLOW** | Extreme regime concentration; net returns are negative in 2025 | High | Yes |
| **Fat-tail dependency** | **YELLOW** | Removing top 5% of trades drops net returns to +0.12% | High | No (Standard for momentum) |
| **LPS breakout viability**| **RED** | Breakout entries (Model B/C) underperformed baseline Open entries | High | Yes |
| **Statistical robustness**| **YELLOW** | Checkpoints overlap, introducing autocorrelation | High | Yes |

### **FINAL RESEARCH CONCLUSION:**
* **Screener shows a conditional edge but requires refinement (YELLOW/GREEN).** The underlying Wyckoff event detectors (Spring, SC) capture real market-breadth capitulation capitulations. However, the composite scoring logic and the dashboard breakout rules degrade returns and should not be deployed to production as currently designed.

---

## 3. Answers to the 10 Key Questions

### Q1. Does the current screener demonstrate a positive historical expectancy?
**Yes.** The baseline strategy has a net average 60D return of **`+3.71%`** with a net profit factor of **`1.53`** (net of 0.40% round-trip friction).

### Q2. Does the composite score actually improve trade selection?
**No.** Spearman correlation is **`-0.0108`**. Top quartile setups (+3.05% net) underperformed bottom quartile setups (+3.30% net). The scoring system is ineffective for ranking.

### Q3. Which Wyckoff events appear genuinely useful?
* **Spring:** Avg Net **`+5.30%`** | PF **1.85** | Win Rate **54.53%** (n = 5,005)
* **SC (Selling Climax):** Avg Net **`+5.99%`** | PF **1.91** | Win Rate **53.47%** (n = 2,968)
* *Note:* LPS (`+2.87%`) and AR (`+2.55%`) are significantly weaker.

### Q4. Is the apparent edge robust after removing extreme winners?
**No, it is highly sensitive to outliers.** Excluding the top 1% of winners reduces average return to **`+2.54%`**. Excluding the top 5% reduces it to **`+0.12%`**. This positive-skew profile is characteristic of trend-following strategies.

### Q5. How strongly does market regime affect performance?
**Extremely strongly.** The strategy generated +14.60% net return in 2023, but lost money (**`-0.76%`**) during the sideways consolidation of 2025.

### Q6. Is UTAD actually harmful, neutral, or useful depending on regime?
**Regime-dependent.** In the 2025 consolidation market, UTAD was a highly effective bearish signal (**`-2.96%`** return, 35.97% win rate). In the 2023 bull market, it was overridden by trend beta and was bullish (**`+13.47%`**).

### Q7. Does LPS deserve a dedicated execution experiment?
**Yes.** However, our offline experiment shows that conditional breakout entries (Model B: +2.12% net, Model C: +2.49% net) underperform the baseline Open entry (Model A: +2.87% net) due to entry price markup drag and breakout whipsaws.

### Q8. What is the single biggest weakness discovered by this backtest?
**The scoring logic weights.** High P&F upside and momentum are inversely related to performance because they select late-stage, extended setups.

### Q9. What is the single strongest evidence that the screener may have genuine edge?
**The outperformance of Springs and Selling Climaxes in Bear breadth regimes.** Buying Springs during capitulations yielded a net average return of **`+9.36%`** with a **63.22%** win rate (n = 3,225).

### Q10. What MUST be tested next before changing any production logic?
1. **Scoring Formula Optimization:** Run an out-of-sample optimization to re-weight setup scoring.
2. **Point-in-Time Universe Integration:** Acquire index revisions to quantify the survivorship bias decay.
