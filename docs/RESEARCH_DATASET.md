# Broad NSE EQ Research Dataset (Phase 9B) Documentation

## 1. Overview & Dataset Purpose
The **Broad NSE EQ Research Dataset** provides the canonical, standardized, validated, and cached OHLCV dataset constructed directly from the Phase 9A Broad NSE EQ Research Universe snapshot (`data/universe_snapshots/<YYYYMMDD>/eligible.csv`).

Phase 9B is **Dataset Construction Only**. It guarantees chronological integrity, explicit error isolation, expanded SHA-256 cache verification, and optional TradingView review links while preserving complete backward compatibility with the existing analytical engine and the 15-stock development fixture (`data/sample_nse_symbols.csv`).

---

## 2. Input Universe & Traceability Lineage
Every research dataset is generated strictly from an auditable Phase 9A research universe snapshot:
$$\text{NSE Official Source} \longrightarrow \text{Phase 9A Snapshot (eligible.csv)} \longrightarrow \text{Phase 9B Canonical OHLCV Dataset}$$

Lineage fields preserved in `symbols.csv`:
- `source_universe_snapshot`: Exact file path to input Phase 9A snapshot.
- `source_universe_date`: Source acquisition date and timestamp.
- `research_eligibility_status`: `True`.
- `data_acquisition_status`: `CACHE_HIT` / `FRESH_DOWNLOAD` / `VALIDATION_FAILED`.

---

## 3. Historical Data Window & Mathematical Justification

### Lookback Audit Across Codebase:
1. **Indicator Warm-up**:
   - `broad_filter.py`: 40-week WMA requires $\ge 40$ weekly bars ($\approx 200$ daily bars); 100-day DMA requires $\ge 100$ daily bars.
   - `volatility.py`: 50-day ATR ratio requires $\ge 50$ daily bars.
   - `schematic_events.py` / `swing_points.py`: Trading range base lookbacks require $\ge 60$ daily bars.
   - `pf_chart.py`: Point & Figure chart horizontal count rows require $\ge 60$ daily bars.
2. **Research & Backtest Lookback**:
   - `backtest/historical_scorer.py`: `DEFAULT_LOOKBACK_WINDOW = 250` daily bars at each checkpoint.
   - Forward evaluation horizon: $H \in \{10, 20, 60\}$ daily bars post-checkpoint.
3. **Historical Cycle Depth**:
   - Evaluating multi-year accumulation/re-accumulation cycles across market regimes requires at least 2–3 calendar years.

### Recommended Window:
- **Default Start Date**: `2023-01-01`
- **End Date**: `latest`
- **Total Historical Depth**: $\approx 850$ daily bars ($\ge 200\text{d warm-up} + 250\text{d rolling backtest} + 60\text{d outcome horizon} + 340\text{d base depth}$).
- **Minimum Acceptable History**: $\ge 60$ bars (strictly enforced).

---

## 4. Canonical OHLCV Schema

Every materialized CSV in `<dataset_dir>/data/<TICKER>.csv` conforms to:

| Column | Type | Formatting / Constraints |
|---|---|---|
| `Date` | `datetime64[ns]` / `YYYY-MM-DD` | Strictly ascending, unique, no gaps created artificially |
| `Open` | `float64` | Strictly positive ($> 0.0$) |
| `High` | `float64` | Strictly positive ($> 0.0$), $H \ge L \land H \ge O \land H \ge C$ |
| `Low` | `float64` | Strictly positive ($> 0.0$), $L \le O \land L \le C$ |
| `Close` | `float64` | Strictly positive ($> 0.0$) |
| `Volume` | `float64` | Strictly non-negative ($\ge 0.0$), zero-volume rate $< 10.0\%$ |

---

## 5. Corporate Action & Price Adjustment Policy
- **Provider**: Yahoo Finance (`yfinance`).
- **Adjustment Behavior**:
  - `Open`, `High`, `Low`, `Close`: Retroactively adjusted for corporate stock splits and bonus issues.
  - Cash dividends: Not deducted from historical OHLC prices (`auto_adjust=False`), preserving chart support/resistance geometry.
  - `Volume`: Unadjusted raw traded volume.
- **Wyckoff Implications**: Split adjustment is vital for valid P&F arithmetic and volume spread analysis without artificial jump artifacts.

---

## 6. Duplicate Date Handling Policy
1. **Identical Duplicate Rows**: Duplicate date rows with identical $(O, H, L, C, V)$ values are deduplicated deterministically (first row kept, notice logged).
2. **Conflicting Duplicate Rows**: Duplicate date rows with differing values raise `DataValidationError` with `CONFLICTING_DUPLICATE_DATES` and are strictly excluded.

---

## 7. Cache Architecture & SHA-256 Verification
Cached data in `data/cache/<TICKER>.csv` and `<TICKER>.meta.json`:
- `.meta.json` records: `symbol`, `provider`, `frequency`, `requested_start/end`, `actual_start/end`, `retrieved_at_utc`, `schema_version`, `adjustment_policy`, `row_count`, `data_hash` (SHA-256 hex digest), and `zero_volume_pct`.
- **Integrity Validation**: Cache reads re-compute the SHA-256 hash of the CSV file. If the hash mismatches or parsing fails, the cache is automatically invalidated and redownloaded.

---

## 8. Failure Isolation & Rate Limiting
- Concurrency bounded to `max_workers = 4` with exponential backoff retry (`max_retries = 3`).
- Single-stock download or parsing failures are isolated into `failures.csv` without aborting batch materialization.
- Machine-readable reasons: `DOWNLOAD_FAILED`, `TIMEOUT`, `EMPTY_DATA`, `DATA_QUALITY_FAILURE`, `INSUFFICIENT_HISTORY`, `RATE_LIMITED`.

---

## 9. Optional TradingView Visual Review Layer

Reusing the established Phase 8 infrastructure (`src/wyckoff_screener/charting/tradingview_links.py`):
- For every successfully materialized security, deterministic TradingView URLs (`tradingview_daily_url`, `tradingview_weekly_url`, `tradingview_75m_url`) are attached to `symbols.csv`.
- **Strict Boundary Guarantee**:
  - TradingView is **NEVER** a data source, analytical source of truth, or prerequisite for dataset construction.
  - TradingView link generation cannot affect research eligibility, mechanical qualification, or setup scoring.
  - Any error in link generation will not fail OHLCV dataset materialization.

---

## 10. Dataset Manifest & Output Structure

Snapshots are written to `data/research_datasets/<YYYYMMDD>/`:

```
data/research_datasets/YYYYMMDD/
├── manifest.json         # High-level dataset audit, provider, counts, schema version
├── symbols.csv           # Per-symbol metrics, Phase 9A traceability, and TradingView review URLs
├── failures.csv          # Isolated failures with exact error reasons and retries
└── data/                 # Normalized canonical OHLCV CSVs (Date, Open, High, Low, Close, Volume)
    ├── ANANTRAJ.NS.csv
    ├── APOLLO.NS.csv
    └── ...
```

---

## 11. CLI & Programmatic Usage

### Build Dataset Snapshot from Phase 9A Universe
```bash
# Materialize canonical research dataset from Phase 9A snapshot
python -m wyckoff_screener.scan --build-dataset --universe data/universe_snapshots/20260823/eligible.csv
```

### Screen Directly Off Materialized Dataset (Offline / Zero Network)
```bash
# Run batch screening directly off materialized canonical CSVs
python -m wyckoff_screener.scan --dataset-dir data/research_datasets/20260823
```

### Python API
```python
from wyckoff_screener.data import build_research_dataset

result = build_research_dataset(
    universe_snapshot_path="data/universe_snapshots/20260823/eligible.csv",
    output_base_dir="data/research_datasets",
    start_date="2023-01-01",
)

print(f"Materialized {result.manifest.successful_symbols} securities to {result.dataset_dir}")
```
