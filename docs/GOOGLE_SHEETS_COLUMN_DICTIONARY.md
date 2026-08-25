# Google Sheets Forward-Validation Column Dictionary

This document provides complete, unambiguous definitions, source attributions, and data types for all columns across the 8 tabs of the Phase 18 Google Sheets Forward-Validation System.

---

## 1. `CANDIDATES` Tab (Columns A through V)

| Col | Field Name | Type | Source | Definition & Formula |
| :---: | :--- | :---: | :---: | :--- |
| **A** | `Candidate_ID` | String | Python Screener | Unique identifier structured as `{YYYYMMDD}_{SYMBOL}` (e.g. `20260824_ZEEL`). Prevents collisions across runs. |
| **B** | `Screening_Date` | Date | Python Screener | Point-in-time date of screener execution (e.g. `2026-08-21`). |
| **C** | `Symbol` | String | Python Screener | National Stock Exchange (NSE) ticker symbol (e.g. `ZEEL`, `JINDALSAW`). |
| **D** | `Company_Name` | String | Python Screener | Full legal corporate issuer name. |
| **E** | `Exchange` | String | System | Equity exchange (`"NSE"`). |
| **F** | `Priority` | String | Python Screener | Screener category: `HIGH_PRIORITY_CANDIDATE` (Score $\ge 60$) or `QUALIFIED_CANDIDATE` ($40 - 59.99$). |
| **G** | `Setup` | String | Python Screener | Wyckoff setup classification (e.g. `Wyckoff LPS Setup`, `Wyckoff SOS Setup`). |
| **H** | `Score` | Float | Python Screener | 0–100 quantified composite score combining mechanical filters, VSA bar evidence, and P&F target ratio. |
| **I** | `Qualification_Status` | String | Python Screener | `QUALIFIED` if broad trend, moving average, RSI, and liquidity filters passed; else `UNQUALIFIED`. |
| **J** | `Wyckoff_Event` | String | Python Screener | Most recent detected schematic event (`Spring`, `LPS`, `SOS`, `ST`, `SC`, `AR`, `UTAD`). |
| **K** | `Entry_Price` | Float | Python Screener | Authoritative closing price on `Screening_Date`. Immutable baseline for forward return measurements. |
| **L** | `Entry_Date` | Date | Python Screener | Date of signal evaluation / intended entry observation. |
| **M** | `Initial_Stop` | Float | Config / Calc | Stop loss price level. Defaults to $\text{Entry\_Price} \times (1 - 0.05)$ ($-5.0\%$). |
| **N** | `Target_1` | Float | Config / Calc | Profit Target 1. Bruce Fraser P&F horizontal price objective if available; otherwise $\text{Entry\_Price} \times 1.10$ ($+10.0\%$). |
| **O** | `Target_2` | Float | Config / Calc | Secondary extension target ($\text{Entry\_Price} \times 1.20$ or $\text{Target\_1} \times 1.15$). |
| **P** | `Target_3` | Float | Config / Calc | Tertiary extension target ($\text{Entry\_Price} \times 1.30$ or $\text{Target\_1} \times 1.30$). |
| **Q** | `Risk_Per_Share` | Float | Calculated | Monetary risk per share: $\text{Entry\_Price} - \text{Initial\_Stop}$. |
| **R** | `Risk_Percent` | Float | Calculated | Initial risk percentage: $(\text{Risk\_Per\_Share} / \text{Entry\_Price}) \times 100$. |
| **S** | `TradingView_URL` | String | Python Screener | Direct interactive URL to TradingView Daily Chart with pre-formatted ticker and timeframes. |
| **T** | `Screener_Reason` | String | Python Screener | Explicit numeric evidence behind event (volume ratio, spread ratio, close position, ATR contraction). |
| **U** | `Data_Source` | String | Python Screener | File path / snapshot provenance of the source OHLCV data. |
| **V** | `Validation_Status` | String | System | Tracking status (`PENDING_FORWARD_EVALUATION`, `ACTIVE_TRACKING`, `COMPLETED`). |

---

## 2. `SIGNALS` Tab

| Field Name | Type | Definition |
| :--- | :---: | :--- |
| `Candidate_ID` | String | Matching Candidate ID linking to CANDIDATES tab. |
| `Symbol` | String | NSE ticker symbol. |
| `Screening_Date`| Date | Date when screener identified candidate. |
| `Candidate_Price`| Float | Closing price on screening date. |
| `Actual_Entry_Date` | Date | Actual execution date. |
| `Actual_Entry_Price`| Float | Actual execution entry price. |
| `Stop_Price` | Float | Active protective stop loss level. |
| `Target_1, 2, 3` | Float | Active profit target levels. |
| `Exit_Date` | Date | Date when position exited (target, stop, or time expiration). |
| `Exit_Price` | Float | Realized exit execution price. |
| `Exit_Reason` | String | `TARGET_1_HIT`, `STOP_LOSS_HIT`, `TIME_LIMIT_REACHED`, `AMBIGUOUS`. |
| `Holding_Period` | Integer | Trading sessions held from entry to exit. |
| `Status` | String | `OPEN`, `COMPLETED`, `INVALID`. |

---

## 3. `PERFORMANCE` Tab

| Field Name | Type | Definition & Formula |
| :--- | :---: | :--- |
| `Forward_Return_1D (%)` | Float | Return after 1 trading day: $((P_{T+1} - P_{\text{entry}}) / P_{\text{entry}}) \times 100$. |
| `Forward_Return_3D (%)` | Float | Return after 3 trading days: $((P_{T+3} - P_{\text{entry}}) / P_{\text{entry}}) \times 100$. |
| `Forward_Return_5D (%)` | Float | Return after 5 trading days: $((P_{T+5} - P_{\text{entry}}) / P_{\text{entry}}) \times 100$. |
| `Forward_Return_10D (%)`| Float | Return after 10 trading days: $((P_{T+10} - P_{\text{entry}}) / P_{\text{entry}}) \times 100$. |
| `Forward_Return_20D (%)`| Float | Return after 20 trading days: $((P_{T+20} - P_{\text{entry}}) / P_{\text{entry}}) \times 100$. |
| `Forward_Return_30D (%)`| Float | Return after 30 trading days: $((P_{T+30} - P_{\text{entry}}) / P_{\text{entry}}) \times 100$. |
| `Forward_Return_40D (%)`| Float | Return after 40 trading days: $((P_{T+40} - P_{\text{entry}}) / P_{\text{entry}}) \times 100$. |
| `Forward_Return_60D (%)`| Float | Return after 60 trading days: $((P_{T+60} - P_{\text{entry}}) / P_{\text{entry}}) \times 100$. |
| `Forward_Return_1M (%)` | Float | Return after ~21 trading days (1 calendar month). |
| `Forward_Return_3M (%)` | Float | Return after ~63 trading days (3 calendar months). |
| `MFE_5D / 10D / 20D / 40D / 60D (%)` | Float | Maximum Favorable Excursion: $(\max(\text{High}_d) - P_{\text{entry}}) / P_{\text{entry}} \times 100$. |
| `MAE_5D / 10D / 20D / 40D / 60D (%)` | Float | Maximum Adverse Excursion: $(\min(\text{Low}_d) - P_{\text{entry}}) / P_{\text{entry}} \times 100$. |
| `Target_1 / 2 / 3_Hit` | String | `YES` if $\text{High}_d \ge \text{Target}$, else `NO`. |

| `Stop_Hit` | String | `YES` if $\text{Low}_d \le \text{Stop}$, else `NO`. |
| `Candidate_Return (%)` | Float | Total return from entry to current price / exit. |
| `NIFTY_Return (%)` | Float | NIFTY 50 benchmark return over the exact matching holding window. |
| `Excess_Return (%)` | Float | Alpha over benchmark: $\text{Candidate\_Return} - \text{NIFTY\_Return}$. |

---

## 4. `TRADE_LOG` Tab

| Field Name | Type | Definition |
| :--- | :---: | :--- |
| `Outcome_Type` | String | `WIN` (Target before Stop), `LOSS` (Stop before Target), `OPEN`, `AMBIGUOUS`, `NOT_VALID`. |
| `Realized_Return (%)` | Float | Net realized percentage return on closed trade. |
| `R_Multiple` | Float | Realized return in risk units: $(P_{\text{exit}} - P_{\text{entry}}) / \text{Risk\_Per\_Share}$. |
| `Lookahead_Check` | String | `PASS` (verified zero future price influence on signal generation). |

---

## 5. `SUMMARY` Tab

Contains aggregated executive KPIs, Score Predictive Bands (`<40`, `40–49.99`, `50–59.99`, `60–69.99`, `70–79.99`, `80+`), Priority Comparison (`HIGH PRIORITY` vs `QUALIFIED`), and Wyckoff Event breakdowns (`Spring`, `LPS`, `SOS`, `ST`, `SC`, `AR`, `UTAD`).
