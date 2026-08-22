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
