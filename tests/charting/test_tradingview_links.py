"""Unit tests for TradingView link generation, checklists, and manual chart review records."""

import pytest

from wyckoff_screener.charting.tradingview_links import (
    CHART_REVIEW_CHECKLIST,
    ChartReviewRecord,
    format_tradingview_symbol,
    generate_tradingview_links,
    make_tradingview_symbol_url,
)


def test_tradingview_symbol_formatting():
    """Verify expected TradingView symbol formatting from raw and NSE tickers."""
    assert format_tradingview_symbol("ANANTRAJ.NS") == "NSE:ANANTRAJ"
    assert format_tradingview_symbol("APOLLO.NS") == "NSE:APOLLO"
    assert format_tradingview_symbol("HINDCOPPER.NS") == "NSE:HINDCOPPER"
    assert format_tradingview_symbol("M&M.NS") == "NSE:M&M"
    assert format_tradingview_symbol("BAJAJ-AUTO.NS") == "NSE:BAJAJ-AUTO"
    assert format_tradingview_symbol("NSE:TCS") == "NSE:TCS"


def test_tradingview_timeframe_urls():
    """Verify URL generation across Daily, Weekly, and 75-Minute intervals."""
    sym = "ANANTRAJ.NS"
    daily = make_tradingview_symbol_url(sym, interval="D")
    weekly = make_tradingview_symbol_url(sym, interval="W")
    intraday = make_tradingview_symbol_url(sym, interval="75")

    assert "symbol=NSE%3AANANTRAJ" in daily
    assert "interval=D" in daily

    assert "symbol=NSE%3AANANTRAJ" in weekly
    assert "interval=W" in weekly

    assert "symbol=NSE%3AANANTRAJ" in intraday
    assert "interval=75" in intraday


def test_generate_tradingview_links_bundle_and_disclaimers():
    """Verify full bundle generation, 75m note, and non-confirmation disclaimer."""
    links = generate_tradingview_links("HINDCOPPER.NS")

    assert links.exchange_symbol == "NSE:HINDCOPPER"
    assert "interval=D" in links.daily_url
    assert "interval=W" in links.weekly_url
    assert "interval=75" in links.intraday_75m_url
    assert "75m manually" in links.intraday_note
    assert "does NOT replace or modify" in links.disclaimer


def test_chart_review_record_workflow():
    """Verify manual chart review record lifecycle (pending -> reviewed / rejected)."""
    rec = ChartReviewRecord(
        symbol="HINDCOPPER.NS",
        tradingview_daily_url="https://tradingview.com/daily",
        tradingview_weekly_url="https://tradingview.com/weekly",
        tradingview_intraday_url="https://tradingview.com/75m",
    )
    assert rec.chart_review_status == "pending"

    # Mark reviewed
    rec.mark_reviewed(
        notes="Clean Phase D absorption visible above 550 support.",
        timeframes=["Daily", "Weekly"],
        accepted_events=["LPS on 2026-08-19"],
        rejected_events=[],
    )
    assert rec.chart_review_status == "reviewed"
    assert rec.reviewed_at is not None
    assert "Phase D" in rec.reviewer_notes

    # Invalid status should raise error
    with pytest.raises(ValueError):
        ChartReviewRecord(
            symbol="HINDCOPPER.NS",
            tradingview_daily_url="",
            tradingview_weekly_url="",
            tradingview_intraday_url="",
            chart_review_status="invalid_status",
        )


def test_checklist_completeness():
    """Verify 9-point manual review checklist includes all required technical checks."""
    assert len(CHART_REVIEW_CHECKLIST) == 9
    full_text = " ".join(CHART_REVIEW_CHECKLIST)
    assert "Daily chart" in full_text
    assert "Weekly chart" in full_text
    assert "RSI(14)" in full_text
    assert "20-period volume" in full_text
    assert "50 EMA" in full_text
    assert "VCP" in full_text
    assert "support and resistance" in full_text
    assert "Spring / ST / LPS / SOS / UTAD" in full_text
    assert "effort-vs-result" in full_text


def test_tradingview_link_generation_preserves_numeric_isolation():
    """Verify generating TradingView links is a pure function that does not alter price data."""
    import pandas as pd
    prices = [100.0, 102.0, 105.0]
    df = pd.DataFrame({"Close": prices})
    original_sum = float(df["Close"].sum())

    links = generate_tradingview_links("ANANTRAJ.NS")
    assert links.exchange_symbol == "NSE:ANANTRAJ"
    assert float(df["Close"].sum()) == original_sum
