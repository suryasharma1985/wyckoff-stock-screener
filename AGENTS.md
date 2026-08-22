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
