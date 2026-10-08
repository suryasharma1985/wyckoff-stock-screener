"""
Display-only helper module for the Sign of Strength (SOS) Highlight View in the Streamlit dashboard.
Provides pure, testable classification and sorting logic with zero Streamlit or src/ dependencies.
"""

from typing import Any, Dict, List, Optional, Tuple
import pandas as pd
import numpy as np

SOS_STATUS_LABEL = "SOS (Research-Validated)"
OTHER_EVENT_LABEL = "Other Event"
NO_EVENT_LABEL = "None"

def classify_sos_status(row: Any) -> str:
    """
    Classifies a row's Wyckoff SOS status.
    Precedence:
    1. If most_recent_event_type == 'SOS' or possible_SOS is True -> 'SOS (Research-Validated)'
    2. If most_recent_event_type is non-empty/not null and != 'SOS' -> 'Other Event'
    3. Otherwise -> 'None'
    """
    if isinstance(row, dict):
        event_type = row.get("most_recent_event_type")
        possible_sos = row.get("possible_SOS", False)
    elif hasattr(row, "get"):
        event_type = row.get("most_recent_event_type")
        possible_sos = row.get("possible_SOS", False)
    elif isinstance(row, pd.Series):
        event_type = row.get("most_recent_event_type") if "most_recent_event_type" in row.index else None
        possible_sos = row.get("possible_SOS") if "possible_SOS" in row.index else False
    else:
        return NO_EVENT_LABEL

    # Check for possible_SOS boolean truthiness (handling string representations like 'True' if any)
    is_possible_sos = False
    if isinstance(possible_sos, (bool, np.bool_)):
        is_possible_sos = bool(possible_sos)
    elif isinstance(possible_sos, str):
        is_possible_sos = possible_sos.strip().lower() == "true"

    # Event type normalization
    ev_str = str(event_type).strip() if pd.notna(event_type) and event_type is not None else ""

    if ev_str == "SOS" or is_possible_sos:
        return SOS_STATUS_LABEL
    elif ev_str and ev_str not in ("None", "nan", ""):
        return OTHER_EVENT_LABEL
    else:
        return NO_EVENT_LABEL

def add_sos_status_column(df: pd.DataFrame) -> pd.DataFrame:
    """
    Adds the 'sos_status' column to a DataFrame using classify_sos_status.
    """
    if df.empty:
        df_out = df.copy()
        df_out["sos_status"] = pd.Series(dtype="object")
        return df_out
        
    df_out = df.copy()
    df_out["sos_status"] = df_out.apply(classify_sos_status, axis=1)
    return df_out

def prepare_sos_display_df(
    df: pd.DataFrame,
    sos_only: bool = False,
    event_filter: str = "All Events"
) -> Tuple[pd.DataFrame, bool]:
    """
    Prepares DataFrame for rendering:
    - Applies SOS status column if not already present.
    - If sos_only is True, filters to SOS rows.
    - If sos_only is True OR event_filter == 'SOS', sorts by vsa_volume_ratio descending.
    - Otherwise, sorts by composite_score descending (default behavior).
    Returns (processed_df, is_sos_active).
    """
    df_proc = add_sos_status_column(df)
    
    is_sos_active = bool(sos_only or (event_filter == "SOS"))
    
    if sos_only:
        df_proc = df_proc[df_proc["sos_status"] == SOS_STATUS_LABEL].copy()
        
    if is_sos_active:
        # Sort by vsa_volume_ratio descending if column exists
        if "vsa_volume_ratio" in df_proc.columns:
            df_proc = df_proc.sort_values("vsa_volume_ratio", ascending=False)
        elif "composite_score" in df_proc.columns:
            df_proc = df_proc.sort_values("composite_score", ascending=False)
    else:
        # Default behavior: sort by composite_score descending
        if "composite_score" in df_proc.columns:
            df_proc = df_proc.sort_values("composite_score", ascending=False)
            
    return df_proc, is_sos_active
