# Phase 9C: Broad NSE EQ Research Screening & Candidate Intelligence

## 1. Overview & Purpose
Phase 9C implements the **Research Screening & Candidate Intelligence Engine** for the Wyckoff Stock Screener. It operates directly upon canonical, validated Phase 9B research datasets (`data/research_datasets/<YYYYMMDD>/`) and evaluates 100% of research-eligible securities across all frozen analytical layers:
1. **Broad Mechanical 3-Gate Filter**: Mandatory liquidity, weekly/daily trend confirmation, and setup quality/contraction.
2. **Volume Spread Analysis (VSA) Bar Physics**: Volume ratio, spread ratio, close position, stopping volume (absorption), and supply/demand dry-up.
3. **Wyckoff Schematic Event Detection**: Candidate Selling Climax (`SC`), Automatic Rally (`AR`), Secondary Test (`ST`), Spring, Last Point of Support (`LPS`), Sign of Strength (`SOS`), and Upthrust After Distribution (`UTAD`).
4. **Point & Figure (P&F) Calculation**: Bruce Fraser 3-box reversal horizontal count row, price objective targets, and upside potential.
5. **Setup Scoring & Structural Disqualification**: 0–100 composite ranking scores with component breakdown and structural red flags.
6. **Evidence-First Explanations**: Structured numeric narratives citing exact calculations.
7. **Optional Visual Review Layer**: Multi-timeframe TradingView chart URLs (`Daily`, `Weekly`, `75m`).

---

## 2. Lineage & Relationship to Phase 9A and 9B

```
Phase 9A: Broad Universe Ingestion (NSE EQ Series)
   └── data/universe_snapshots/<YYYYMMDD>/eligible.csv (31 securities)
          │
          ▼
Phase 9B: Canonical Research Dataset Construction
   └── data/research_datasets/<YYYYMMDD>/
          ├── manifest.json
          ├── symbols.csv
          ├── failures.csv
          └── data/<TICKER>.csv (26,137 historical bars)
                 │ (Zero external network requests)
                 ▼
Phase 9C: Research Screening & Candidate Intelligence Engine
   └── data/research_results/<YYYYMMDD>/
          ├── research_manifest.json (Run audit & reconciliation)
          ├── all_results.csv        (100% of input securities)
          ├── candidates.csv         (High Priority & Qualified candidates)
          ├── disqualified.csv       (Securities with structural red flags)
          └── failures.csv           (Isolated evaluation errors)
                 │
                 ▼
Optional Human Visual Review (TradingView Daily/Weekly/75m charts)
```

---

## 3. Strict Frozen Analytical Components
Phase 9C is an **orchestration layer** and does not alter the underlying analytical formulas or thresholds:
- **Mechanical Qualification Rule**:
  $$\text{is\_mechanically\_qualified} = \text{pass\_liq} \land (\text{pass\_weekly} \lor \text{pass\_dma}) \land (\text{pass\_rsi} \lor \text{pass\_atr} \lor \text{pass\_bbw})$$
- **Setup Scoring Weights**:
  - Mechanical Filters: 30% (7.5 pts per sub-filter)
  - Recent Schematic Event: 40% (LPS: 40, SOS: 35, Spring: 30, ST: 15, AR: 10, SC: 5)
  - Peer Relative Strength: 20% (0.0 pts awarded when peer analysis skipped in broad mode)
  - Point & Figure Upside: 10% (scaled up to +30% upside)
- **VSA Thresholds**:
  - Climactic Volume $\ge 2.0$, High $\ge 1.5$, Low $< 0.75$, Very Low $< 0.4$
  - Wide Spread $\ge 1.5$, Narrow $< 0.6$
  - Near High Close $> 0.7$, Near Low Close $< 0.3$

---

## 4. Candidate Categorization & Precedence

Every screened security receives exactly one mutually exclusive category based on strict precedence:

```
                  ┌───────────────────────────────┐
                  │ Evaluate Security in Phase 9B │
                  └──────────────┬────────────────┘
                                 │
                     [is_disqualified == True?]
                                 │
                    ┌────────────┴────────────┐
                 YES│                       NO│
                    ▼                         ▼
         ┌────────────────────┐   [is_mechanically_qualified == True
         │    DISQUALIFIED    │    AND composite_score >= 60.0
         └────────────────────┘    AND (LPS OR SOS OR Spring)?]
                                              │
                                 ┌────────────┴────────────┐
                              YES│                       NO│
                                 ▼                         ▼
                     ┌───────────────────────┐ [is_mechanically_qualified == True
                     │ HIGH_PRIORITY_CANDIDATE│  AND composite_score >= 40.0?]
                     └───────────────────────┘             │
                                              ┌────────────┴────────────┐
                                           YES│                       NO│
                                              ▼                         ▼
                                  ┌────────────────────┐ [is_mechanically_qualified
                                  │ QUALIFIED_CANDIDATE│  OR candidate_event_detected
                                  └────────────────────┘  OR composite_score >= 30.0?]
                                                                   │
                                                      ┌────────────┴────────────┐
                                                   YES│                       NO│
                                                      ▼                         ▼
                                               ┌───────────┐             ┌──────────┐
                                               │ WATCHLIST │             │ NO_SETUP │
                                               └───────────┘             └──────────┘
```

---

## 5. Output Schemas & Manifest Reconciliation

### Output Files (`data/research_results/<YYYYMMDD>/`):
1. **`research_manifest.json`**: Machine-readable audit file containing run parameters, input snapshot path, software version, category counts, and mathematical reconciliation.
2. **`all_results.csv`**: Contains one complete record for every successfully evaluated input security.
3. **`candidates.csv`**: Filtered subset containing `HIGH_PRIORITY_CANDIDATE` and `QUALIFIED_CANDIDATE` records.
4. **`disqualified.csv`**: Subset of securities flagged with structural red flags (e.g. UTAD warning).
5. **`failures.csv`**: Isolated records for securities that could not be evaluated due to corruption or missing files.

### Mandatory Reconciliation Invariant:
$$\text{total\_input\_securities} = \text{successful\_evaluations} + \text{failed\_evaluations}$$
$$\text{successful\_evaluations} = \text{high\_priority} + \text{qualified} + \text{watchlist} + \text{no\_setup} + \text{disqualified}$$

---

## 6. TradingView Visual Review Layer Isolation
- TradingView links (`Daily`, `Weekly`, `75m`) are generated solely for human chart inspection.
- TradingView is **never** an analytical data source, never influences scores, never affects research eligibility, and never determines candidate categorization.
- If TradingView link generation encounters an exception, the error is logged to `screening_errors`, but screening of the security and the overall batch proceeds with 100% success.

---

## 7. CLI Usage

```bash
# Standalone execution on a specific Phase 9B dataset:
python -m wyckoff_screener.research --dataset-dir data/research_datasets/20260823_31_AUDIT

# Integrated execution via scanner:
python -m wyckoff_screener.scan --dataset-dir data/research_datasets/20260823_31_AUDIT --research-screening

# Optional configuration parameters:
#   --min-turnover-cr 1.0         (Liquidity threshold in INR Crores)
#   --high-priority-threshold 60.0 (Score threshold for High Priority)
#   --qualified-threshold 40.0     (Score threshold for Qualified)
#   --watchlist-threshold 30.0     (Score threshold for Watchlist)
```

---

## 8. Limitations & Non-Goals
- **No Automated Trading**: This system is research and visual-triage tooling only. It generates zero buy/sell signals or orders.
- **Survivorship Bias Boundary**: Screening current active constituents over historical lookback windows carries survivorship bias; point-in-time constituent snapshots must be supplied for unbiased backtesting.
- **Candidate Events vs. Confirmed Phases**: All event flags are candidate detections citing numeric evidence; none constitute automatic confirmation of Wyckoff accumulation.
