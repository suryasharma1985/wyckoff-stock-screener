# Wyckoff Stock Screener (NSE)

A Python research and screening tool for Indian equities (NSE) based on the **Wyckoff Method** and **Volume Spread Analysis (VSA)**.

## Core Features
- **Quantified VSA Bar Classification**: Evaluates volume ratios, spread ratios, and close positions with explicit numeric metrics.
- **Wyckoff Schematic Event Detection**: Identifies candidate events (SC, AR, ST, Spring, LPS, SOS, UTAD) with strict empirical evidence.
- **Point & Figure Price Objectives**: Bruce Fraser horizontal count method applied to algorithmic box charts.
- **Comparative Peer Strength**: Normalizes multi-stock performance against structural lows.
- **Evidence-First Architecture**: Every flagged event provides underlying quantitative metrics—no unbacked labels.

## Getting Started
1. Set up a virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Or on Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   ```
2. Run tests:
   ```bash
   pytest
   ```
3. Run Streamlit dashboard:
   ```bash
   streamlit run dashboard/app.py
   ```

## Status

**Phase 11 complete — 145/145 tests passing.**

- **Live / Paper Prospective Forward Validation Engine**: Automated prospective forward screening (`python -m wyckoff_screener.forward screen --date YYYY-MM-DD`), persistent snapshot ledger (`data/forward_validation/snapshots/`), and forward price-path outcome tracking (`python -m wyckoff_screener.forward update`) across 10d, 20d, and 60d trading-bar horizons with MFE/MAE excursions.
- **Strict Zero-Lookahead & Immutability**: All screening at date $T$ uses strictly historical data $Date \le T$. Daily candidate snapshots are permanently frozen with deterministic SHA-256 candidate IDs. Future market data updates outcome fields only and never modifies historical screening snapshots.
- **Streamlit Forward Paper Validation Dashboard**: Integrated **"🔮 Forward Paper Validation"** view in `dashboard/app.py` for monitoring active open candidates, realized cohort win rates/returns, and historical baseline comparisons.
- **Historical Validation & Backtesting Engine (Phase 10)**: Point-in-time walk-forward validation engine (`python -m wyckoff_screener.validation --dataset-dir <path>`) tests candidate signals against historical forward returns with zero future-bar leakage.
- **Evidence-First Candidate Triage**: Evaluates candidate categories across historical checkpoints with cohort and benchmark baselines, explicit temporal in-sample vs out-of-sample partitioning, and survivorship-bias transparency.
- **Research & Screening Tool Only**: The system flags candidate events and does not generate automated buy signals, guaranteed predictions, or live orders. See `AGENTS.md`, `docs/FORWARD_VALIDATION.md`, and `docs/HISTORICAL_VALIDATION.md` for full specifications and findings.
