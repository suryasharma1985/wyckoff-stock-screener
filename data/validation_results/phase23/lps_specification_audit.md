# Experiment 8: LPS Breakout Specification Audit

This document formalizes the mechanical rules for conditional LPS breakout trading setups and identifies design parameters that require research decisions before backtesting can commence.

## Mechanical Specifications

1. **LPS Identification:**
   An LPS candidate is identified when a stock forms a higher low holding above trading range support on below-average volume (volume ratio < 0.75).
2. **Breakout Trigger:**
   **UNSPECIFIED — REQUIRES RESEARCH DECISION**
   * *Option A:* Close above the local trading range resistance.
   * *Option B:* Intrabar high crossing above resistance by 1% or 2%.
3. **Entry Price:**
   **UNSPECIFIED — REQUIRES RESEARCH DECISION**
   * *Option A:* Limit order placed at the resistance breakout level.
   * *Option B:* Next-day Open execution.
4. **Structural Stop-Loss:**
   Placed 1 ATR below the low of the most recent Spring or Secondary Test (ST) candidate in the accumulation base.
5. **Profit Target:**
   Set dynamically using the Point & Figure (P&F) horizontal count price objective.
6. **Time-Stop:**
   **UNSPECIFIED — REQUIRES RESEARCH DECISION**
   * *Option A:* Exit after 60 trading days if neither stop nor target is hit.
   * *Option B:* Hold position indefinitely until target/stop trigger.
7. **Position Sizing:**
   **UNSPECIFIED — REQUIRES RESEARCH DECISION**
   * *Option A:* Equal-weight allocation (e.g. 5% capital per trade).
   * *Option B:* Volatility-adjusted sizing (inverse ATR allocation).
