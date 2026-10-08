"""
Unit tests for the dashboard SOS Highlight View pure helper module (dashboard/sos_view.py).
"""

import sys
from pathlib import Path

# Ensure repo root is on sys.path for dashboard module discovery
repo_root = Path(__file__).resolve().parent.parent.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

import pandas as pd
import pytest
from dashboard.sos_view import (
    classify_sos_status,
    add_sos_status_column,
    prepare_sos_display_df,
    SOS_STATUS_LABEL,
    OTHER_EVENT_LABEL,
    NO_EVENT_LABEL
)

def test_classify_sos_status_direct_sos():
    row = {"most_recent_event_type": "SOS", "possible_SOS": False}
    assert classify_sos_status(row) == SOS_STATUS_LABEL

def test_classify_sos_status_other_event():
    row = {"most_recent_event_type": "Spring", "possible_SOS": False}
    assert classify_sos_status(row) == OTHER_EVENT_LABEL
    
    row_sc = {"most_recent_event_type": "SC", "possible_SOS": False}
    assert classify_sos_status(row_sc) == OTHER_EVENT_LABEL

def test_classify_sos_status_possible_sos_precedence():
    # possible_SOS True even when most_recent_event_type is None/empty
    row = {"most_recent_event_type": None, "possible_SOS": True}
    assert classify_sos_status(row) == SOS_STATUS_LABEL
    
    row_str = {"most_recent_event_type": "", "possible_SOS": "True"}
    assert classify_sos_status(row_str) == SOS_STATUS_LABEL

def test_classify_sos_status_no_event():
    row_none = {"most_recent_event_type": None, "possible_SOS": False}
    assert classify_sos_status(row_none) == NO_EVENT_LABEL
    
    row_empty = {"most_recent_event_type": "", "possible_SOS": False}
    assert classify_sos_status(row_empty) == NO_EVENT_LABEL
    
    row_nan = {"most_recent_event_type": float("nan"), "possible_SOS": False}
    assert classify_sos_status(row_nan) == NO_EVENT_LABEL

def test_add_sos_status_column():
    data = [
        {"symbol": "TICKER1", "most_recent_event_type": "SOS", "possible_SOS": True, "vsa_volume_ratio": 2.5, "composite_score": 70},
        {"symbol": "TICKER2", "most_recent_event_type": "Spring", "possible_SOS": False, "vsa_volume_ratio": 1.2, "composite_score": 85},
        {"symbol": "TICKER3", "most_recent_event_type": None, "possible_SOS": False, "vsa_volume_ratio": 0.8, "composite_score": 60}
    ]
    df = pd.DataFrame(data)
    df_res = add_sos_status_column(df)
    
    assert "sos_status" in df_res.columns
    assert df_res.iloc[0]["sos_status"] == SOS_STATUS_LABEL
    assert df_res.iloc[1]["sos_status"] == OTHER_EVENT_LABEL
    assert df_res.iloc[2]["sos_status"] == NO_EVENT_LABEL

def test_prepare_sos_display_df_default_sorting():
    data = [
        {"symbol": "TICKER1", "most_recent_event_type": "SOS", "possible_SOS": True, "vsa_volume_ratio": 1.5, "composite_score": 60},
        {"symbol": "TICKER2", "most_recent_event_type": "Spring", "possible_SOS": False, "vsa_volume_ratio": 2.5, "composite_score": 90},
        {"symbol": "TICKER3", "most_recent_event_type": "None", "possible_SOS": False, "vsa_volume_ratio": 0.8, "composite_score": 75}
    ]
    df = pd.DataFrame(data)
    df_res, is_sos_active = prepare_sos_display_df(df, sos_only=False, event_filter="All Events")
    
    assert is_sos_active is False
    assert len(df_res) == 3
    # Default sort by composite_score desc: TICKER2 (90) -> TICKER3 (75) -> TICKER1 (60)
    assert df_res.iloc[0]["symbol"] == "TICKER2"
    assert df_res.iloc[1]["symbol"] == "TICKER3"
    assert df_res.iloc[2]["symbol"] == "TICKER1"

def test_prepare_sos_display_df_sos_only_active():
    data = [
        {"symbol": "TICKER1", "most_recent_event_type": "SOS", "possible_SOS": True, "vsa_volume_ratio": 1.8, "composite_score": 60},
        {"symbol": "TICKER2", "most_recent_event_type": "Spring", "possible_SOS": False, "vsa_volume_ratio": 2.5, "composite_score": 90},
        {"symbol": "TICKER3", "most_recent_event_type": "SOS", "possible_SOS": True, "vsa_volume_ratio": 3.2, "composite_score": 50}
    ]
    df = pd.DataFrame(data)
    df_res, is_sos_active = prepare_sos_display_df(df, sos_only=True, event_filter="All Events")
    
    assert is_sos_active is True
    assert len(df_res) == 2
    # Sorted by vsa_volume_ratio desc: TICKER3 (3.2) -> TICKER1 (1.8)
    assert df_res.iloc[0]["symbol"] == "TICKER3"
    assert df_res.iloc[1]["symbol"] == "TICKER1"

def test_prepare_sos_display_df_event_filter_sos():
    data = [
        {"symbol": "TICKER1", "most_recent_event_type": "SOS", "possible_SOS": True, "vsa_volume_ratio": 1.5, "composite_score": 60},
        {"symbol": "TICKER2", "most_recent_event_type": "SOS", "possible_SOS": True, "vsa_volume_ratio": 4.1, "composite_score": 55}
    ]
    df = pd.DataFrame(data)
    df_res, is_sos_active = prepare_sos_display_df(df, sos_only=False, event_filter="SOS")
    
    assert is_sos_active is True
    assert df_res.iloc[0]["symbol"] == "TICKER2"
    assert df_res.iloc[1]["symbol"] == "TICKER1"
