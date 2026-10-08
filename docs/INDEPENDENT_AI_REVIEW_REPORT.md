# Independent AI Review Report — Wyckoff NSE Stock Screener

---

## 1. Executive Verdict

**Classification: Promising but unvalidated research hypothesis — NOT a proven profitable strategy.**

The system demonstrates **positive average net expectancy at 60-day horizons (+3.71%)** with a profit factor of 1.53, but this result is **not statistically credible as evidence of a tradable edge** due to:
- Severe survivorship bias (current August 2026 universe applied historically)
- Extreme regime dependence (works only in bull markets, fails in sideways/consolidation)
- Composite score fails to discriminate returns (Spearman ρ = -0.0108)
- Heavy tail dependence (top 5% of trades contribute ~97% of average expectancy)
- No mature out-of-sample validation (only 2 trading sessions of OOS data)

**Verdict:** Do not paper trade. The system requires rigorous out-of-sample testing with survivorship-bias-free universes, regime-conditioned evaluation, and proper statistical validation before any capital allocation consideration.

---

## 2. What Is Genuinely Promising

| Component | Evidence | Assessment |
|-----------|----------|------------|
| **Disqualification gate (`is_disqualified`)** | Directionally consistent across 3/3 stocks in Phase 7; separates qualified (+3.57% to +30%) from disqualified (-7.63% to +11%) at 60D | **Strongest signal** — the only component with per-stock consistency |
| **Spring detection** | +5.30% net return, 54.53% win rate, PF 1.85 (n≈5,005) in discovery backtest | **Plausible edge** — accumulation/capitulation detection appears to capture genuine mean-reversion/bounce dynamics |
| **Selling Climax (SC) detection** | +5.99% net return, 53.47% win rate, PF 1.91 (n≈2,968) | **Plausible edge** — similar rationale to Spring; climactic volume + wide spread + down-close = panic selling absorption |
| **SOS detection** | +4.84% net return, 50.88% win rate, PF 1.72 (n≈9,426) | **Plausible edge** — breakout on volume confirms supply absorption |
| **Point-in-time validation architecture** | Zero lookahead bias verified via corruption tests (test_lookahead_bias.py) | **Methodologically sound** — the engineering correctly isolates signal generation from outcome measurement |

---

## 3. What Is Weak or Invalid

| Component | Problem | Severity |
|-----------|---------|----------|
| **Composite score (continuous)** | Spearman ρ = -0.0108 vs 60D returns; score buckets 0-49 outperformed 50-89; inverted on 2/3 stocks in Phase 7 | **Fundamentally broken as ranking tool** — should not be used for position sizing or prioritization |
| **Score thresholds (60/40/30)** | Arbitrary bands; no evidence these thresholds optimize anything; 70-79 bucket outperforms 80-89 | **Unvalidated heuristics** |
| **10D/20D horizons** | Near-random win rates (46-47%), expectancy barely positive after costs | **Not tradable** — Wyckoff setups require multi-month horizons per theory |
| **UTAD interpretation** | Positive returns in bull markets (+13.47% in 2023) but negative in consolidation (-2.96% in 2025) | **Event labels are regime-dependent** — cannot be interpreted in isolation |
| **LPS breakout trigger** | Dashboard feature only; NOT tested in historical backtest; no forward performance data | **Untested hypothesis** |
| **Peer relative strength** | Scored 0 when unavailable (correct per AGENTS.md), but 20-point weight is arbitrary; no validation shown | **Unvalidated component** |

---

## 4. Statistical Concerns

### 4.1 Sample Independence Violation
- **76,869 "observations" ≠ 76,869 independent trials**
- Monthly checkpoints on overlapping 250-bar windows create massive autocorrelation
- Step = 5 bars means 98% overlap between consecutive checkpoints
- Effective independent observations ≈ **39 (monthly) × ~50 (effective independent stocks) ≈ 1,950** — not 68,059
- All standard errors, confidence intervals, and p-values assuming n=68,059 are **wildly overstated**

### 4.2 Cross-Sectional Dependence
- All 1,971 stocks trade in the same market (NSE)
- Returns are driven by common factor (NIFTY beta)
- Treating each stock-month as independent ignores factor structure
- Portfolio-level variance would be far higher than per-trade variance suggests

### 4.3 Multiple Testing
- 7 event types × 3 horizons × multiple score bands × regime splits = dozens of implicit hypotheses
- No Bonferroni, Benjamini-Hochberg, or family-wise error correction
- "Spring works" could be a false positive from data dredging

### 4.4 Mean vs. Median Discrepancy
- 60D: Mean +3.71% vs Median -0.08% → **extreme right skew**
- Mean is not a robust estimator of central tendency here
- Median and trimmed means should be primary metrics
- Profit factor of 1.53 is driven by outliers

### 4.5 Tail Sensitivity (Confirmed)
| Exclusion | Avg 60D Net Return | Interpretation |
|-----------|-------------------|----------------|
| None | +3.71% | Headline figure |
| Top 1% | +2.54% | -32% drop |
| Top 5% | +0.12% | **Essentially zero** |
| Top 10% | Likely negative | Strategy collapses without extreme winners |

This is characteristic of **lottery-ticket payoff structures**, not consistent skill.

---

## 5. Backtest Methodology Concerns

### 5.1 Lookahead Bias — **Correctly Addressed**
- `df.iloc[:t+1]` slicing verified by corruption tests
- Signal generation uses only data ≤ T
- Forward returns computed from T+1 onward
- **No lookahead leakage detected in code**

### 5.2 Survivorship Bias — **Critical Failure**
- Universe = current August 2026 NSE constituents (1,971 stocks)
- Backtest runs June 2023 → August 2026 on this static list
- **Delisted, bankrupt, merged, suspended stocks are EXCLUDED**
- In Indian markets, ~10-15% of listed stocks delist/merge over 3 years
- These are precisely the stocks most likely to generate large negative returns
- **Direction of bias: UPWARD** — results are optimistically biased
- Phase 22 pre-discovery test (Jun 2022–May 2023) used **same biased universe** (403 stocks excluded for lack of history)

### 5.3 Selection Bias
- No evidence the 1,971 stocks are representative of NSE
- Liquidity filter (`min_avg_turnover_cr ≥ 1.0`) introduces additional selection
- Stocks with data gaps excluded → survival bias within survivors

### 5.4 Entry/Exit Model
- **Entry: T+1 Open** — reasonable but assumes fills at open (slippage risk)
- **Exit: Fixed horizons (10/20/60 bars)** — no trailing stops, no time-stop logic, no structural exits
- **0.40% round-trip friction** — reasonable for liquid NSE stocks but ignores:
  - Bid-ask spread (wider for small caps)
  - Market impact (not modeled)
  - STT, exchange fees, GST (included in 0.40%?)

### 5.5 Duplicate/Correlated Observations
- Same stock appears at multiple monthly checkpoints
- Same calendar month across stocks = single market regime observation
- Standard errors should be clustered by (stock, month) or (month)

---

## 6. Survivorship Bias Assessment

### Severity: **SEVERE — Invalidates Historical Backtest as Proof of Edge**

**Quantitative Estimate:**
- NSE delisting rate: ~3-5% per year (conservative)
- Over 3 years: ~10-15% of universe disappears
- These stocks typically underperform before delisting
- Academic literature (e.g., Elton et al. 1996; Shumway 1997) shows survivorship bias adds **+1% to +4% annually** to equity strategy returns
- For a strategy claiming +3.71% per 60D (~22% annualized), survivorship bias could explain **50-100% of the apparent edge**

### Practical Remediation Required:
1. **Point-in-time NSE constituent snapshots** — monthly/quarterly index membership from NSE or vendor (NSE Indices, Refinitiv, Bloomberg)
2. **Delisted stock data** — require historical OHLCV for removed symbols
3. **Alternative: Use index membership** — backtest only NIFTY 500 / NIFTY Total Market index constituents at each date
4. **At minimum: Document the bias** — every report must state "Subject to survivorship bias; not a bias-free backtest"

**Current mitigation in code:** `SURVIVORSHIP_BIAS_WARNING` constant in models.py — **correct disclosure but does not fix the problem**.

---

## 7. Regime Dependence Assessment

### Evidence:
| Period | Market Character | 60D Gross Return | Win Rate | N |
|--------|------------------|------------------|----------|---|
| 2023 | Strong bull | +15.00% | 70.00% | 11,042 |
| 2024 | Sideways/flat | +0.19% | 41.88% | 20,028 |
| 2025 | Consolidation | -0.36% | 43.01% | 21,552 |
| 2026 | Bull | +11.26% | 67.15% | 7,634 |

### Interpretation:
- The screener is **long beta** — it selects stocks that move with the market
- In bull markets: Wyckoff accumulation patterns align with broad uptrend → false attribution of skill
- In sideways markets: Patterns fail or produce whipsaws → no edge over buy-and-hold
- **UTAD paradox** confirms this: bearish pattern generates bull returns in bull markets

### Critical Question Unanswered:
> Does the screener add alpha **above NIFTY/NIFTY 500** after controlling for beta?

No benchmark comparison shown in Phase 17 results. The "BENCHMARK" tab in engine.py compares to universe equal-weighted mean, not a proper factor model.

---

## 8. Score System Assessment

### Current Design (100 points):
| Component | Weight | Problem |
|-----------|--------|---------|
| Mechanical Filters | 30 | Binary pass/fail; no gradation |
| Schematic Recency | 40 | Heuristic decay curves; no optimization |
| Peer Rank | 20 | Linear decay; arbitrary weight |
| P&F Upside | 10 | Tiered thresholds (≥20%/≥10%/>0%); arbitrary |

### Evidence Against Predictive Validity:
1. **Spearman ρ = -0.0108** — effectively zero monotonic relationship
2. **Score bucket inversion** — 0-49 bucket beat 50-89 buckets
3. **Per-stock failure** — 2/3 stocks showed high scores underperforming low scores
4. **No out-of-sample validation** of score-weighting scheme

### Root Cause Hypothesis (from AGENTS.md):
> High scores capture "how extended an already-mature move is" rather than "upside remaining"

This is plausible: mechanical filters + fresh bullish events + high peer rank + high P&F target = late-stage momentum, not early accumulation.

### Recommendation:
- **Reduce composite score to binary gate only**: `qualified (score ≥ 40) vs disqualified`
- **Do not re-weight** on current data — sample size and bias preclude reliable optimization
- **Test components independently** in controlled experiments

---

## 9. Spring/SC/SOS Assessment

### Spring (+5.30%, WR 54.53%, PF 1.85, n≈5,005)
- **Strengths**: Large sample, consistent with Wyckoff theory (undercut + reclaim = supply absorption)
- **Concerns**:
  - No regime-conditioned analysis shown (does it work in 2024/2025?)
  - No tail-trimming analysis (is PF driven by outliers?)
  - Definition uses simple min(Low) over 50 bars as "support" — in strong trends this is not valid support
  - No control for market beta (Spring in bull market = buy the dip)

### SC (+5.99%, WR 53.47%, PF 1.91, n≈2,968)
- **Strengths**: Clear quantitative definition (wide spread + high volume + down-close + prior decline)
- **Concerns**: Same as Spring — regime dependence untested

### SOS (+4.84%, WR 50.88%, PF 1.72, n≈9,426)
- **Strengths**: Breakout on volume is a classic momentum signal
- **Concerns**: Win rate barely >50%; may just be "buy breakouts in bull market"

### Required Tests Before Trusting:
1. **Regime-stratified performance** (bull vs sideways vs bear)
2. **Winsorized/trimmed mean returns** at 1%, 5%, 10%
3. **Beta-adjusted returns** (regress on NIFTY 500)
4. **Permutation test**: Shuffle event labels across time — does edge persist?
5. **Minimum holding period analysis**: Does edge require full 60D or emerge earlier?

---

## 10. LPS Breakout Assessment

### Current State:
- **Dashboard feature only** — conditional trigger at LPS bar high
- Structural R:R calculation using support/anchor low (not 5% fixed stop)
- Example: HINDCOPPER showed ~1:7.29 structural R:R

### Critical Gaps:
1. **Zero historical backtest** — original backtest used T+1 Open entry, not LPS breakout
2. **No forward test data** — cannot evaluate hit rate of trigger, time-to-trigger, false breakout rate
3. **No position sizing model** — R:R is theoretical; actual risk depends on entry fill
4. **Structural stop vs 5% stop confusion** — code says "reference risk management" is separate but dashboard mixes them

### Required Experiment:
```
Controlled backtest with:
- Entry: Next bar Open after LPS breakout trigger (high > LPS high)
- Stop: Structural support (trading range low)
- Target: P&F objective
- Compare vs: T+1 Open entry (current baseline)
- Metrics: Win rate, expectancy, MFE/MAE, time in trade, fill rate at trigger
```

**Do not deploy live until this experiment completes.**

---

## 11. OOS Methodology Assessment

### Current Design:
- **Firewall date**: August 24, 2026
- **OOS period begins**: August 25, 2026
- **Data acquired**: 2 trading sessions (Aug 25-26, 2026)
- **Maturity requirement**: 10/20/60 trading sessions for 10D/20D/60D horizons

### Status: **NOT TESTABLE YET**
- 60D horizon requires ~3 calendar months of data
- Earliest 60D evaluation: ~November 2026
- Any "OOS results" before then are **premature and invalid**

### Hidden Leakage Risks:
| Risk | Assessment |
|------|------------|
| Universe changes | Same 1,971 symbols — no new IPOs, delistings handled? |
| Parameter tuning | Phase 22 pre-discovery test used same thresholds — no re-optimization on OOS |
| Human review | TradingView links generated but manual review not yet recorded |
| Data revision | Yahoo Finance adjusts splits/dividends — historical data may change |

### Correct Protocol:
1. **Lock all parameters** (thresholds, weights, rules) at firewall date
2. **Pre-register analysis plan** (this review serves as partial pre-registration)
3. **Wait for full maturity** (60 trading sessions minimum)
4. **Run single OOS evaluation** — no iterative tweaking

---

## 12. Recommended Baselines

### Minimum Required Comparisons:
| Baseline | Purpose |
|----------|---------|
| **Buy-and-hold NIFTY 50** | Market beta benchmark |
| **Buy-and-hold NIFTY 500** | Broad market benchmark |
| **Equal-weight universe** | Current "BENCHMARK" tab (universe mean) |
| **Random stock selection** | Monte Carlo: pick N random stocks monthly, measure 60D return |
| **Simple momentum** | Top 20% 6-month performers, monthly rebalance |
| **Simple mean-reversion** | RSI < 30 bounce, monthly |
| **Spring-only strategy** | Enter on Spring detection, exit at 60D |
| **SC-only strategy** | Enter on SC detection, exit at 60D |
| **Spring + SC combined** | Union of both events |
| **Current full screener** | All categories combined |

### Statistical Framework:
- **Primary metric**: 60D net return (after 0.40% friction)
- **Inference unit**: Monthly checkpoint (not individual trade)
- **Test**: Paired t-test / Wilcoxon signed-rank on monthly excess returns vs baseline
- **Minimum OOS period**: 12 months (12 monthly checkpoints = 12 independent observations)

---

## 13. Recommended Statistical Tests

| Test | Purpose | Implementation |
|------|---------|----------------|
| **Block bootstrap** (by month) | Valid CIs accounting for autocorrelation | Resample months with replacement, recompute mean 60D return |
| **Permutation test** (event labels) | Is Spring/SC edge real or chance? | Shuffle event dates across time, recompute performance |
| **Winsorized mean** (1%, 5%) | Robust expectancy estimate | Trim extremes, report trimmed mean + CI |
| **Quantile regression** | Tail behavior | Model 90th/95th percentile of returns |
| **Factor regression** (NIFTY 500, size, value, momentum) | Alpha after risk adjustment | Monthly portfolio returns regressed on factors |
| **Clustered standard errors** | Correct inference | Cluster by month and/or stock |
| **Multiple testing correction** (Benjamini-Hochberg) | Control false discoveries | Apply to all event/horizon/regime tests |
| **Out-of-sample R² / MSE** | Predictive validity | Compare predicted vs realized returns |

---

## 14. Exact Phase 21 Validation Protocol

### Phase 21A: Data Maturity (Current — Wait)
- **Action**: Do nothing. Wait for 60 trading sessions post-August 24, 2026.
- **Target date**: ~November 2026 for first 60D evaluation.

### Phase 21B: Survivorship-Bias-Free Universe Construction (Parallel)
- **Source**: NSE Indices historical constituent data (NIFTY 500 / NIFTY Total Market)
- **Frequency**: Monthly snapshots
- **Coverage**: All EQ series stocks, including delisted
- **Deliverable**: `universe/pit_constituents_YYYYMMDD.csv` for each signal date

### Phase 21C: Regime-Conditioned OOS Evaluation (When Mature)
```python
# Pre-registered analysis plan:
1. Load OOS signals (Aug 25, 2026 → maturity date)
2. Compute 10D/20D/60D net returns per signal
3. Stratify by:
   - Candidate category (HP, Qualified, Watchlist, Disqualified)
   - Most recent event (Spring, SC, SOS, LPS, UTAD, None)
   - Market regime (NIFTY 50 50DMA > 100DMA = bull, else not)
   - Score band (<40, 40-59, 60-79, 80+)
4. Primary comparison: Qualified vs Disqualified at 60D (paired by month)
5. Secondary: Spring/SC/SOS vs No-Event at 60D
6. Benchmark: Excess return vs NIFTY 500 (monthly)
7. Robustness: Winsorized at 5%, trimmed at 5%, median
8. Statistical test: Clustered (by month) t-test on monthly alpha
```

### Phase 21D: Component Isolation Experiments
| Experiment | Design |
|------------|--------|
| Mechanical filters only | Score = mechanical filters (30 pts), ignore events/peer/P&F |
| Events only | Score = schematic recency (40 pts), ignore others |
| Spring-only strategy | Enter on Spring, exit 60D, no other filters |
| SC-only strategy | Enter on SC, exit 60D, no other filters |
| Disqualification gate only | Binary: disqualified vs not, no scoring |

---

## 15. PASS/FAIL Criteria (Pre-Registered)

### PASS (All Must Hold):
| Criterion | Threshold | Rationale |
|-----------|-----------|-----------|
| **Positive 60D net expectancy** | > 0% after 0.40% friction | Minimum viability |
| **95% CI excludes zero** | Clustered bootstrap CI | Statistical significance |
| **Qualified > Disqualified at 60D** | Δ > 0, p < 0.05 (paired monthly) | Gate validity |
| **Spring/SC edge survives regime control** | Positive in bull AND not severely negative in sideways | Not pure beta |
| **Tail robustness** | 5% winsorized mean > 0.5% | Not lottery tickets |
| **Max drawdown < 25%** | 60D MAE / portfolio DD | Risk control |
| **Beats NIFTY 500** | Monthly alpha > 0, p < 0.10 | Adds value |
| **Sufficient independent opportunities** | ≥ 12 monthly checkpoints with ≥ 10 qualified signals each | Sample adequacy |

### FAIL (Any Triggers Redesign/Reject):
| Condition | Action |
|-----------|--------|
| 60D net expectancy ≤ 0 after costs | **Reject** — no edge |
| Qualified ≤ Disqualified at 60D | **Redesign** — gate inverted |
| Edge vanishes in sideways market (2024/2025 analogue) | **Redesign** — regime filter needed |
| Top 5% winsorized mean ≤ 0 | **Reject** — lottery tickets only |
| OOS Sharpe < 0.5 (annualized) | **Reject** — poor risk-adjusted |
| Survivorship-bias-free backtest reverses edge | **Reject** — bias was the edge |

---

## 16. What Should NOT Be Changed Yet

| Component | Reason |
|-----------|--------|
| **Event detection logic** (SC/AR/ST/Spring/LPS/SOS/UTAD) | Core domain logic; frozen per AGENTS.md; tests pass |
| **VSA metrics** (volume_ratio, spread_ratio, close_position) | Quantified per AGENTS.md; validated |
| **P&F construction** (Fraser method) | Correct implementation; fallback labeled |
| **Point-in-time validation engine** | Zero lookahead verified; architecture sound |
| **Disqualification flags** (UTAD, no base, all mechanical failed) | Only consistently validated signal |
| **Data validation pipeline** | Robust; handles Yahoo/TradingView formats |

---

## 17. What Should Eventually Be Redesigned

| Component | Redesign Direction |
|-----------|-------------------|
| **Composite score** | Replace with binary qualification + event-type flags; continuous score is misleading |
| **Mechanical filters** | Test each independently; consider continuous scoring (distance from MA, RSI level) |
| **Peer analysis** | Validate Bogomazov slope comparison; test if it adds incremental info |
| **P&F upside scoring** | Tiered thresholds arbitrary; test continuous upside % or log-transform |
| **Universe construction** | Build point-in-time NSE constituent database (critical for credible backtests) |
| **Regime filter** | Add explicit market regime classifier (bull/sideways/bear) as gate or weight modifier |
| **Position sizing / risk model** | Replace fixed 5% stop with structural stops; add portfolio heat/leverage limits |
| **Exit logic** | Test structural exits (UTAD, trend break) vs fixed horizons |

---

## 18. Final Recommendation

### **CONTINUE RESEARCH — But With Strict Discipline**

**Do NOT:**
- Paper trade or live trade any version of this system
- Optimize weights/thresholds on discovery or pre-discovery data
- Treat composite score as meaningful ranking
- Ignore survivorship bias in any report or presentation

**DO:**
1. **Build point-in-time NSE universe** (Phase 21B) — this is the highest-impact fix
2. **Wait for OOS maturity** (November 2026+) — no premature evaluation
3. **Run pre-registered Phase 21C protocol** — single evaluation, no iteration
4. **Test component isolation** (Phase 21D) — find what actually drives edge
5. **Add regime conditioning** — the system likely needs a market-state filter
6. **Publish negative results honestly** — if OOS fails, document why and stop

### Personal Capital Allocation Answer:
> **If this were my own money, I would need to see:**
> 1. A survivorship-bias-free backtest over ≥ 5 years (including 2020 COVID crash, 2022 bear)
> 2. Positive 60D net expectancy in OOS period (6+ months live)
> 3. Qualified > Disqualified holding in OOS with p < 0.05
> 4. 5% winsorized mean > 1% per 60D trade
> 5. Maximum portfolio drawdown < 20% in stress periods
> 6. Beats NIFTY 500 on risk-adjusted basis (Sharpe > 1.0)
>
> **Without ALL of the above: $0 allocation.**

---

## Summary for Decision Makers

| Question | Answer |
|----------|--------|
| Is there a statistical edge? | **Inconclusive** — positive mean but median ≤ 0, severe bias, regime dependence |
| Is the composite score useful? | **No** — use only binary disqualification gate |
| Which events show promise? | **Spring, SC, SOS** — but untested in bear/sideways regimes |
| Is LPS breakout ready? | **No** — zero validation |
| When can we trust OOS? | **November 2026 earliest** (60D maturity) |
| Biggest risk? | **Survivorship bias + regime dependence = illusory edge** |

**Bottom line**: The engineering is solid, the domain implementation is faithful to Wyckoff/VSA theory, and the validation architecture correctly prevents lookahead bias. But the *statistical evidence for a tradable edge does not yet exist*. Treat this as a **research prototype requiring rigorous out-of-sample validation**, not a trading system.
