"""Unit tests for Daily Automation and Session Pre-Flight Checks."""

from datetime import date
from pathlib import Path
import pytest

from scripts.check_nse_session import is_nse_trading_day, NSE_HOLIDAYS


def test_weekend_detected_as_non_trading():
    """Verify Saturdays and Sundays are identified as non-trading days."""
    saturday = date(2026, 8, 22)  # Saturday
    sunday = date(2026, 8, 23)    # Sunday
    
    is_sat, reason_sat = is_nse_trading_day(saturday)
    assert not is_sat
    assert "Weekend" in reason_sat
    
    is_sun, reason_sun = is_nse_trading_day(sunday)
    assert not is_sun
    assert "Weekend" in reason_sun


def test_official_nse_holiday_detected():
    """Verify known NSE holidays are identified."""
    republic_day = date(2026, 1, 26)
    independence_day = date(2026, 8, 15)
    gandhi_jayanti = date(2026, 10, 2)
    
    is_rep, reason_rep = is_nse_trading_day(republic_day)
    assert not is_rep
    assert "Official NSE Trading Holiday" in reason_rep

    is_ind, reason_ind = is_nse_trading_day(independence_day)
    assert not is_ind

    is_gan, reason_gan = is_nse_trading_day(gandhi_jayanti)
    assert not is_gan


def test_regular_trading_day_detected():
    """Verify normal trading day passes check."""
    trading_day = date(2026, 8, 24)  # Monday, non-holiday
    is_trading, reason = is_nse_trading_day(trading_day)
    assert is_trading
    assert reason == "Trading Day"


def test_github_workflow_yaml_syntax():
    """Verify GitHub Actions workflow file exists and has required keys."""
    workflow_file = Path(".github/workflows/daily_screen.yml")
    assert workflow_file.exists(), "daily_screen.yml workflow must exist"
    
    content = workflow_file.read_text(encoding="utf-8")
    assert "schedule:" in content
    assert "cron:" in content
    assert "workflow_dispatch:" in content
    assert "run_daily_screening.py" in content
    assert "check_nse_session.py" in content
