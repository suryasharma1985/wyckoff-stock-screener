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

**Phase 8 complete — 88/88 tests passing.**

- **Batch Screening & TradingView Integration**: Batch screener (`python -m wyckoff_screener.scan --universe <csv>`) ingests NSE symbol universes, evaluates mechanical filters, and exports structured CSVs containing multi-timeframe TradingView chart URLs (Daily, Weekly, 75-min) paired with a 9-point manual review checklist.
- **Strict Separation of Concerns**: TradingView serves solely as a visual review and chart-navigation layer for human confirmation. All numeric metrics (volume ratios, spread ratios, RSI, ATR/VCP contraction, P&F targets) are derived strictly from validated point-in-time OHLCV data.
- **Research & Screening Tool Only**: The system flags candidate events (`candidate_event_detected`, `possible_LPS`) and does not generate automated buy signals, guaranteed predictions, or confirmed accumulation labels without manual review records. Phase 7 backtest findings confirmed that while the disqualification gate (`is_disqualified`) has consistent directional value, the composite score magnitude is exploratory and not a proven ranking system. See `AGENTS.md` for full specifications and findings.


