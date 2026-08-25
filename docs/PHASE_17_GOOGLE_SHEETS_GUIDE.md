# Phase 17 — Google Sheets Backtesting User Guide

This guide explains how to upload, navigate, and analyze the historical backtest results from [`data/backtest/phase17_google_sheets_backtest.xlsx`](file:///c:/Users/surya/Downloads/wyckoff-stock-screener/data/backtest/phase17_google_sheets_backtest.xlsx) in **Google Sheets**.

---

## 1. How to Import the Workbook into Google Sheets

1. Open [Google Sheets](https://sheets.google.com).
2. Click **Blank spreadsheet** (or open an existing workspace).
3. Go to **File -> Import -> Upload**.
4. Drag and drop or browse to:
   ```
   c:\Users\surya\Downloads\wyckoff-stock-screener\data\backtest\phase17_google_sheets_backtest.xlsx
   ```
5. In the import options, select **"Replace spreadsheet"** or **"Insert new sheet(s)"** and click **Import data**.

---

## 2. Recommended Sheet Inspection Workflow

We recommend reviewing the sheets in the following order:

### Step 1: `README` & `PARAMETERS`
- Verify the backtest metadata: date range, checkpoint frequency (monthly), entry model (next-day Open $T+1$), and round-trip friction deduction (0.40%).

### Step 2: `MONTHLY_SUMMARY` & `EQUITY_CURVE`
- Inspect month-by-month performance.
- Check `HP_Win_Rate_20D (%)`, `HP_Mean_Net_20D (%)`, and `HP_Alpha_20D (%)` to see if High Priority candidates beat the equal-weighted baseline.
- Review `EQUITY_CURVE` to examine the compounded growth index and drawdown progression.

### Step 3: `SIGNALS` & `TRADES`
- **Filter and Audit**: Use Google Sheets filters on `qualification_status` to isolate `HIGH_PRIORITY_CANDIDATE` or `QUALIFIED_CANDIDATE`.
- Inspect individual stock rows to verify numeric evidence (`explanation`), stop prices, Fraser P&F targets, and realized returns.

### Step 4: `WYCKOFF_ANALYSIS` & `SCORE_ANALYSIS`
- Review which schematic events (e.g. Spring, LPS, SOS) produced the highest win rates and largest R-multiples.
- Review performance across score deciles (e.g. 60–70 vs 50–60).

### Step 5: `PORTFOLIO` & `DRAWDOWN`
- Review the simulated portfolio stats (Portfolios A, B, C) and maximum adverse excursions (MAE) to understand tail risk.

---

## 3. Custom Google Sheets Analysis Ideas

Once imported into Google Sheets, you can easily create:
1. **Interactive Pivot Tables**: Insert a Pivot Table on the `TRADES` tab with `wyckoff_event` in Rows and `AVERAGE(return_percent)` in Values.
2. **Win/Loss Charts**: Create a Bar Chart comparing `HP_Mean_Net_20D (%)` against `Universe_Mean_Gross_20D (%)` across all months.
3. **Scatter Plot**: Plot `initial_risk_percent` vs `R_multiple` to visualize trade payoff distributions.
