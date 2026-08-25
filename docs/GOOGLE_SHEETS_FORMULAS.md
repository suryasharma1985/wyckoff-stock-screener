# Google Sheets Formulas & Calculation Guide

This guide details the exact formulas implemented in the Phase 18 Google Sheets Forward-Validation System.

---

## 1. Market Data Retrieval (GOOGLEFINANCE)

### A. Daily Closing Price History for NSE Equities
Retrieves daily closing prices from signal date to current date:
```excel
=GOOGLEFINANCE("NSE:" & C2, "price", B2, TODAY(), "DAILY")
```
- `C2`: Symbol (e.g. `ZEEL`)
- `B2`: Screening Date (e.g. `DATE(2026,8,21)`)

### B. Full Daily Candlestick History (Open, High, Low, Close, Volume)
```excel
=GOOGLEFINANCE("NSE:" & C2, "all", B2, TODAY(), "DAILY")
```

### C. NIFTY 50 Benchmark History
```excel
=GOOGLEFINANCE("NSE:NIFTY 50", "price", B2, TODAY(), "DAILY")
```

---

## 2. Forward Return Formulas

### A. Fixed-Horizon Forward Returns (1D, 3D, 5D, 10D, 20D, 30D, 60D)
Where $P_{\text{entry}}$ is cell `K2` (Entry Price) and $P_{T+N}$ is the price on trading day $N$:
```excel
=((INDEX(PRICE_DATA!$B$2:$B$100, N) / K2) - 1) * 100
```
- **5D Return**: `((INDEX(PRICE_DATA!$B$2:$B$100, 5) / K2) - 1) * 100`
- **10D Return**: `((INDEX(PRICE_DATA!$B$2:$B$100, 10) / K2) - 1) * 100`
- **20D Return**: `((INDEX(PRICE_DATA!$B$2:$B$100, 20) / K2) - 1) * 100`
- **40D Return**: `((INDEX(PRICE_DATA!$B$2:$B$100, 40) / K2) - 1) * 100`
- **60D Return**: `((INDEX(PRICE_DATA!$B$2:$B$100, 60) / K2) - 1) * 100`


### B. Current Unrealized Return
```excel
=((M2 - K2) / K2) * 100
```
- `M2`: Current Price
- `K2`: Entry Price

---

## 3. Maximum Favorable & Adverse Excursion (MFE / MAE)

### A. Maximum Favorable Excursion (MFE 20D)
Peak percentage gain achieved above entry during the first 20 sessions:
```excel
=((MAX(INDEX(PRICE_DATA!$C$2:$C$100, 1):INDEX(PRICE_DATA!$C$2:$C$100, 20)) - K2) / K2) * 100
```
- `PRICE_DATA!$C$2:$C$100`: High price column

### B. Maximum Adverse Excursion (MAE 20D)
Worst percentage drawdown experienced below entry during the first 20 sessions:
```excel
=((MIN(INDEX(PRICE_DATA!$D$2:$D$100, 1):INDEX(PRICE_DATA!$D$2:$D$100, 20)) - K2) / K2) * 100
```
- `PRICE_DATA!$D$2:$D$100`: Low price column

---

## 4. Target & Stop Detection Formulas

### A. Target 1 Reached (+10%)
```excel
=IF(MAX(PRICE_DATA!$C$2:$C$100) >= N2, "YES", "NO")
```
- `N2`: Target 1 price level

### B. Stop Loss Reached (-5%)
```excel
=IF(MIN(PRICE_DATA!$D$2:$D$100) <= M2, "YES", "NO")
```
- `M2`: Initial Stop price level

### C. Same-Day Ambiguity & Result Classification
If Target 1 Hit Day equals Stop Loss Hit Day on the same daily candle:
```excel
=IF(AND(Target_1_Hit_Day = Stop_Hit_Day, Target_1_Hit_Day > 0), "AMBIGUOUS",
  IF(AND(Target_1_Hit_Day > 0, OR(Stop_Hit_Day = 0, Target_1_Hit_Day < Stop_Hit_Day)), "WIN",
  IF(AND(Stop_Hit_Day > 0, OR(Target_1_Hit_Day = 0, Stop_Hit_Day < Target_1_Hit_Day)), "LOSS",
  "OPEN")))
```

---

## 5. Benchmark Alpha & Excess Return

```excel
=Candidate_Return_% - NIFTY_Return_%
```
- **Positive Excess Return**: Screener candidate generated alpha over the broad market.
- **Negative Excess Return**: Candidate underperformed the NIFTY 50 index.

---

## 6. Executive Summary Dashboard Formulas

### A. Win Rate (%)
```excel
=IF((COUNTIF(TRADE_LOG!G:G, "WIN") + COUNTIF(TRADE_LOG!G:G, "LOSS")) > 0,
  COUNTIF(TRADE_LOG!G:G, "WIN") / (COUNTIF(TRADE_LOG!G:G, "WIN") + COUNTIF(TRADE_LOG!G:G, "LOSS")) * 100,
  0)
```

### B. Trade Expectancy (%)
```excel
=(Win_Rate * AVERAGEIF(TRADE_LOG!G:G, "WIN", TRADE_LOG!H:H)) -
 ((100 - Win_Rate) * ABS(AVERAGEIF(TRADE_LOG!G:G, "LOSS", TRADE_LOG!H:H)))
```
- `TRADE_LOG!H:H`: Realized Net Return (%) column

### C. Score-Band Win Rate
```excel
=COUNTIFS(CANDIDATES!H:H, ">=60", CANDIDATES!H:H, "<70", TRADE_LOG!G:G, "WIN") /
 MAX(1, COUNTIFS(CANDIDATES!H:H, ">=60", CANDIDATES!H:H, "<70", TRADE_LOG!G:G, "<>OPEN")) * 100
```
