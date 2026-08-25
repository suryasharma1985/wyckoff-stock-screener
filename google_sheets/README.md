# Google Sheets Stock Screener Validation & Forward-Testing System

This directory contains the Google Sheets template and Google Apps Script (`Code.gs`) for validating Wyckoff stock screener signals through a lightweight, rolling research ledger.

---

## 1. Quick Start: Setting Up the Google Sheet

### Step 1: Upload the Template to Google Drive / Sheets
1. Open [Google Sheets](https://sheets.google.com).
2. Click **File -> Import -> Upload**.
3. Select [`data/google_sheets/phase18_google_sheets_template.xlsx`](file:///c:/Users/surya/Downloads/wyckoff-stock-screener/data/google_sheets/phase18_google_sheets_template.xlsx).
4. Choose **"Replace spreadsheet"** and click **Import data**.

### Step 2: Add Google Apps Script (Automated Daily Price Evaluation)
1. In your newly created Google Sheet, click **Extensions -> Apps Script**.
2. Delete any default code in the editor.
3. Open [`google_sheets/Code.gs`](file:///c:/Users/surya/Downloads/wyckoff-stock-screener/google_sheets/Code.gs), copy all contents, and paste them into the Apps Script editor.
4. Click **Save** (disk icon) and name the project `WyckoffScreenerValidation`.
5. Return to your Google Sheet and reload the page.
6. A new menu **"📊 Wyckoff Screener"** will appear in the top toolbar.

---

## 2. Standard Operating Workflow

### Adding New Screener Candidates:
1. Run our Python screener or export script:
   ```bash
   python scripts/export_google_sheets.py --top-n 20
   ```
2. Open [`data/google_sheets/screener_signals.csv`](file:///c:/Users/surya/Downloads/wyckoff-stock-screener/data/google_sheets/screener_signals.csv).
3. Copy the rows (or selected candidates) and paste them below existing rows on the **`SIGNALS`** sheet.
4. Click **"📊 Wyckoff Screener" -> "▶️ Evaluate All Signals & Update Dashboard"**.
5. The Apps Script automatically:
   - Fetches historical/current daily OHLC bars starting from `Signal_Date`.
   - Evaluates whether Target 1 (+15% or P&F target) or Stop Loss (-5%) was reached first.
   - Calculates MFE (Maximum Favorable Excursion), MAE (Maximum Adverse Excursion), forward returns (5D, 10D, 20D, 30D, 60D), and R-multiples.
   - Populates the **`TEST_RESULTS`** tab.
   - Updates the live aggregate KPIs on the **`DASHBOARD`** tab.

---

## 3. Sheet Architecture

| Tab Name | Description |
| :--- | :--- |
| **`SIGNALS`** | Primary signal input ledger. Paste screener candidates here. Records symbol, date, score, priority, entry, stop, and targets. |
| **`PRICE_DATA`** | Reference and helper sheet for `=GOOGLEFINANCE()` daily OHLC queries. |
| **`TEST_RESULTS`** | Detailed per-trade outcome table (exits, holding days, returns, MFE, MAE, R-multiples, target/stop flags). |
| **`DASHBOARD`** | Aggregate research metrics: Win Rate, Average Return, Profit Factor, Target/Stop Hit Rates, Excursions. |
| **`SETTINGS`** | Configurable parameters: Stop %, Target %, Max Holding Days, Friction %, Ambiguity Handling. |
| **`README`** | Quick in-sheet reference and workflow reminders. |

---

## 4. Key Methodology Rules

1. **Zero Lookahead Bias**:
   - Signal criteria and screener scores are derived **strictly on or before Signal Date $T$**.
   - Performance evaluation uses daily OHLC candles occurring **strictly on or after Date $T+1$**.
2. **Next-Day Open Entry**:
   - The executable entry model is strictly the next market trading day's opening price ($T+1$ Open).
3. **Daily Candle OHLC Evaluation**:
   - Daily **High** determines whether a profit target was reached.
   - Daily **Low** determines whether a stop loss was triggered.
   - Daily **Close** is used for intermediate mark-to-market returns.
4. **Same-Day Ambiguity**:
   - If both Target and Stop are hit on the same daily candle, `CONSERVATIVE` mode records a stop exit.

---

## 5. GOOGLEFINANCE vs Apps Script Limitations

- **GOOGLEFINANCE Formula**: Works well for liquid NSE stocks (`=GOOGLEFINANCE("NSE:RELIANCE", "all", startDate, endDate)`), but can produce `#N/A` or `#LOADING` on micro-cap equities and cannot easily scan dynamic multi-day High/Low ranges in a single cell.
- **Apps Script (`Code.gs`)**: Solves this by fetching the exact daily OHLC series, iterating over each bar chronologically, and updating `TEST_RESULTS` deterministically.
