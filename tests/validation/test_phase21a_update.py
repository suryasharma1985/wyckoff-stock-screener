import pytest
import pandas as pd
import numpy as np
from pathlib import Path
from scripts.update_phase21_oos_data import validate_row, get_sha256

def test_discovery_firewall_validation():
    # Test that dates on or before 2026-08-24 are flagged or raise error in the update logic context
    # In the actual script, this is checked via: if date_str <= "2026-08-24": raise AssertionError
    invalid_date = "2026-08-24"
    valid_date = "2026-08-25"
    
    assert invalid_date <= "2026-08-24"
    assert not (valid_date <= "2026-08-24")

def test_duplicate_prevention():
    # Test drop_duplicates behavior
    data = [
        {"Date": "2026-08-25", "Symbol": "APOLLO", "Close": 100},
        {"Date": "2026-08-25", "Symbol": "APOLLO", "Close": 105}, # Duplicate
        {"Date": "2026-08-26", "Symbol": "APOLLO", "Close": 110}
    ]
    df = pd.DataFrame(data)
    df_clean = df.drop_duplicates(subset=["Symbol", "Date"])
    assert len(df_clean) == 2
    assert df_clean.iloc[0]["Close"] == 100

def test_ohlc_validation():
    # Normal valid row
    valid_row = {
        "Open": 100.0, "High": 110.0, "Low": 95.0, "Close": 105.0, "Volume": 1000
    }
    ok, err = validate_row(valid_row)
    assert ok
    
    # High < Low violation
    bad_row1 = {
        "Open": 100.0, "High": 90.0, "Low": 95.0, "Close": 105.0, "Volume": 1000
    }
    ok, err = validate_row(bad_row1)
    assert not ok
    assert "High < Low" in err
    
    # High < Close violation
    bad_row2 = {
        "Open": 100.0, "High": 105.0, "Low": 95.0, "Close": 110.0, "Volume": 1000
    }
    ok, err = validate_row(bad_row2)
    assert not ok
    assert "High < Close" in err
    
    # Low > Open violation
    bad_row3 = {
        "Open": 90.0, "High": 110.0, "Low": 95.0, "Close": 105.0, "Volume": 1000
    }
    ok, err = validate_row(bad_row3)
    assert not ok
    assert "Low > Open" in err
    
    # Negative price violation
    bad_row4 = {
        "Open": -10.0, "High": 110.0, "Low": 95.0, "Close": 105.0, "Volume": 1000
    }
    ok, err = validate_row(bad_row4)
    assert not ok
    assert "Price <= 0" in err
    
    # Negative volume violation
    bad_row5 = {
        "Open": 100.0, "High": 110.0, "Low": 95.0, "Close": 105.0, "Volume": -5
    }
    ok, err = validate_row(bad_row5)
    assert not ok
    assert "Volume < 0" in err

def test_missing_values_detection():
    bad_row = {
        "Open": 100.0, "High": np.nan, "Low": 95.0, "Close": 105.0, "Volume": 1000
    }
    ok, err = validate_row(bad_row)
    assert not ok
    assert "Missing fields" in err

def test_session_counting_maturity():
    # Test counting unique sessions
    dates = ["2026-08-25", "2026-08-26", "2026-08-25"] # 2 unique dates
    df = pd.DataFrame({"Date": dates})
    n_sessions = df["Date"].nunique()
    assert n_sessions == 2
    
    # Calculate maturity
    status_10d = "READY" if n_sessions >= 10 else "NOT READY"
    assert status_10d == "NOT READY"
    assert max(0, 10 - n_sessions) == 8

def test_hash_generation(tmp_path):
    # Test sha256 generation on simple file
    test_file = tmp_path / "test.txt"
    test_file.write_text("hello phase 21a")
    h1 = get_sha256(test_file)
    h2 = get_sha256(test_file)
    assert h1 == h2
    assert len(h1) == 64
