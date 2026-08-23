# Broad NSE EQ Research Universe (Option C) Documentation

## 1. Overview & Definition of Option C
The **Broad NSE EQ Research Universe** (Option C) is the standardized, auditable research universe for the Wyckoff & Volume Spread Analysis screener. It encompasses **all currently available National Stock Exchange of India (NSE) equity securities belonging to the `EQ` series** that satisfy explicit, quantified research-eligibility filters.

Option C replaces hardcoded or arbitrary watchlists with a reproducible, source-traceable constituent pool while preserving complete backward compatibility with the deterministic 15-stock sample fixture (`data/sample_nse_symbols.csv`).

---

## 2. Source of NSE EQ Securities
- **Official Source**: National Stock Exchange of India Official Archives:
  - URL: `https://archives.nseindia.com/content/equities/EQUITY_L.csv`
  - Ingested via: `wyckoff_screener.universe.sources.NseOfficialEquitySource`
- **Fallback / Local Sources**:
  - Sample fixture: `data/sample_nse_symbols.csv` (via `LocalCsvUniverseSource`)
  - Custom CSV universes (via `LocalCsvUniverseSource(csv_path="...")`)
- **No Data Fabrication Principle**: If the live NSE archive endpoint is unreachable, rate-limited, or blocked, the engine records a structured `SOURCE_FETCH_FAILED` error in the audit report rather than manufacturing fake tickers or silently substituting samples.

---

## 3. Strict Architectural Separation

The framework enforces three decoupled operational layers:

```
[ Layer 1: Universe Ingestion & Validation ]
       ↓  (is_valid_symbol, is_eligible_series == 'EQ', is_duplicate == False)
[ Layer 2: Data Availability, History & Quality ]
       ↓  (data_available, bars >= 60, zero_volume < 10%, price/OHLC valid)
[ Layer 3: Research Liquidity Filter ]
       ↓  (20-day rolling avg daily turnover >= ₹1.0 Crore)
============================================================
       → BROAD NSE EQ RESEARCH UNIVERSE (is_research_eligible == True)
============================================================
       ↓
[ Layer 4: Setup Qualification & Screener Ranking ]
       ↓  (Phase 8 Three-Gate: Liquidity + Trend + Contraction/Momentum)
       ↓  (Wyckoff Candidates: SC / AR / ST / Spring / LPS / SOS / UTAD)
       → Mechanically Qualified Setups & TradingView Review Layer
```

> [!IMPORTANT]
> **Research Eligibility vs. Setup Qualification:**
> A security failing Wyckoff setup conditions is **NOT** excluded from the research universe.
> For example:
> `is_research_eligible = True` while `is_mechanically_qualified = False`
> is a standard, valid state for heavily trending, ill-timed, or non-accumulating securities.

---

## 4. Exact Eligibility Rules & Formulas

### A. Universe-Level Eligibility Gate
1. **Symbol Validation**: Must match regex `^[A-Z0-9&_\-]+$`.
2. **Series Eligibility**: Must belong to `EQ` series by default. Non-`EQ` series (e.g. `BE` Trade-for-Trade, `SM` SME, `GB` Govt Bonds, Debt) are rejected.
3. **Deduplication**: Duplicate ticker symbols are flagged and excluded.
4. **Non-Empty Fields**: Missing symbol or series rows are rejected.

### B. Research-Level Eligibility Gate
$$\text{is\_research\_eligible} = \text{is\_valid\_symbol} \land \text{is\_eligible\_series} \land \neg\text{is\_duplicate} \land \text{has\_data\_available} \land \text{has\_sufficient\_history} \land \text{has\_acceptable\_data\_quality} \land \text{passes\_liquidity}$$

Where:
- `has_sufficient_history`: $\text{Bar Count} \ge 60$ daily bars.
- `has_acceptable_data_quality`:
  - Zero-volume rate: $\frac{\text{Count}(\text{Volume} = 0)}{\text{Total Bars}} \times 100.0 < 10.0\%$.
  - Price validity: $\text{Close} > 0 \land \text{High} > 0 \land \text{Low} > 0 \land \text{Open} > 0$.
  - OHLC logic: $\text{High} \ge \text{Low} \land \text{High} \ge \text{Open} \land \text{High} \ge \text{Close}$.
  - Chronological ordering: Dates strictly ascending without duplicate timestamps.
- `passes_liquidity`: 20-day rolling average daily turnover:
  $$\text{Turnover}_{\text{20d}} = \text{mean}\left(\frac{\text{Close} \times \text{Volume}}{10,000,000}\right) \ge ₹1.0\text{ Crore}$$

---

## 5. Machine-Readable Exclusion Reason Taxonomy

Every excluded security is classified with a primary machine-readable reason:

| Exclusion Reason | Trigger Condition |
|---|---|
| `INVALID_SYMBOL` | Symbol contains illegal punctuation or violates syntax regex. |
| `NON_EQ_SERIES` | Security belongs to `BE`, `SM`, `GB`, `IL`, or debt series without explicit opt-in. |
| `DUPLICATE_SYMBOL` | Repeated symbol encountered in constituent source. |
| `MISSING_REQUIRED_FIELDS` | Row missing symbol or series data. |
| `DATA_DOWNLOAD_FAILED` | Network or exchange failure during OHLCV retrieval. |
| `EMPTY_DATA` | Returned OHLCV dataset contains 0 bars. |
| `MISSING_REQUIRED_COLUMNS` | OHLCV missing Date, Open, High, Low, Close, or Volume. |
| `INSUFFICIENT_HISTORY` | Total available bars $< 60$. |
| `DATA_QUALITY_FAILURE` | Zero-volume rate $\ge 10.0\%$, non-positive prices, or invalid OHLC bars. |
| `LIQUIDITY_FAILURE` | 20-day average daily turnover $< ₹1.0\text{ Crore}$. |

---

## 6. Snapshot Mechanism & Output Structure

Every universe build generates a dated snapshot under `data/universe_snapshots/<YYYYMMDD>/`:

```
data/universe_snapshots/YYYYMMDD/
├── source.csv            # Exact raw constituent table as fetched from source
├── eligible.csv          # All securities satisfying is_research_eligible == True
├── excluded.csv          # All excluded securities with primary_exclusion_reason and details
└── universe_report.json  # Comprehensive machine-readable audit report
```

### Snapshot Schema (`eligible.csv` & `excluded.csv`):
- `symbol`: NSE ticker symbol
- `company_name`: Official registered company name
- `series`: Series code (e.g. `EQ`)
- `exchange`: Exchange identifier (`NSE`)
- `yfinance_ticker`: Yahoo Finance ticker (e.g. `RELIANCE.NS`)
- `source_date`: Date and timestamp of source ingestion
- `universe_source`: Source identifier
- `is_valid_symbol`: Boolean syntax validity
- `is_eligible_series`: Boolean series match
- `is_duplicate`: Boolean deduplication flag
- `has_data_available`: Boolean OHLCV presence
- `has_sufficient_history`: Boolean bar count check
- `has_acceptable_data_quality`: Boolean data quality check
- `passes_liquidity`: Boolean turnover check
- `is_research_eligible`: Compound research eligibility
- `primary_exclusion_reason`: Machine-readable reason code (if excluded)
- `exclusion_details`: Descriptive message of specific failures
- `data_bars_count`: Number of historical daily bars evaluated
- `avg_20_daily_turnover_cr`: 20-day average daily turnover in Crores
- `zero_volume_pct`: Percentage of zero-volume trading sessions

---

## 7. Survivorship Bias & Historical Limitations

> [!WARNING]
> **Important Research Limitation:**
> The Broad NSE EQ Research Universe represents a **current point-in-time survivor snapshot**.
> - It is mathematically sound and valid for **forward monitoring, live batch screening, and current-market triage**.
> - Applying a current constituent snapshot retrospectively across historical periods introduces **survivorship bias** (delisted, acquired, or failed companies from previous years are absent).
> - **Historical point-in-time constituent reconstruction is NOT implemented.** For bias-free historical backtesting, historical index snapshot constituents must be supplied by the caller.

---

## 8. CLI & Programmatic Usage

### Build Universe Snapshot
```bash
# 1. Build research universe snapshot from live official NSE equity list
python -m wyckoff_screener.scan --build-universe --universe-source nse_eq

# 2. Build research universe snapshot from sample fixture
python -m wyckoff_screener.scan --build-universe --universe-source sample
```

### Screen Against Existing Snapshot
```bash
# Screen directly against an existing dated eligible universe snapshot
python -m wyckoff_screener.scan --universe data/universe_snapshots/20260823/eligible.csv
```

### Screen Against Sample Universe (Preserved Baseline)
```bash
# Fast 15-stock development and CI run
python -m wyckoff_screener.scan --universe data/sample_nse_symbols.csv
```

### Python API
```python
from wyckoff_screener.universe import build_research_universe, get_universe_source

# Build snapshot from official NSE source
src = get_universe_source("nse_eq")
result = build_research_universe(
    source=src,
    output_base_dir="data/universe_snapshots",
    evaluate_data_layer=True,
    min_avg_turnover_cr=1.0,
)

print(f"Eligible securities: {len(result.eligible_records)}")
print(f"Excluded securities: {len(result.excluded_records)}")
```
