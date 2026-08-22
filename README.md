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

**Phase 7 complete — all 7 phases implemented, 70/70 tests passing.**

Phase 7 backtest (3 NSE stocks, Jan 2024–Aug 2026, 246 rolling checkpoints) found that the **disqualification gate** (`is_disqualified`) shows consistent directional edge at the 60-bar horizon across all three stocks — the most trustworthy signal in the system. The composite score's *magnitude* as a continuous ranking variable above the qualification threshold did **not** hold up per-stock (inverted on 2 of 3 stocks); treat it as a coarse triage tool, not a precision ranking. See `AGENTS.md § Validated Findings` for the full findings and limitations.

