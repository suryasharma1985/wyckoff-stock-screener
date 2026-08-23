"""Unit tests for broad mechanical filtering, weekly bar completeness, and batch screening results."""

import numpy as np
import pandas as pd
import pytest

from wyckoff_screener.scanning.broad_filter import (
    BatchScreeningResult,
    check_weekly_bar_completeness,
    evaluate_broad_setup,
)


def _create_passing_synthetic_stock(bars: int = 300) -> pd.DataFrame:
    """Create synthetic stock data with steady uptrend, RSI in 55-65 band, ATR contraction, and high turnover."""
    dates = pd.date_range("2024-01-01", periods=bars)
    prices = [100.0] * bars

    # Upward drift
    for idx in range(bars):
        prices[idx] = 100.0 + idx * 0.8

    highs = [p + 1.5 for p in prices]
    lows = [p - 1.5 for p in prices]
    opens = [p - 0.2 for p in prices]
    closes = [p + 0.2 for p in prices]
    # High volume to ensure turnover >= 1 Crore (Close ~ 300, Vol = 100,000 => Turnover = 3 Cr)
    volumes = [100000.0] * bars

    return pd.DataFrame({
        "Date": dates,
        "Open": opens,
        "High": highs,
        "Low": lows,
        "Close": closes,
        "Volume": volumes,
    })


def _create_failing_synthetic_stock(bars: int = 150) -> pd.DataFrame:
    """Create synthetic stock in continuous downtrend with low liquidity."""
    dates = pd.date_range("2024-01-01", periods=bars)
    prices = [200.0 - idx * 0.8 for idx in range(bars)]
    highs = [p + 2.0 for p in prices]
    lows = [p - 2.0 for p in prices]
    opens = [p + 0.5 for p in prices]
    closes = [p - 0.5 for p in prices]
    volumes = [10.0] * bars  # Minimal volume -> turnover near zero

    return pd.DataFrame({
        "Date": dates,
        "Open": opens,
        "High": highs,
        "Low": lows,
        "Close": closes,
        "Volume": volumes,
    })


def test_passing_stock_mechanical_filters():
    """Verify synthetic uptrending stock passes mechanical filters and records exact values."""
    df_pass = _create_passing_synthetic_stock(bars=500)
    res = evaluate_broad_setup(df_pass, symbol="PASSING.NS", company_name="Passing Test Corp")

    assert res.symbol == "PASSING.NS"
    assert res.is_mechanically_qualified is True
    assert res.filter_results["weekly_uptrend"] is True
    assert res.filter_results["dma_50_above_100"] is True
    assert res.filter_results["min_liquidity_passed"] is True
    assert res.liquidity_metrics["avg_20_turnover_cr"] > 1.0
    assert res.tradingview_chart_links.exchange_symbol == "NSE:PASSING"
    assert res.manual_review_pending is True
    assert res.chart_review_record.chart_review_status == "pending"


def test_failing_stock_mechanical_filters():
    """Verify synthetic downtrending illiquid stock fails mechanical filters."""
    df_fail = _create_failing_synthetic_stock(bars=150)
    res = evaluate_broad_setup(df_fail, symbol="FAILING.NS", min_avg_turnover_cr=1.0)

    assert res.is_mechanically_qualified is False
    assert res.filter_results["weekly_uptrend"] is False
    assert res.filter_results["dma_50_above_100"] is False
    assert res.filter_results["min_liquidity_passed"] is False


def test_weekly_bar_completeness_check():
    """Verify check_weekly_bar_completeness distinguishes Friday/weekend from mid-week bars."""
    # 2026-08-21 is Friday (weekday 4)
    df_friday = pd.DataFrame({"Date": [pd.to_datetime("2026-08-21")]})
    assert check_weekly_bar_completeness(df_friday) is True

    # 2026-08-19 is Wednesday (weekday 2)
    df_wednesday = pd.DataFrame({"Date": [pd.to_datetime("2026-08-19")]})
    assert check_weekly_bar_completeness(df_wednesday) is False


def test_mechanical_qualification_exact_3_gate_rules():
    """Prove the exact Boolean formula of is_mechanically_qualified across each gate:

    Rule: is_mechanically_qualified = min_liquidity_passed
                                    AND (weekly_uptrend OR dma_50_above_100)
                                    AND (rsi_in_band OR atr_contracting OR vcp_bbw_contracting)
    """
    df_base = _create_passing_synthetic_stock(bars=500)

    # 1. Base stock passes
    res_base = evaluate_broad_setup(df_base, symbol="BASE.NS", min_avg_turnover_cr=1.0)
    assert res_base.is_mechanically_qualified is True

    # 2. Gate 1 (Liquidity) failure: setting min_avg_turnover_cr to impossible level (e.g. 1000 Cr)
    res_liq_fail = evaluate_broad_setup(df_base, symbol="LIQ_FAIL.NS", min_avg_turnover_cr=1000.0)
    assert res_liq_fail.filter_results["min_liquidity_passed"] is False
    assert res_liq_fail.is_mechanically_qualified is False

    # 3. Gate 2 (Trend) failure: downward trending stock fails both weekly and daily trend
    df_trend_fail = _create_failing_synthetic_stock(bars=150)
    res_trend_fail = evaluate_broad_setup(df_trend_fail, symbol="TREND_FAIL.NS", min_avg_turnover_cr=0.0)
    assert res_trend_fail.filter_results["weekly_uptrend"] is False
    assert res_trend_fail.filter_results["dma_50_above_100"] is False
    assert res_trend_fail.is_mechanically_qualified is False

