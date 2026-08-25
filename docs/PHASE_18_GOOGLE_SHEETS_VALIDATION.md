# Phase 18 — Google Sheets Stock Screener Validation & Research Ledger System

**Execution Timestamp**: 2026-08-24 19:20:00 IST  
**Artifacts Generated**:
- Multi-Tab Google Sheets Template Workbook: [`data/google_sheets/phase18_google_sheets_template.xlsx`](file:///c:/Users/surya/Downloads/wyckoff-stock-screener/data/google_sheets/phase18_google_sheets_template.xlsx)
- Google Sheets Import Signals CSV: [`data/google_sheets/screener_signals.csv`](file:///c:/Users/surya/Downloads/wyckoff-stock-screener/data/google_sheets/screener_signals.csv)
- Google Apps Script Engine: [`google_sheets/Code.gs`](file:///c:/Users/surya/Downloads/wyckoff-stock-screener/google_sheets/Code.gs)
- Google Sheets User Guide: [`google_sheets/README.md`](file:///c:/Users/surya/Downloads/wyckoff-stock-screener/google_sheets/README.md)
**Status**: **COMPLETE & VALIDATED**

---

## 1. Why We Changed Direction from the Expensive Historical Backtest

The full 3.2-year $\times$ 1,971-stock Python historical backtest required massive multi-hour re-evaluations across thousands of historical point-in-time slices. More importantly, giant one-off backtests obscure individual trade dynamics and cannot easily serve as an ongoing, interactive forward-testing ledger.

Phase 18 introduces a **lightweight, practical, and transparent Google Sheets research ledger**:
- **Python Screener** remains responsible for the heavy Wyckoff event detection, VSA metrics, Point & Figure targets, and composite scoring on current/recent market data.
- **Google Sheets** serves as the interactive research ledger where candidates can be pasted, tracked over time, audited bar-by-bar, and aggregated into visual dashboard statistics without running heavy backtesting loops.

---

## 2. Google Sheets Architecture

The workbook contains **6 dedicated sheets**:

```
phase18_google_sheets_template.xlsx
├── README           # Workflow guide, field definitions, and methodology reminders
├── SIGNALS          # Primary input ledger for screener candidates
├── PRICE_DATA       # Helper sheet for GOOGLEFINANCE OHLC historical queries
├── TEST_RESULTS     # Detailed per-trade outcome tracking (exits, MFE, MAE, R-multiples)
├── DASHBOARD        # Live aggregated KPIs (win rate, profit factor, score deciles, events)
└── SETTINGS         # Configurable parameters (Stop %, Target %, Max Days, Friction %, Ambiguity)
```

---

## 3. Data Sources & GOOGLEFINANCE Capabilities / Limitations

### Native `GOOGLEFINANCE()` Capabilities
- Syntax: `=GOOGLEFINANCE("NSE:SYMBOL", "all", StartDate, EndDate, "DAILY")`
- Returns: 6-column array: `Date`, `Open`, `High`, `Low`, `Close`, `Volume`.
- Strengths: Native, free, zero setup, automatically refreshes inside Google Sheets.

### Critical Limitations of `GOOGLEFINANCE()`
1. **Array Complexity**: Scanning dynamic multi-day Highs/Lows across variable holding periods to detect whether High $\ge$ Target occurred before Low $\le$ Stop is extremely complex in native sheet formulas without auxiliary helper sheets.
2. **Missing Tickers & Delay**: Illiquid or newly listed small-cap NSE tickers occasionally return `#N/A` or have missing holiday candles.
3. **Throttling**: Having 50+ concurrent `GOOGLEFINANCE("all", ...)` array formulas across a single workbook can cause recalculation delays and `#LOADING...` errors.

### The Solution: Google Apps Script (`Code.gs`)
- [`google_sheets/Code.gs`](file:///c:/Users/surya/Downloads/wyckoff-stock-screener/google_sheets/Code.gs) provides a clean, 1-click execution engine that fetches daily OHLC candles, evaluates target/stop triggers bar-by-bar, records MFE/MAE/R-multiples into `TEST_RESULTS`, and refreshes `DASHBOARD`.

---

## 4. Signal Schema & Field Mapping

| Field | Source | Description |
| :--- | :--- | :--- |
| `Signal_ID` | Python Screener | Unique ID formatted as `{Symbol}_{Signal_Date}` |
| `Signal_Date` | Python Screener | Point-in-time date of signal generation |
| `Symbol` | Python Screener | NSE ticker symbol (e.g. `ZEEL`, `JINDALSAW`) |
| `Company` | Python Screener | Full issuer name |
| `Exchange` | System Default | `"NSE"` |
| `Screener_Score` | Python Screener | 0–100 composite Wyckoff score |
| `Priority` | Python Screener | `HIGH_PRIORITY_CANDIDATE`, `QUALIFIED_CANDIDATE` |
| `Wyckoff_Event` | Python Screener | `LPS`, `SOS`, `Spring`, `ST`, `SC`, `AR`, `UTAD` |
| `Entry_Type` | Strategy Standard | `NEXT_DAY_OPEN` |
| `Entry_Price` | Screener / Actual | Next trading day Open ($T+1$ Open) or signal-day close |
| `Stop_Price` | Configurable | Support level or entry $\times (1 - \text{stop\_pct})$ |
| `Target_1` | Screener / Config | Bruce Fraser P&F horizontal price objective or $+15\%$ |
| `Target_2` | Configurable | Secondary extension target ($+30\%$) |
| `Status` | Google Sheets | `ACTIVE`, `EXITED`, `PENDING` |
| `Exit_Date` | Google Sheets | Realized exit date |
| `Exit_Price` | Google Sheets | Realized exit price |
| `Return_Pct` | Google Sheets | Realized net return (deducting 0.40% friction) |
| `R_Multiple` | Google Sheets | $(\text{Exit} - \text{Entry}) / \text{Risk\_Per\_Share}$ |
| `Days_Held` | Google Sheets | Trading days from entry to exit |
| `Outcome` | Google Sheets | `WIN`, `LOSS`, `BREAKEVEN`, `PENDING` |
| `Notes` | Python Screener | Specific numeric evidence (volume ratio, spread ratio, close pos) |

---

## 5. Entry & Exit Logic

### A. Executable Entry Model
- **Definition**: **Next Trading Day Open ($T+1$ Open)**.
- **Rationale**: An analyst reviewing candidates after market close on Date $T$ cannot execute at the Date $T$ close. The realistic execution price is the opening print on Date $T+1$.

### B. Exit Evaluation Rules
For each daily bar $d \in 1 \dots \text{Max\_Holding\_Days}$:
1. **Target Hit**: Bar $\text{High} \ge \text{Target\_1} \implies$ Exit at Target Price, `TARGET_HIT`, Outcome `WIN`.
2. **Stop Hit**: Bar $\text{Low} \le \text{Stop\_Price} \implies$ Exit at Stop Price, `STOP_HIT`, Outcome `LOSS`.
3. **Time Horizon**: If neither target nor stop is hit after 60 trading days $\implies$ Exit at Close of 60th bar, `TIME_HORIZON_REACHED`.

### C. Same-Day Ambiguity Treatment
If both $\text{High} \ge \text{Target}$ and $\text{Low} \le \text{Stop}$ occur on the **same daily candle**:
- **Default Mode (`CONSERVATIVE`)**: Assumes stop was hit first. Exit recorded at stop price, outcome `LOSS`, flagged as `AMBIGUOUS_SAME_DAY`.
- **Alternative Modes in `SETTINGS`**: `TARGET_FIRST`, `STOP_FIRST`, `EXCLUDE`.

---

## 6. Excursions & Horizon Returns

For every tested trade, the system calculates:
- **Maximum Favorable Excursion (MFE %)**: Peak unrealized gain reached during the holding period:
  $$\text{MFE} = \max_{d} \left( \frac{\text{High}_d - \text{Entry}}{\text{Entry}} \right) \times 100$$
- **Maximum Adverse Excursion (MAE %)**: Worst unrealized drawdown experienced during the holding period:
  $$\text{MAE} = \min_{d} \left( \frac{\text{Low}_d - \text{Entry}}{\text{Entry}} \right) \times 100$$
- **Fixed Horizon Returns**: Mark-to-market net return at **5D, 10D, 20D, 30D, and 60D**.

---

## 7. Lookahead-Bias Protection

- **Mathematical Proof**: Automated test [`tests/google_sheets/test_lookahead_bias.py`](file:///c:/Users/surya/Downloads/wyckoff-stock-screener/tests/google_sheets/test_lookahead_bias.py) verifies that mutating future bars ($T+1 \dots T+90$) with $100\times$ shocks leaves all signal attributes generated on Date $T$ **100% bit-for-bit unchanged**.
- **Data Boundary**: Signal criteria use ONLY data $\le \text{Signal\_Date}$; performance evaluation uses data STRICTLY $> \text{Signal\_Date}$.

---

## 8. Automated Test Results

Executed: `.venv\Scripts\pytest.exe tests/google_sheets/`
- **Total Google Sheets Tests**: **7 / 7 passed (100.0%)** in 2.01 seconds.
  - `test_export_google_sheets.py`: 2 PASS (schema formatting and workbook creation)
  - `test_lookahead_bias.py`: 1 PASS (adversarial future mutation test)
  - `test_trade_evaluator.py`: 4 PASS (target hits, stop hits, same-day ambiguity, MFE/MAE/R-multiples)

---

## 9. Small Validation Sample

Exported top 20 candidates from the 2026-08-24 production run into [`data/google_sheets/phase18_google_sheets_template.xlsx`](file:///c:/Users/surya/Downloads/wyckoff-stock-screener/data/google_sheets/phase18_google_sheets_template.xlsx):
- 20 candidate rows formatted with symbol, company name, score, priority, LPS/SOS events, T+1 Open entry, stop (-5%), P&F target, and numeric evidence.
- Verified all 6 sheets load cleanly in Excel / Google Sheets with zero schema errors.
