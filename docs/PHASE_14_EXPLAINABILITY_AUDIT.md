# Phase 14 Explainability Integrity & Claim Classification Audit

> **EXPLAINABILITY AUDIT VERDICT**: **`PASS — 100% EVIDENCE-FIRST ALIGNMENT`**
> Every factual statement, visual checklist badge, narrative summary, and risk disclosure in the explainable UI has been audited against the frozen analytical engine. All theoretical inferences are explicitly labeled, and all non-evaluated dimensions (e.g. fundamental financial ratios, intraday order flow, macroeconomic trends) are transparently disclosed.

---

## 1. Claim Classification Framework

All statements and visual indicators across `dashboard/app.py`, `dashboard/explainers.py`, and `dashboard/glossary.py` are audited and classified into four categories:

- **Category A (Direct Engine Output)**: Exact numeric values, dates, boolean flags, and calculations computed by the engine.
- **Category B (Plain-English Translation)**: Clear translations of mechanical thresholds (e.g. `is_mechanically_qualified == True` translated to *"Passed technical trend, momentum, and turnover gates"*).
- **Category C (Theoretical Interpretation / Inference)**: Classic Wyckoff structural hypotheses (e.g. Spring testing remaining supply) explicitly framed with non-certainty language (*"consistent with"*, *"candidate setup"*, *"theoretical Wyckoff interpretation"*).
- **Category D (Not Supported / Not Evaluated)**: External market factors explicitly disclosed as un-evaluated by the engine (*"Not evaluated by current engine: fundamental earnings, news sentiment, intraday order flow"*).

---

## 2. Systematic Claim Classification Audit

| UI Component | Statement / Claim in UI | Classification | Underlying Engine Basis / Governance |
| :--- | :--- | :---: | :--- |
| **Composite Score** | *"Composite Score: 78.5 / 100"* | **A** | Direct calculation from `score_setup()` allocating 30 mech + 40 recency + 20 peer + 10 P&F. |
| **Score Caveat** | *"Score is a research triage ranking, NOT a win probability."* | **B** | Mandated by AGENTS.md and Phase 7 Finding 2 (non-monotonic score behavior). |
| **Category Chip** | *"⭐ High Priority Candidate"* | **B** | Direct mapping from `candidate_category == HIGH_PRIORITY_CANDIDATE`. |
| **Wyckoff Event** | *"Candidate LPS identified on 2026-08-20"* | **A** | Direct output from `detect_all_schematic_events()`. |
| **Volume Ratio** | *"Elevated Volume: 2.20x 20-period average"* | **A** | Exact calculation `volume / rolling_20_period_avg_volume`. |
| **Volume Meaning** | *"Interpreted in VSA as elevated trading effort"* | **C** | Standard VSA theoretical inference; explicitly labeled as interpretation. |
| **Volume Dry-Up** | *"Volume Dry-Up: 0.60x 20-period average"* | **A & C** | Direct metric `< 0.75x` combined with VSA theoretical dry-up concept. |
| **Spread Ratio** | *"Spread Ratio: 1.60x 20-period ATR (Wide spread)"* | **A & B** | Direct metric `(High - Low) / ATR_20 >= 1.5`. |
| **Close Position** | *"Strong Close: 0.85 (top 15% of daily range)"* | **A & B** | Direct metric `(Close - Low) / (High - Low) >= 0.70`. |
| **Trend Alignment** | *"Weekly Close > 30-week SMA and 50 DMA > 100 DMA"* | **A & B** | Direct technical indicators from `scanning/broad_filter.py`. |
| **RSI Momentum** | *"14-period RSI in 55–70 bullish zone"* | **A & B** | Direct indicator evaluation `55.0 <= rsi <= 70.0`. |
| **VCP / BBW** | *"Both ATR and Bollinger Bandwidth are contracting"* | **A & B** | Direct rolling indicators `atr_ratio < 1.0` and `bbw < rolling_mean_bbw_50`. |
| **P&F Target** | *"P&F Target: ₹900.00 (Analytical Objective: +20.0%)"* | **A & B** | Bruce Fraser horizontal count formula `Count_Row + (Cols * Box * 3)`. |
| **Stale Anchor Warning** | *"P&F anchor is older than 60 bars (stale count)"* | **A & B** | Direct rule `pf_is_stale_anchor == True` (0 pts awarded). |
| **Spring Meaning** | *"In Wyckoff theory, a Spring tests remaining supply..."* | **C** | Classical structural interpretation; explicitly framed as hypothesis. |
| **Invalidation Level** | *"A daily close below ₹X invalidates the accumulation premise"* | **C** | Structural support boundary defined by trading range low. |
| **Disqualification** | *"Disqualified Setup: UTAD or distribution detected"* | **A & B** | Direct engine trigger `is_disqualified == True`. |
| **Un-Evaluated Factors** | *"Not evaluated: fundamental earnings, news, order flow"* | **D** | Transparent negative disclosure preventing fabricated confidence. |

---

## 3. Specific Sensitive Domain Audits

### A. Institutional Activity & "Smart Money"
- **Audit Rule**: High volume must never be claimed as guaranteed institutional accumulation.
- **Verification**: The UI describes high volume as `elevated trading effort (volume_ratio = X.XXx)` and frames institutional accumulation as a classical theoretical hypothesis, never as a guaranteed fact.

### B. Point & Figure Price Objectives
- **Audit Rule**: P&F targets must never be presented as guaranteed price forecasts.
- **Verification**: P&F targets are explicitly labeled as *"Analytical Objectives based on horizontal base width (Bruce Fraser method), NOT guaranteed future prices."*

### C. Invalidation Levels & Risks
- **Audit Rule**: Support levels and invalidation criteria must derive from actual range boundaries.
- **Verification**: Invalidation levels reference the trading range support floor (e.g. Spring low or count row base) identified by the engine.

### D. Probabilities & Expected Returns
- **Audit Rule**: No probability percentages or expected return figures may be fabricated for individual setups.
- **Verification**: The dashboard includes prominent warning banners stating: *"Composite score is a research ranking, NOT a mathematical win probability."*

---

## 4. Explainability Audit Conclusion

**All UI components adhere strictly to AGENTS.md Guiding Principles**:
1. **No Fabricated Confidence**: Every signal cites explicit numeric metrics.
2. **Candidates, Never Certainties**: All schematic labels use candidate terminology.
3. **Evidence-First Presentation**: Summary $\rightarrow$ Why Selected $\rightarrow$ Evidence $\rightarrow$ Risks $\rightarrow$ Technical Details.
