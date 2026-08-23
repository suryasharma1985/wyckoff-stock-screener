# Project Progress Log

## Status: Phase 8 Complete (Batch Screening & TradingView Integration Active)

## Completed
- [x] Phase 1: Scaffolding (AGENTS.md, folder structure, git init) — 2026-08-22
- [x] Phase 2: Data ingestion (data_loader.py, validation, tests) — 2026-08-22
- [x] Phase 3: Indicators (moving_averages, momentum/RSI, volatility/ATR, vsa_metrics) + ATR consistency fix — 2026-08-22
- [x] Phase 4: Wyckoff schematic event detectors (SC/AR/ST/Spring/LPS/SOS/UTAD) + UTAD threshold fix — 2026-08-22
- [x] Phase 5: Point & Figure counting + Bogomazov peer-strength comparison — 2026-08-22
- [x] Phase 6: Scoring/ranking engine + Streamlit dashboard — 2026-08-22
- [x] Phase 7: Historical backtest validation & forward-return evaluation — 2026-08-22
- [x] Phase 8: CSV-defined batch screening & TradingView manual-review integration — 2026-08-23

## Test Suite Status
- 89/89 passing as of Phase 8 release audit (including universe ingestion, batch downloader cache, TradingView URLs, broad filters, 3-gate qualification rules, and review record schema)

## Bugs Found and Fixed
- **2026-08-22**: Fixed combinatorial explosion in `detect_secondary_test_candidates()` and `detect_lps_candidates()`. Previously, both functions scanned from each anchor to the end of the dataset without a search ceiling and recorded every matching bar (yielding 211 STs and 13,534 LPSs on ANANTRAJ). Fixed by introducing bounded lookahead windows (`ST_MAX_BARS_AFTER_SC = 15`, `LPS_MAX_BARS_AFTER_ANCHOR = 20`) and recording only the first qualifying bar per anchor. Reduced ANANTRAJ counts to 4 STs and 6 LPSs.
- **2026-08-22**: Fixed silent fallback in `count_price_objective()`: added `used_fallback_count: bool` to `PFPriceObjective` and prepended a visible warning notice to `supporting_note` whenever no column exactly touches the count row.
- **2026-08-22**: Fixed unused swing low check in `compare_low_to_low_slope()`: added `is_first_swing_low`, `is_second_swing_low`, and `swing_validated` fields to `PeerSlopeResult`, raising `ValueError` when `validate_swing=True` and dates are not swing lows.
- **2026-08-22**: Fixed default `validate_swing=False` in `rank_peer_relative_strength()`: updated default to `validate_swing=True` and stopped silently dropping failed peer exceptions, returning `(ranked_results, failed_peers)` tuple with exact error messages per skipped peer.
- **2026-08-22**: Fixed fabricated half-credit bug when `peer_rank is None` in `score_setup()`: missing peer comparison previously awarded 10.0 points (half credit). Fixed to strictly score 0.0 points, added `peer_analysis_skipped: bool = True` to `ScoredSetup`, and exposed it in the output breakdown.
- **2026-08-22**: Fixed stale P&F anchor auto-selection bug in `score_setup()`: when auto-selecting the count row from an old LPS/Spring event with no recency constraint, the engine computed stale objectives (e.g. 329.85 for APOLLO when price was 384.55). Fixed by adding `PF_ANCHOR_MAX_STALENESS_BARS = 60` and setting `stale_anchor = True`, `pf_pts = 0.0`, and prepending an explicit staleness warning to `supporting_note`.



## Known Decisions / Deviations from Literal AGENTS.md Text
- `spread_ratio` ATR denominator: `use_wilder=False` (simple rolling mean) chosen to react faster to immediate local bar spread rather than smoothed lag.
- `UTAD_MIN_VOLUME_RATIO`: set to 1.5 (aligns with AGENTS.md's "High" volume band, 1.5 - 2.0) to represent genuinely elevated volume rather than the Average band.
- `DEFAULT_MIN_DECLINE_PCT`: set to 0.03 (3% drop over 10-bar lookback window) in `detect_prior_decline()` as the quantitative threshold for "clear prior decline".
- `get_prior_trading_range()` uses a simple min(Low)/max(High) over the trailing N bars as support/resistance, not a validated consolidation/range-bound check — in a strong trend this can return a 'range' that isn't really ranging. Flagged as an approximation per AGENTS.md's fallback-labeling rule. Revisit if false-positive rate on real data looks high.
- `P&F Box Size Scaling`: Default percentage-of-price method (`calculate_dynamic_box_size()`, ~1% rounded to clean tick/currency steps) implemented instead of hardcoding static traditional lookup tables, allowing dynamic scaling across all NSE stock denominations.
- `P&F Count Row Selection`: `count_price_objective()` identifies and counts all vertical columns within the range whose box span covers the count row level (with a fallback to range span if exact touches are empty), showing the counted column indices explicitly in the output note.
- `Scoring Engine Weights`: Explicit 100-point allocation across 4 components: 30 pts Mechanical Filters (4 x 7.5), 40 pts Schematic Event Recency, 20 pts Peer Relative Strength, and 10 pts P&F Upside.
- `Disqualification Override`: Red flags (most recent event = UTAD, absence of base accumulation structure, or failure of all mechanical filters) explicitly set `is_disqualified = True` and force setups to the bottom of the watchlist ranking regardless of numerical score.
- `Peer Score Decay Formula`: Linear formula `1.0 - ((peer_rank - 1) / total_peers)` ensures all evaluated peers receive scaled relative credit, with the lowest-ranked peer retaining a small nonzero positive contribution rather than dropping to zero (deliberate choice).
- `P&F Count-Row Auto-Selection Priority`: When `count_row_price` is not provided by caller, auto-selects by priority: most recent `LPS` candidate price > most recent `Spring` candidate price > `current_close`.
- `P&F Upside-to-Points Tiers`: Upside thresholds (>=20% => 10 pts, >=10% => 6 pts, >0% => 3 pts, <=0% => 0 pts) are codified arbitrary threshold bands for ranking prioritization, not derived literally from AGENTS.md text.
- `Backtest Lookback Window`: `run_rolling_score()` uses a 250-bar rolling window (not expanding) so earlier data is dropped at each checkpoint. This matches how the scoring engine was designed (recent-history scoring), but means the engine never "sees" the full dataset simultaneously.
- `Compound Mechanical Qualification Rule`: `is_mechanically_qualified` is a 3-gate compound rule: `pass_liq AND (weekly_uptrend OR dma_50_above_100) AND (rsi_in_band OR atr_contracting OR vcp_bbw_contracting)`. Individual filter results are exposed separately in `filter_results`.
- `Three-Layer Concept Separation`:
  1. Universe Eligibility: Series `EQ` filter and ticker syntax validation (`universe/nse_symbols.py`).
  2. Setup / Mechanical Qualification: Technical trend, momentum, volatility contraction, and turnover gates (`scanning/broad_filter.py`).
  3. Research / Backtest Eligibility: Data bar sufficiency (`min_bars >= 60`), session continuity, zero-volume rate, and point-in-time constituent snapshot verification.
- `Universe Provenance & Survivorship Bias Notice`: Current constituent lists (such as `data/sample_nse_symbols.csv` containing 15 accepted EQ stocks) are CSV-defined sample universes suitable for forward screening/monitoring, but do NOT represent survivorship-bias-free historical index constituents. Point-in-time constituent snapshots must be supplied for historical research.



## Phase 7 Backtest Findings — 2026-08-22

**Setup**: 3 NSE stocks (ANANTRAJ.NS, APOLLO.NS, HINDCOPPER.NS), Jan 2024–Aug 2026, 246 total checkpoints (82 per stock, step=5 bars, lookback=250 bars). Forward returns computed at 10, 20, 60 daily bars post-checkpoint. **No-lookahead verified**: scoring at checkpoint i is identical whether using a truncated or full dataset.

**Finding 1 — Disqualification filter: directionally consistent (3/3 stocks)**

At the 60-bar horizon, qualified setups outperformed disqualified ones on all three stocks individually:
- ANANTRAJ: Qualified +3.57% vs Disqualified -7.63% (25% win rate disqualified)
- APOLLO: Qualified +30.01% vs Disqualified +11.49% (5 disq. obs. only — tiny bucket)
- HINDCOPPER: Qualified +20.70% vs Disqualified +10.03%

The UTAD + absence-of-base disqualification flag appears to identify genuinely weaker 60d outcomes. This is the only finding consistent across all three stocks.

**Finding 2 — Composite score magnitude: inconsistent (2/3 stocks invert)**

At the 60-bar horizon, high-score (>=60) setups did NOT outperform low-score (<40) setups on 2 of 3 stocks:
- ANANTRAJ: High Score -11.64% vs Low Score +3.24% (INVERTED — n=6, very small)
- APOLLO: High Score +9.57% vs Low Score +38.32% (INVERTED — n=11)
- HINDCOPPER: High Score +36.09% vs Low Score +23.78% (correct direction)

Root cause: high-score checkpoints on ANANTRAJ clustered at the late-bull peak preceding a UTAD reversal; on APOLLO the biggest recovery moves happened when scores were still low. The pooled +17.44% high-score figure masks this 2/3 failure rate. **Score magnitude above the disqualification threshold should not be used to size or prioritize positions.**

**Finding 3 — Short-horizon signals (10d, 20d): near-random**

No consistent direction at 10-bar or 20-bar horizons across cohorts or stocks. Wyckoff setups operate on multi-week/multi-month timeframes; 10-20 bar forward noise dominates.

**MANDATORY LIMITATIONS — Not statistically significant:**
- n=3 stocks over 2.5 years in a bull market is exploratory, not validated alpha.
- All 3 equities benefited from India's 2024–2026 equity bull run. Results in a bear or sideways market are unknown.
- Checkpoints every 5 bars are heavily autocorrelated. Effective independent observations are far fewer than 246.
- High-score cohort sizes of n=6 to n=19 are too small to separate signal from variance.
- These findings are directional indicators for further research, not a basis for capital allocation decisions.






