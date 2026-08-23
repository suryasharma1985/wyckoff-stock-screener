# AGENTS.md

## Project Overview
A Wyckoff Method + Volume Spread Analysis (VSA) research and screening tool for NSE-listed Indian equities. It ingests historical OHLCV data and applies a codified, numeric version of the framework below to classify bars, flag candidate Wyckoff schematic events, screen a watchlist, and calculate Point & Figure price objectives.

**Guiding Principle — No Fabricated Confidence**: Every flagged event must cite the specific numbers behind it (volume ratio, spread ratio, close position, price level). Never assert a phase or signal without showing the numeric evidence. Say *"candidate SC: volume 4.2x the 20-period average, close in the bottom 15% of the bar's range"* — never just *"this is a Selling Climax."*

---

## Tech Stack
- **Runtime**: Python 3.11+, standard `venv`
- **Data Handling**: `pandas`, `numpy`
- **Market Data**: `yfinance` for optional live data (NSE tickers use the `.NS` suffix)
- **Testing**: `pytest` for unit and integration tests
- **Charting**: `matplotlib` / `plotly` — decide at the reporting phase, not needed initially

---

## Repository Structure
```
wyckoff-stock-screener/
├── data/                         # Raw OHLCV CSVs (gitignored actual data, keep sample fixtures)
│   └── sample_nse_ohlcv.csv
├── src/
│   └── wyckoff_screener/         # Core application package
│       ├── __init__.py
│       ├── data_loader.py        # OHLCV ingestion & validation
│       ├── indicators/           # Technical indicators & rolling metrics
│       ├── wyckoff/              # Wyckoff schematic event detection
│       ├── peer_analysis/        # Comparative peer strength analysis
│       ├── pointfigure/          # Point & Figure chart construction & counting
│       └── scoring/              # Screener scoring & ranking
├── tests/                        # Pytest test suite mirroring src structure
│   ├── __init__.py
│   ├── test_data_loader.py
│   ├── indicators/
│   ├── wyckoff/
│   ├── peer_analysis/
│   ├── pointfigure/
│   └── scoring/
├── .gitignore
├── AGENTS.md                     # Permanent agent context & domain specification
├── README.md
└── requirements.txt
```

---

## Coding Conventions
- **Type Annotations**: Type-hint every function and method signature explicitly.
- **Explicit Thresholds**: Every classification/detection function must take named threshold parameters with defaults defined as module-level constants — never use bare magic numbers in logic.
- **Evidence-First Return Values**: Every function that returns a "signal" or "event" must return the supporting metrics alongside the label, never the label alone.
- **Test-Driven Detection**: New detection logic must always ship with a `pytest` test using a small synthetic OHLCV fixture containing a hand-built, known example of the pattern.

---

## Domain Knowledge — VSA Bar Classification (Quantified)
- **Volume Ratio** (`volume_ratio` = bar volume / rolling 20-period average volume):
  - $\ge 2.0$: Very High / Climactic
  - $1.5 - 2.0$: High
  - $0.75 - 1.5$: Average
  - $0.4 - 0.75$: Low
  - $< 0.4$: Very Low
- **Spread Ratio** (`spread_ratio` = bar (high - low) / rolling 20-period average true range):
  - $\ge 1.5$: Wide
  - $0.6 - 1.5$: Average
  - $< 0.6$: Narrow
- **Close Position** (`close_position` = (close - low) / (high - low)):
  - $> 0.7$: Near High (Strong close)
  - $< 0.3$: Near Low (Weak close)
  - $0.3 - 0.7$: Mid-range close
- **No Demand**: Up-close bar, narrow spread (`spread_ratio < 0.6` or $< 1.0$), `volume_ratio < 1.0`
- **No Supply**: Down-close bar, narrow spread (`spread_ratio < 0.6` or $< 1.0$), `volume_ratio < 1.0`
- **Stopping Volume**: `volume_ratio >= 1.5`, `spread_ratio < 1.0` (absorption of supply)
- **Effort vs. Result Flag**: `volume_ratio` disagrees with (`spread_ratio` and `close_position` direction) — flag for review.

---

## Domain Knowledge — Wyckoff Schematic Events (Candidates, Never Certainties)
- **Selling Climax (SC) Candidate**: `spread_ratio >= 1.5`, down-close bar, `volume_ratio >= 2.0`, occurring after a clear prior decline.
- **Automatic Rally (AR) Candidate**: Sharp up bar immediately following an SC candidate, with `volume_ratio >= 1.0`.
- **Secondary Test (ST) Candidate**: Retest of the SC-candidate low area, with `volume_ratio` strictly lower than the SC candidate's own volume ratio.
- **Spring Candidate**: Bar's low undercuts prior support (even intrabar), then closes back above that support level.
- **Last Point of Support (LPS) Candidate**: Higher low than the most recent Spring / ST candidate, `volume_ratio < 0.75`, holding above trading range support.
- **Sign of Strength (SOS) Candidate**: Close breaks above trading range resistance, `volume_ratio >= 1.5`, `close_position > 0.7`.
- **Upthrust After Distribution (UTAD) Candidate**: High breaks above trading range resistance intrabar but closes back below it, often on elevated `volume_ratio`.

---

## Domain Knowledge — Point & Figure Counting (Bruce Fraser Method)
- Construct an actual P&F chart from OHLC data: fixed box size (start with traditional scaling, make it swappable), N-box reversal (default 3).
- Identify the horizontal count row (typically at/near the LPS level).
- Count columns across the row within the trading range.
- **Price Objective Calculation**:
  $$\text{Price Objective} = \text{Count-Row Price} + (\text{Columns} \times \text{Box Size} \times \text{Reversal } N)$$
- Must be real box-construction logic against the OHLC series, not a simplified high-minus-low measured move. If a measured-move approximation is ever used as a fallback, label it explicitly as an approximation in the output.

---

## Domain Knowledge — Comparative Peer-Strength (Bogomazov-Style)
- Given a primary stock's structural low date:
  1. Pull each peer's price series.
  2. Normalize each series to percentage change from that common reference date.
  3. Compare the slope between two corresponding significant lows (the low before, and the next higher low) for the primary stock versus each peer.
- A flatter or negative slope on a peer over the same window indicates **relative weakness**; a steeper / more positive slope indicates **relative strength**.

---

## Initial Watchlist (For Validation)
- **ANANTRAJ** (Anant Raj Limited)
- **APOLLO** (Apollo Micro Systems)
- **HINDCOPPER** (Hindustan Copper Limited)
- *Note*: All are NSE-listed. Confirm exact Yahoo Finance ticker symbols (`.NS` suffix, e.g. `ANANTRAJ.NS`, `APOLLO.NS`, `HINDCOPPER.NS`) before wiring up live fetch; do not hardcode unverified symbols.

---

## What Not To Do
- **Never state a candidate event as a confirmed phase.**
- **Never tune a threshold to make a specific stock look more bullish** — thresholds are shared constants, changed deliberately with documented rationale, not per-stock.
- **Never skip a test on new detection logic.**
- **This is analysis/research tooling only — no live order execution, ever.**

---

## Progress Tracking
- Maintain [`PROGRESS.md`](file:///c:/Users/surya/Downloads/wyckoff-stock-screener/PROGRESS.md) continuously: after completing any task (phase, module, or fix), immediately update the completed checklist with the current date, refresh the test suite pass count, and record any threshold/design decisions in "Known Decisions / Deviations".

---

## Validated Findings (Phase 7 Backtest)

**Sample**: 3 NSE stocks (ANANTRAJ, APOLLO, HINDCOPPER), Jan 2024–Aug 2026, 246 rolling checkpoints (82 per stock, step=5 bars, 250-bar lookback window). **NOT statistically significant — exploratory and directional only.** Three stocks over 2.5 years in a bull market is insufficient to validate alpha. Treat all findings below as hypotheses for further investigation, not established results.

**FINDING 1 — Disqualification filter is the most trustworthy signal in the system.**
The `is_disqualified` gate (triggered by UTAD, absent base accumulation structure, or all mechanical filters failing) shows a consistent directional edge across all 3 stocks individually at the 60-bar forward horizon:
- ANANTRAJ: Qualified +3.57% vs Disqualified -7.63%
- APOLLO:    Qualified +30.01% vs Disqualified +11.49%
- HINDCOPPER: Qualified +20.70% vs Disqualified +10.03%

This is the only signal that held on every stock without exception. The UTAD + absent-base flag appears to identify periods where accumulation has either not yet formed or has already transitioned into distribution, which subsequently underperformed over ~3-month horizons. Use the disqualification gate as the primary decision boundary.

**FINDING 2 — composite_score's magnitude as a continuous ranking variable ABOVE the qualification threshold does NOT hold up per-stock.**
At the 60-bar horizon, high-score (≥60) setups inverted vs low-score (<40) setups on 2 of 3 stocks:
- ANANTRAJ: High Score -11.64% vs Low Score +3.24% (n=6 — INVERTED)
- APOLLO:   High Score +9.57%  vs Low Score +38.32% (n=11 — INVERTED)
- HINDCOPPER: High Score +36.09% vs Low Score +23.78% (n=14 — correct)

The pooled +17.44% for high-score vs +15.75% for low-score looks like a marginal win but conceals a 2/3 per-stock failure rate. **Do not present composite_score as if higher-is-reliably-better beyond the qualify/disqualify gate.** Above the qualification threshold, score differences should be treated as weak supporting evidence, not a ranking you can trust to pick the best of several qualified setups.

**HYPOTHESIS (untested)** — High scores may partly capture "how extended an already-mature move is" rather than "how much upside remains." ANANTRAJ's and APOLLO's high-score windows clustered near late-bull peaks and post-recovery phases respectively, when the mechanical filters and recency components scored well precisely because conditions looked ideal — just before they reversed. This would explain why high scores appear at the wrong moment. This hypothesis requires a larger universe (50+ stocks, multiple market cycles) before it can be confirmed or rejected.

**What to do with this:**
- Use `is_disqualified` as a hard gate — do not engage with disqualified setups.
- Use composite_score as a coarse triage tool within the qualified universe, not a precision ranking.
- Do not re-weight the scoring engine based on this dataset alone — sample size is too small.
- Any future re-weighting must be documented with sample size, methodology, and honest out-of-sample results.

---

## Universe Ingestion & Survivorship Bias Distinction
- **Current Universe Screening vs. Historical Backtesting**: Ingesting a current constituent list (e.g. current Nifty 50 or active NSE equities) is appropriate for forward monitoring, triage, and manual review. However, screening a current list over historical periods introduces **survivorship bias** (failing or delisted companies are excluded).
- For bias-free historical backtests, point-in-time universe snapshots must be supplied. Every universe validation report explicitly records `universe_source`, `retrieval_date`, and constituent methodology.
- **Series Eligibility**: `EQ` is the default eligible series for standard Indian equity trading. Alternative series (such as `BE` Trade-for-Trade / Book Entry) carry distinct settlement constraints and liquidity dynamics; they are not treated as equivalent to `EQ` and must be deliberately opted in by the caller.

---

## TradingView Integration & Visual Review Layer
- **Strict Separation of Quantitative Engine and Visual Chart Navigation**:
  - TradingView URLs (Daily, Weekly, 75-Minute) are generated purely to facilitate human visual inspection on TradingView's platform.
  - A generated TradingView link is **NOT evidence** that a setup, Spring, LPS, SOS, or accumulation structure is valid or confirmed.
  - All numeric calculations (moving averages, RSI, ATR/VCP ratios, volume spreads, P&F targets) are derived strictly from the application's validated, point-in-time OHLCV dataset.
- **Manual Chart-Review Checklist**:
  1. Daily chart with volume (bar-by-bar spread & volume interaction)
  2. Weekly chart with volume (macro trend / base structure)
  3. RSI(14) in 55–70 bullish momentum zone
  4. 20-period volume average comparison (climactic volume >= 2.0x, dry-up < 0.75x)
  5. 50 EMA and 100 EMA / SMA alignment
  6. ATR / VCP volatility contraction across successive swings
  7. Marked support and resistance levels across trading range
  8. Schematic candidate: Spring / ST / LPS / SOS / UTAD context
  9. Close-position and effort-vs-result absorption check
- **Manual Review Records**:
  - Review records must explicitly record `chart_review_status` (`pending`, `reviewed`, `rejected`), `reviewed_timeframes`, `reviewer_notes`, `confirmed_candidate_events`, and `rejected_candidate_events`.
  - Candidate events must **never** be automatically converted to "confirmed" status without a completed manual review record.



