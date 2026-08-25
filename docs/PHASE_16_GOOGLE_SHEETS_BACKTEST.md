# Phase 16 — Google Sheets Backtesting System Manual & Formula Guide

**Architecture**:
```text
PYTHON SCREENER
        ↓
Strict Point-in-Time Signal Generation (df.iloc[:i])
        ↓
Backtest Exports: historical_signals.csv + historical_prices.csv + backtest_manifest.json
        ↓
GOOGLE SHEETS WORKBOOK (Transparent, formula-driven auditability)
        ↓
Forward Returns (+5D, +10D, +20D, +40D, +60D), MFE, MAE, Score Buckets, Wyckoff & P&F Analysis
```

---

## 1. Google Sheets Import Workflow

### Step 1: Create Google Sheets Workbook
1. Open Google Sheets and create a new spreadsheet named `Wyckoff_VSA_Historical_Backtest`.

### Step 2: Import `SIGNALS` Tab
1. Click **File -> Import -> Upload**.
2. Select `historical_signals.csv` from `data/backtest_exports/<run_id>/`.
3. Choose **Insert new sheet(s)** and rename the tab to `SIGNALS`.

### Step 3: Import `PRICES` Tab
1. Click **File -> Import -> Upload**.
2. Select `historical_prices.csv` from `data/backtest_exports/<run_id>/`.
3. Choose **Insert new sheet(s)** and rename the tab to `PRICES`.
4. Ensure column `C` is `Trading_Day_Num` and column `B` is `Symbol`.

---

## 2. Workbook Tab Structure & Exact Formulas

---

### TAB 1: `README` / `CONFIG`
Contains strategy parameters, entry models, and transaction cost assumptions.

| Cell | Parameter Name | Default Value | Notes |
| :--- | :--- | :--- | :--- |
| **B3** | `Entry Model` | `next_trading_day_open` | Signal generated on Date D close; Entry on Date D+1 open |
| **B4** | `Transaction Cost (One-Way bps)` | `10` | 0.10% brokerage/STT/turnover charges |
| **B5** | `Slippage (One-Way bps)` | `10` | 0.10% estimated execution slippage |
| **B6** | `Round-Trip Friction (%)` | `=(B4+B5)*2/10000` | 0.40% total round-trip cost subtracted from Gross Return |
| **B7** | `Survivorship Bias Status` | `Survivorship-biased` | Discloses current constituent snapshot |

---

### TAB 2: `SIGNALS`
Raw point-in-time signal export (`historical_signals.csv`).

Key Columns:
- `A: signal_date`
- `B: symbol`
- `G: composite_score`
- `H: candidate_category`
- `I: is_high_priority`
- `J: is_qualified`
- `K: is_candidate`
- `L: is_watchlist`
- `M: is_disqualified`
- `P: most_recent_event_type`
- `AE: pf_target_price`
- `AF: pf_upside_pct`
- `AJ: signal_close`

---

### TAB 3: `PRICES`
Multi-symbol panel price database (`historical_prices.csv`).

Key Columns:
- `A: Date`
- `B: Symbol`
- `C: Trading_Day_Num` (Consecutive 1-indexed bar count per symbol)
- `D: Open`
- `E: High`
- `F: Low`
- `G: Close`
- `H: Volume`

---

### TAB 4: `BACKTEST`
The central evaluation tab where signals are linked to price lookups and forward returns.

#### Column Layout & Formulas (Row 2):

1. **Signal Date (Col A)**: `=SIGNALS!A2`
2. **Symbol (Col B)**: `=SIGNALS!B2`
3. **Composite Score (Col C)**: `=SIGNALS!G2`
4. **Category (Col D)**: `=SIGNALS!H2`
5. **Wyckoff Event (Col E)**: `=SIGNALS!P2`
6. **Signal Close Price (Col F)**: `=SIGNALS!AJ2`

7. **Signal Bar Trading Day Index (Col G)**:
   ```excel
   =INDEX(PRICES!$C:$C, MATCH(1, (PRICES!$A:$A=A2)*(PRICES!$B:$B=B2), 0))
   ```
   *(Note: Enter with `Ctrl+Shift+Enter` as array formula or use `XLOOKUP` if available)*:
   ```excel
   =XLOOKUP(A2&B2, PRICES!$A:$A&PRICES!$B:$B, PRICES!$C:$C)
   ```

8. **Entry Date (D+1) (Col H)**:
   ```excel
   =XLOOKUP((G2+1)&B2, PRICES!$C:$C&PRICES!$B:$B, PRICES!$A:$A, "N/A")
   ```

9. **Entry Price (D+1 Open) (Col I)**:
   ```excel
   =XLOOKUP((G2+1)&B2, PRICES!$C:$C&PRICES!$B:$B, PRICES!$D:$D, "N/A")
   ```

10. **Forward Exit Prices (Cols J to N)**:
    - **+5D Close (Col J)**: `=XLOOKUP((G2+5)&B2, PRICES!$C:$C&PRICES!$B:$B, PRICES!$G:$G, "")`
    - **+10D Close (Col K)**: `=XLOOKUP((G2+10)&B2, PRICES!$C:$C&PRICES!$B:$B, PRICES!$G:$G, "")`
    - **+20D Close (Col L)**: `=XLOOKUP((G2+20)&B2, PRICES!$C:$C&PRICES!$B:$B, PRICES!$G:$G, "")`
    - **+40D Close (Col M)**: `=XLOOKUP((G2+40)&B2, PRICES!$C:$C&PRICES!$B:$B, PRICES!$G:$G, "")`
    - **+60D Close (Col N)**: `=XLOOKUP((G2+60)&B2, PRICES!$C:$C&PRICES!$B:$B, PRICES!$G:$G, "")`

11. **Forward Returns % (Cols O to S)**:
    - **+5D Gross Return (Col O)**: `=IF(ISNUMBER(J2), (J2-I2)/I2, "")`
    - **+10D Gross Return (Col P)**: `=IF(ISNUMBER(K2), (K2-I2)/I2, "")`
    - **+20D Gross Return (Col Q)**: `=IF(ISNUMBER(L2), (L2-I2)/I2, "")`
    - **+40D Gross Return (Col R)**: `=IF(ISNUMBER(M2), (M2-I2)/I2, "")`
    - **+60D Gross Return (Col S)**: `=IF(ISNUMBER(N2), (N2-I2)/I2, "")`

12. **Maximum Favorable Excursion (MFE) over 60 bars (Col T)**:
    ```excel
    =IF(ISNUMBER(I2), (MAXIFS(PRICES!$E:$E, PRICES!$B:$B, B2, PRICES!$C:$C, ">="&(G2+1), PRICES!$C:$C, "<="&(G2+60)) - I2) / I2, "")
    ```

13. **Maximum Adverse Excursion (MAE) over 60 bars (Col U)**:
    ```excel
    =IF(ISNUMBER(I2), (MINIFS(PRICES!$F:$F, PRICES!$B:$B, B2, PRICES!$C:$C, ">="&(G2+1), PRICES!$C:$C, "<="&(G2+60)) - I2) / I2, "")
    ```

14. **Net Returns % (Cols V to Z)**:
    - **+20D Net Return (Col X)**: `=IF(ISNUMBER(Q2), Q2 - README!$B$6, "")`
    - **+60D Net Return (Col Z)**: `=IF(ISNUMBER(S2), S2 - README!$B$6, "")`

---

### TAB 5: `SCORE_ANALYSIS`
Tests the core empirical question: **Do higher scores predict superior forward returns?**

| Score Bucket | Signal Count | Mean +20D Return | Median +20D Return | Win Rate % (>0) | Mean +60D Return | Median +60D Return | Mean MFE | Mean MAE |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **80 – 100** | `=COUNTIFS(BACKTEST!C:C, ">=80")` | `=AVERAGEIFS(BACKTEST!Q:Q, BACKTEST!C:C, ">=80")` | `=MEDIAN(FILTER(BACKTEST!Q:Q, BACKTEST!C:C>=80))` | `=COUNTIFS(BACKTEST!C:C, ">=80", BACKTEST!Q:Q, ">0")/COUNTIFS(BACKTEST!C:C, ">=80", BACKTEST!Q:Q, "<>")` | ... | ... | ... | ... |
| **70 – 79** | `=COUNTIFS(BACKTEST!C:C, ">=70", BACKTEST!C:C, "<80")` | `=AVERAGEIFS(BACKTEST!Q:Q, BACKTEST!C:C, ">=70", BACKTEST!C:C, "<80")` | `=MEDIAN(FILTER(BACKTEST!Q:Q, BACKTEST!C:C>=70, BACKTEST!C:C<80))` | ... | ... | ... | ... | ... |
| **60 – 69** | `=COUNTIFS(BACKTEST!C:C, ">=60", BACKTEST!C:C, "<70")` | `=AVERAGEIFS(BACKTEST!Q:Q, BACKTEST!C:C, ">=60", BACKTEST!C:C, "<70")` | ... | ... | ... | ... | ... | ... |
| **50 – 59** | `=COUNTIFS(BACKTEST!C:C, ">=50", BACKTEST!C:C, "<60")` | `=AVERAGEIFS(BACKTEST!Q:Q, BACKTEST!C:C, ">=50", BACKTEST!C:C, "<60")` | ... | ... | ... | ... | ... | ... |
| **40 – 49** | `=COUNTIFS(BACKTEST!C:C, ">=40", BACKTEST!C:C, "<50")` | `=AVERAGEIFS(BACKTEST!Q:Q, BACKTEST!C:C, ">=40", BACKTEST!C:C, "<50")` | ... | ... | ... | ... | ... | ... |
| **30 – 39** | `=COUNTIFS(BACKTEST!C:C, ">=30", BACKTEST!C:C, "<40")` | `=AVERAGEIFS(BACKTEST!Q:Q, BACKTEST!C:C, ">=30", BACKTEST!C:C, "<40")` | ... | ... | ... | ... | ... | ... |
| **0 – 29** | `=COUNTIFS(BACKTEST!C:C, "<30")` | `=AVERAGEIFS(BACKTEST!Q:Q, BACKTEST!C:C, "<30")` | ... | ... | ... | ... | ... | ... |

---

### TAB 6: `CLASS_ANALYSIS`
Tests whether **High Priority** outperforms **Qualified**, and validates the **Disqualification Gate Edge**.

| Category | N | Mean +10D | Median +10D | Mean +20D | Median +20D | Mean +60D | Median +60D | Win Rate % |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **HIGH_PRIORITY_CANDIDATE** | `=COUNTIF(BACKTEST!D:D, "HIGH_PRIORITY_CANDIDATE")` | `=AVERAGEIF(BACKTEST!D:D, "HIGH_PRIORITY_CANDIDATE", BACKTEST!P:P)` | `=MEDIAN(FILTER(BACKTEST!P:P, BACKTEST!D:D="HIGH_PRIORITY_CANDIDATE"))` | `=AVERAGEIF(BACKTEST!D:D, "HIGH_PRIORITY_CANDIDATE", BACKTEST!Q:Q)` | `=MEDIAN(FILTER(BACKTEST!Q:Q, BACKTEST!D:D="HIGH_PRIORITY_CANDIDATE"))` | `=AVERAGEIF(BACKTEST!D:D, "HIGH_PRIORITY_CANDIDATE", BACKTEST!S:S)` | `=MEDIAN(FILTER(BACKTEST!S:S, BACKTEST!D:D="HIGH_PRIORITY_CANDIDATE"))` | `=COUNTIFS(BACKTEST!D:D, "HIGH_PRIORITY_CANDIDATE", BACKTEST!S:S, ">0")/COUNTIFS(BACKTEST!D:D, "HIGH_PRIORITY_CANDIDATE", BACKTEST!S:S, "<>")` |
| **QUALIFIED_CANDIDATE** | `=COUNTIF(BACKTEST!D:D, "QUALIFIED_CANDIDATE")` | `=AVERAGEIF(BACKTEST!D:D, "QUALIFIED_CANDIDATE", BACKTEST!P:P)` | ... | ... | ... | ... | ... | ... |
| **WATCHLIST** | `=COUNTIF(BACKTEST!D:D, "WATCHLIST")` | ... | ... | ... | ... | ... | ... | ... |
| **DISQUALIFIED** | `=COUNTIF(BACKTEST!D:D, "DISQUALIFIED")` | ... | ... | ... | ... | ... | ... | ... |

---

### TAB 7: `WYCKOFF_ANALYSIS`
Evaluates empirical edge across individual Wyckoff schematic events.

| Event Type | N | Win Rate (+20D) | Median +20D | Mean +20D | Median +60D | Mean +60D | Mean MFE | Mean MAE |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Spring** | `=COUNTIF(BACKTEST!E:E, "Spring")` | `=COUNTIFS(BACKTEST!E:E, "Spring", BACKTEST!Q:Q, ">0")/COUNTIFS(BACKTEST!E:E, "Spring", BACKTEST!Q:Q, "<>")` | `=MEDIAN(FILTER(BACKTEST!Q:Q, BACKTEST!E:E="Spring"))` | `=AVERAGEIF(BACKTEST!E:E, "Spring", BACKTEST!Q:Q)` | ... | ... | ... | ... |
| **LPS** | `=COUNTIF(BACKTEST!E:E, "LPS")` | ... | ... | ... | ... | ... | ... | ... |
| **SOS** | `=COUNTIF(BACKTEST!E:E, "SOS")` | ... | ... | ... | ... | ... | ... | ... |
| **ST** | `=COUNTIF(BACKTEST!E:E, "ST")` | ... | ... | ... | ... | ... | ... | ... |
| **SC** | `=COUNTIF(BACKTEST!E:E, "SC")` | ... | ... | ... | ... | ... | ... | ... |
| **AR** | `=COUNTIF(BACKTEST!E:E, "AR")` | ... | ... | ... | ... | ... | ... | ... |
| **UTAD** | `=COUNTIF(BACKTEST!E:E, "UTAD")` | ... | ... | ... | ... | ... | ... | ... |

---

### TAB 8: `PF_ANALYSIS`
Tests whether Point & Figure price objectives are hit.

| Symbol | Entry Price | Target Price | Projected Upside % | Max Price in 60 Days | Target Reached? | Days to Target |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `=BACKTEST!B2` | `=BACKTEST!I2` | `=SIGNALS!AE2` | `=SIGNALS!AF2` | `=MAXIFS(PRICES!$E:$E, PRICES!$B:$B, B2, PRICES!$C:$C, ">="&(BACKTEST!G2+1), PRICES!$C:$C, "<="&(BACKTEST!G2+60))` | `=IF(E2>=C2, "YES", "NO")` | `=IF(F2="YES", XLOOKUP(TRUE, (PRICES!$B:$B=B2)*(PRICES!$C:$C>BACKTEST!G2)*(PRICES!$E:$E>=C2), PRICES!$C:$C) - BACKTEST!G2, "N/A")` |

**Target Hit Rate Summary Formula**:
```excel
=COUNTIF(F:F, "YES") / COUNTIF(F:F, "<>")
```

---

## 3. Summary of Research Integrity Safeguards

1. **Strict Lookahead Isolation**: All signals in `SIGNALS` are generated using only information known on Date $D$.
2. **Realistic Execution**: Entry occurs on Date $D+1$ Open.
3. **Explicit Friction**: Configurable round-trip friction in `README` ensures net returns are transparent.
4. **Survivorship Disclosure**: Explicitly records that historical universe snapshots introduce survivorship bias unless point-in-time constituent datasets are supplied.
