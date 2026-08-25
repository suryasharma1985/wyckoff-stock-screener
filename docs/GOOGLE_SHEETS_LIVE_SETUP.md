# Google Sheets Live Forward-Testing Deployment Guide (Phase 19)

This guide explains how to deploy and operate the live candidate tracking system in Google Sheets.

---

## 1. How to Upload the Workbook to Google Drive
1. Open your web browser and navigate to [Google Drive](https://drive.google.com).
2. Click **+ New $\to$ File upload**.
3. Select [`data/google_sheets/live_forward_testing_workbook.xlsx`](file:///c:/Users/surya/Downloads/wyckoff-stock-screener/data/google_sheets/live_forward_testing_workbook.xlsx) (or [`google_sheets_template.xlsx`](file:///c:/Users/surya/Downloads/wyckoff-stock-screener/data/google_sheets/google_sheets_template.xlsx) for the full 383 candidates).
4. Wait for the upload to complete.

---

## 2. How to Open with Google Sheets
1. Right-click the uploaded `.xlsx` file in Google Drive.
2. Select **Open with $\to$ Google Sheets**.
3. Google Sheets will automatically convert the workbook into an interactive cloud spreadsheet while preserving all 7 tabs:
   - `README`
   - `INPUT`
   - `LIVE_SIGNALS`
   - `MARKET_DATA`
   - `TRACKING`
   - `SUMMARY`
   - `METHODOLOGY`

---

## 3. Which Cells Require Manual Entry vs. Formulas

| Tab | Columns / Cells | Source Type | User Action |
| :--- | :--- | :---: | :--- |
| **`INPUT`** | `A: Symbol` (e.g. `ZEEL`), `C: Screening_Date` (e.g. `2026-08-21`), `E: Entry_Price` (`107.58`), `H: Screener_Score` (`80`), `J: Wyckoff_Event` (`LPS`) | **User Entry** | Enter symbol, date, and score whenever the Python screener flags a setup. |
| **`INPUT`** | `F: Stop_Loss` (`=E2*0.95`), `G: Target_Price` (`=E2*1.10` or P&F target) | **Formula / Manual** | Pre-calculated by default; can be manually overridden. |
| **`MARKET_DATA`** | `C: Current_Price` (`=GOOGLEFINANCE("NSE:" & A2, "price")`), `H: Historical_Daily` (`=GOOGLEFINANCE("NSE:" & A2, "all", ...)`), `J: Benchmark` (`=GOOGLEFINANCE("NSE:NIFTY 50", "price")`) | **GOOGLEFINANCE** | Evaluated live by Google Finance servers automatically. |
| **`TRACKING`** | `E: Current_Price`, `L to Q: 1D to 60D Returns`, `R: Current_Return`, `U to V: Target/Stop Reached`, `W: Outcome` | **Google Sheets Formula** | Computed automatically as time advances. |
| **`SUMMARY`** | All KPI cells (`Win Rate`, `Open Signals`, `Profit Factor`, `Expectancy`, `Score Deciles`) | **Google Sheets Formula** | Evaluated automatically via `COUNTIF()`, `AVERAGEIFS()`, `MEDIAN()`. |
| **`LIVE_SIGNALS`** | Score breakdown, VSA volume/spread ratios, P&F targets, Wyckoff schematic evidence | **Python Generated** | Copied from the Python production screener report. |

---

## 4. How to Add a New Screener Candidate
1. Run the Python production screener:
   ```powershell
   .venv\Scripts\python.exe scripts/export_google_sheets_validation.py
   ```
2. In Google Sheets, navigate to the **`INPUT`** tab.
3. Add a new row at the bottom:
   - **Symbol**: `TCS`
   - **Exchange**: `NSE`
   - **Screening_Date**: `2026-08-24`
   - **Entry_Price**: `4000.0`
   - **Stop_Loss**: `3800.0`
   - **Target_Price**: `4400.0`
   - **Screener_Score**: `75.0`
   - **Candidate_Category**: `HIGH_PRIORITY_CANDIDATE`
   - **Wyckoff_Event**: `SOS`
4. In the **`TRACKING`** tab, drag the formula row down. Google Finance will immediately begin tracking the new ticker prospectively.

---

## 5. How GOOGLEFINANCE Retrieves Market Data
Google Sheets uses native financial functions:
- **Live Closing Price**:
  ```excel
  =GOOGLEFINANCE("NSE:" & A2, "price")
  ```
- **Historical Daily Bar Series (Open, High, Low, Close, Volume)**:
  ```excel
  =GOOGLEFINANCE("NSE:" & A2, "all", C2, TODAY(), "DAILY")
  ```
- **NIFTY 50 Market Benchmark**:
  ```excel
  =GOOGLEFINANCE("NSE:NIFTY 50", "price")
  ```

---

## 6. What Python Does vs. What Google Sheets Does (Option B Hybrid Model)

> [!NOTE]
> **Why Option B (Hybrid Architecture) is Necessary**:
> Google Sheets cannot natively compute multi-period volume ratios, Wyckoff absorption structures, or 3-box reversal Point & Figure chart horizontal counts. Attempting to force these into complex spreadsheet formulas causes performance degradation and high error risk.

- **Python Quantitative Layer**:
  1. Bar-by-bar VSA volume spread and close position analysis.
  2. Multi-bar accumulation structure detection (Spring, LPS, SOS, Secondary Tests).
  3. Bruce Fraser Point & Figure horizontal count price objectives.
  4. Multi-factor composite setup scoring (0–100) and mechanical qualification gates.
- **Google Sheets Forward-Testing Layer**:
  1. Live and historical market price retrieval via `=GOOGLEFINANCE()`.
  2. Point-in-time forward mark-to-market calculations (+1D, +5D, +10D, +20D, +30D, +60D).
  3. Peak favorable excursion (MFE) and adverse excursion (MAE) measurements.
  4. Target and stop loss touch determination and same-day ambiguity classification (`AMBIGUOUS`).
  5. Executive KPI dashboard aggregation (Win Rate, Profit Factor, Expectancy, Score Deciles).

---

## 7. Known Limitations of GOOGLEFINANCE
1. **Intraday Sequence**: Daily `=GOOGLEFINANCE()` returns daily High and Low prices. If both Target 1 and Stop Loss fall within the same daily candle range, Google Sheets classifies the trade as `AMBIGUOUS`.
2. **Small-Cap & Micro-Cap Coverage**: Certain illiquid or newly listed NSE tickers may return `#N/A` or have a 15-minute price delay. These are marked as `INSUFFICIENT DATA` rather than false losses.
3. **Historical Array Size Limits**: Google Sheets limits the size of dynamic array expansions in historical queries. The workbook formulas use structured `INDEX()` lookups to remain light and responsive.
