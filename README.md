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

**Phase 9C complete — 120/120 tests passing.**

- **Broad NSE EQ Research Screening & Candidate Intelligence**: Research screening engine (`python -m wyckoff_screener.research --dataset-dir <path>`) evaluates 100% of research-eligible securities from validated Phase 9B datasets, generating structured output CSVs (`all_results.csv`, `candidates.csv`, `disqualified.csv`, `failures.csv`) and an auditable `research_manifest.json`.
- **Evidence-First Candidate Triage**: Categorizes every security into mutually exclusive workflow tiers (`HIGH_PRIORITY_CANDIDATE`, `QUALIFIED_CANDIDATE`, `WATCHLIST`, `NO_SETUP`, `DISQUALIFIED`) with machine-readable numeric explanations.
- **Strict Separation of Concerns**: TradingView serves solely as an optional visual review and chart-navigation layer for human confirmation. All numeric calculations are computed locally from validated canonical OHLCV datasets with zero external network requests during screening.
- **Research & Screening Tool Only**: The system flags candidate events and does not generate automated buy signals, guaranteed predictions, or confirmed accumulation labels without manual review records. See `AGENTS.md` and `docs/RESEARCH_ENGINE.md` for full specifications and findings.


