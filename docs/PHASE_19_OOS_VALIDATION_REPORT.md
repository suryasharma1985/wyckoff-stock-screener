# Phase 19: Out-of-Sample Validation & Survivorship-Bias Audit Report

**Date:** 2026-08-26  
**OOS Validation Status:** **OOS STATUS = NOT TESTABLE**  
**Validation Runner:** [`scripts/run_phase19_oos_validation.py`](file:///c:/Users/surya/Downloads/wyckoff-stock-screener/scripts/run_phase19_oos_validation.py)  
**Diagnostics Directory:** [`data/diagnostics/phase19/`](file:///c:/Users/surya/Downloads/wyckoff-stock-screener/data/diagnostics/phase19/)  

---

## 1. Out-of-Sample Dataset Audit
* **Available Universe:** 1,971 active NSE equities.
* **Available Date Range:** 2023-01-02 through 2026-08-24.
* **Out-of-Sample Data Availability:** **None**. The local dataset ends on 2026-08-24. Genuinely unseen market data after the cutoff date is completely missing.
* **Action taken:** **OOS execution stopped**. No discovery data was substituted, and no random train/test split of the consumed history was used, preserving lookahead safety and research integrity.

---

## 2. Survivorship-Bias & point-in-time Audit
* **Historical Constituent Revisions:** **NOT AVAILABLE**. The repository has no index membership logs for Nifty 50 / Nifty 500 across 2023–2025.
* **Delisted/Acquired Stocks:** Delisted companies are **absent** from the dataset.
* **Corporate Actions:** Corporate action dividends and splits are adjusted, but ticker changes and mergers are not point-in-time represented.
* **Audit Verdict:** **SURVIVORSHIP-FREE VALIDATION = NOT AVAILABLE**. The current testing universe is heavily survivorship-biased.

---

## 3. Frozen Hypothesis Manifest
The following parameters are frozen for validation once fresh out-of-sample data is loaded:
* **Validation Universe:** 1,971 active NSE equities.
* **Validation Period:** Genuinely unseen temporal period post-`2026-08-24` (e.g. September 2026 through the present).
* **Friction Cost:** 0.40% round-trip friction.
* **Entry Execution:** Unconditional next-day Open entry (Model A).
* **Exit Horizons:** 10D, 20D, and 60D holding windows.
* **Event Definitions:** Frozen schematic event detectors (Spring, SC, SOS, LPS, ST, AR, UTAD).
* **H0 (Baseline Expectancy):** Strategy has positive net expectation (+3.71% net at 60D).
* **H1 (Early Accumulation):** Group A (Spring/SC/SOS) outperforms Group B (LPS/AR/ST/UTAD) (+5.17% vs +3.12% net).
* **H2 (Bear Breadth Gate):** Spring/SC setups have exceptional edge (+9.36% net) if breadth is $< 30\%$.
* **H3 (Neutral Regime Avoidance):** Strategy loses money (expectancy `-1.00%` net) if breadth is $30\% \le \text{breadth} < 60\%$.
* **H4 (LPS Baseline):** Next-day Open LPS entries are positive but weaker.
* **H5 (LPS Breakout Control):** LPS breakout triggers (Model B/C) underperform baseline Open entries (Model A).
* **H6 (Composite Score):** Composite score fails to rank setup outcomes (Spearman correlation $\approx 0.0$).

---

## 4. Master Comparison Table: Discovery vs. OOS

| Metric | Discovery | Out-of-Sample (OOS) | Difference | Status |
|---|---|---|---|---|
| **60D Net Expectancy** | +3.71% | `NOT TESTABLE` | `NOT TESTABLE` | `NOT TESTABLE` |
| **60D Net Win Rate** | 49.82% | `NOT TESTABLE` | `NOT TESTABLE` | `NOT TESTABLE` |
| **60D Net Profit Factor** | 1.53 | `NOT TESTABLE` | `NOT TESTABLE` | `NOT TESTABLE` |
| **Spring 60D Return** | +5.30% | `NOT TESTABLE` | `NOT TESTABLE` | `NOT TESTABLE` |
| **SC 60D Return** | +5.99% | `NOT TESTABLE` | `NOT TESTABLE` | `NOT TESTABLE` |
| **SOS 60D Return** | +4.84% | `NOT TESTABLE` | `NOT TESTABLE` | `NOT TESTABLE` |
| **LPS 60D Return** | +2.87% | `NOT TESTABLE` | `NOT TESTABLE` | `NOT TESTABLE` |
| **Score correlation (Spearman)**| -0.0108 | `NOT TESTABLE` | `NOT TESTABLE` | `NOT TESTABLE` |
| **Top 5% Excluded Return** | +0.12% | `NOT TESTABLE` | `NOT TESTABLE` | `NOT TESTABLE` |
| **Bull Regime Expectancy** | +6.49% | `NOT TESTABLE` | `NOT TESTABLE` | `NOT TESTABLE` |
| **Neutral Regime Expectancy** | -1.00% | `NOT TESTABLE` | `NOT TESTABLE` | `NOT TESTABLE` |
| **Bear Regime Expectancy** | +4.54% | `NOT TESTABLE` | `NOT TESTABLE` | `NOT TESTABLE` |

---

## 5. Final Research Verdict

### **INCONCLUSIVE / INSUFFICIENT DATA**

#### 1. Is there positive OOS expectancy?
**UNKNOWN.** No out-of-sample data is available.

#### 2. Does Spring survive?
**UNKNOWN.**

#### 3. Does SC survive?
**UNKNOWN.**

#### 4. Does SOS survive?
**UNKNOWN.**

#### 5. Does the breadth hypothesis survive?
**UNKNOWN.**

#### 6. Does LPS breakout improve execution?
**UNKNOWN.**

#### 7. Does the composite score discriminate?
**UNKNOWN.**

#### 8. Does the edge survive removal of extreme winners?
**UNKNOWN.**

#### 9. Does it survive transaction costs?
**UNKNOWN.**

#### 10. Is survivorship bias resolved?
**FAIL.** Stored universe lacks delisted company records.

#### 11. Is the sample size sufficient?
**FAIL.** Out-of-sample observations $n = 0$.

#### 12. Is the strategy ready for live paper trading?
**FAIL.** The positive expectation remains an unvalidated discovery hypothesis due to survivorship bias and missing validation price data.

---

## 6. Recommendations for Next Phase
1. **Acquire Post-August 2026 Data:** Fetch price series for the 1,971 constituent stocks covering August 25, 2026 to the present using Yahoo Finance to act as a true out-of-sample validation panel.
2. **Integrate Index Revisions:** Ingest index constituent histories to build a true point-in-time universe, resolving the survivorship bias.
