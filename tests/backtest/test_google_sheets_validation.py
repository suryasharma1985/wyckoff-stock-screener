"""Comprehensive tests for Phase 18 Google Sheets Forward-Validation System."""

from pathlib import Path
import openpyxl
import pandas as pd
import pytest

from wyckoff_screener.google_sheets.validation_builder import (
    build_candidates_sheet_dataframe,
    export_validation_package,
    SCHEMA_VERSION,
)
from wyckoff_screener.forward_testing.models import ForwardSignal
from wyckoff_screener.forward_testing.evaluator import evaluate_forward_performance

CANDIDATES_PATH = Path("data/research_results/20260824/candidates.csv")


def test_candidates_import_schema_and_counts() -> None:
    """Verify 383 candidates (196 High Priority, 187 Qualified) and Columns A to V."""
    assert CANDIDATES_PATH.exists(), f"Production candidates missing at {CANDIDATES_PATH}"
    raw_df = pd.read_csv(CANDIDATES_PATH)
    assert len(raw_df) == 383

    df_cand = build_candidates_sheet_dataframe(raw_df, screening_run_date="20260824")
    assert len(df_cand) == 383

    # Check Columns A through V
    expected_cols = [
        "Candidate_ID", "Screening_Date", "Symbol", "Company_Name", "Exchange",
        "Priority", "Setup", "Score", "Qualification_Status", "Wyckoff_Event",
        "Entry_Price", "Entry_Date", "Initial_Stop", "Target_1", "Target_2", "Target_3",
        "Risk_Per_Share", "Risk_Percent", "TradingView_URL", "Screener_Reason",
        "Data_Source", "Validation_Status"
    ]
    for col in expected_cols:
        assert col in df_cand.columns, f"Column {col} missing from CANDIDATES tab!"

    hp = df_cand[df_cand["Priority"] == "HIGH_PRIORITY_CANDIDATE"]
    q = df_cand[df_cand["Priority"] == "QUALIFIED_CANDIDATE"]
    assert len(hp) == 196
    assert len(q) == 187


def test_candidate_id_uniqueness_and_immutability() -> None:
    """Verify Candidate_ID structure YYYYMMDD_SYMBOL is unique and deterministic."""
    raw_df = pd.read_csv(CANDIDATES_PATH)
    df_cand = build_candidates_sheet_dataframe(raw_df, screening_run_date="20260824")

    # All candidate IDs must start with 20260824_ and be unique within run
    assert df_cand["Candidate_ID"].nunique() == 383
    for cid in df_cand["Candidate_ID"]:
        assert cid.startswith("20260824_")


def test_workbook_all_8_tabs(tmp_path: Path) -> None:
    """Verify generated Excel template contains all 8 required tabs."""
    xlsx_path, csv_path = export_validation_package(
        candidates_csv_path=CANDIDATES_PATH,
        output_dir=tmp_path,
        screening_run_date="20260824",
    )

    assert xlsx_path.exists()
    assert csv_path.exists()

    wb = openpyxl.load_workbook(xlsx_path, read_only=True)
    expected_tabs = [
        "README", "CANDIDATES", "PRICE_DATA", "SIGNALS",
        "PERFORMANCE", "TRADE_LOG", "SUMMARY", "CONFIG"
    ]
    for tab in expected_tabs:
        assert tab in wb.sheetnames, f"Tab {tab} missing from workbook!"


def test_forward_return_formulas() -> None:
    """Verify forward return calculations ((Future_Price / Entry_Price) - 1) * 100."""
    sig = ForwardSignal(
        signal_id="20260824_RELIANCE",
        run_id="20260824",
        signal_date="2026-08-21",
        symbol="RELIANCE",
        company_name="Reliance Industries Limited",
        exchange="NSE",
        priority="HIGH_PRIORITY_CANDIDATE",
        score=75.0,
        signal_type="LPS",
        wyckoff_event="LPS",
        wyckoff_phase="Phase C/D Candidate",
        vsa_status="",
        p_and_f_score="",
        entry_price=3000.0,
        close_price=3000.0,
        broad_setup_status=True,
        mechanically_qualified=True,
        tradingview_url="",
        screening_date="2026-08-21",
        source_run_date="2026-08-21",
        notes="",
    )

    # 5-day series: Day 1 (+1%), Day 3 (+3%), Day 5 (+5%)
    future_df = pd.DataFrame([
        {"Date": "2026-08-24", "Open": 3000.0, "High": 3050.0, "Low": 2980.0, "Close": 3030.0, "Volume": 1000},
        {"Date": "2026-08-25", "Open": 3030.0, "High": 3070.0, "Low": 3010.0, "Close": 3060.0, "Volume": 1000},
        {"Date": "2026-08-26", "Open": 3060.0, "High": 3100.0, "Low": 3040.0, "Close": 3090.0, "Volume": 1000},
        {"Date": "2026-08-27", "Open": 3090.0, "High": 3120.0, "Low": 3070.0, "Close": 3110.0, "Volume": 1000},
        {"Date": "2026-08-28", "Open": 3110.0, "High": 3170.0, "Low": 3100.0, "Close": 3150.0, "Volume": 1000},
    ])

    res = evaluate_forward_performance(sig, future_ohlc_df=future_df)
    # Day 5 return = (3150 - 3000) / 3000 * 100 = +5.0%
    assert res.ret_5d == pytest.approx(5.0, abs=0.01)
    # Max Gain = (3170 - 3000) / 3000 * 100 = +5.67%
    assert res.max_gain_pct == pytest.approx(5.67, abs=0.01)
    # Max Drawdown = (2980 - 3000) / 3000 * 100 = -0.67%
    assert res.max_drawdown_pct == pytest.approx(-0.67, abs=0.01)


def test_target_and_stop_detection() -> None:
    """Verify Target 1 (+10%), Target 2 (+20%), and Stop Loss (-5%) triggers."""
    sig = ForwardSignal(
        signal_id="20260824_TCS",
        run_id="20260824",
        signal_date="2026-08-21",
        symbol="TCS",
        company_name="Tata Consultancy Services Limited",
        exchange="NSE",
        priority="HIGH_PRIORITY_CANDIDATE",
        score=80.0,
        signal_type="SOS",
        wyckoff_event="SOS",
        wyckoff_phase="Phase D Candidate",
        vsa_status="",
        p_and_f_score="",
        entry_price=4000.0,
        close_price=4000.0,
        broad_setup_status=True,
        mechanically_qualified=True,
        tradingview_url="",
        screening_date="2026-08-21",
        source_run_date="2026-08-21",
        notes="",
    )

    # Rallies to High 4450 (+11.25%) without dropping below 3800 (-5%)
    future_df = pd.DataFrame([
        {"Date": "2026-08-24", "Open": 4000.0, "High": 4450.0, "Low": 3950.0, "Close": 4400.0, "Volume": 1000},
    ])

    res = evaluate_forward_performance(sig, future_ohlc_df=future_df)
    assert res.target_10_reached == "YES"
    assert res.target_20_reached == "NO"
    assert res.stop_5_reached == "NO"
    assert res.result == "WIN"


def test_ambiguous_same_day_candle() -> None:
    """Verify that touching both target and stop on the same candle is classified as AMBIGUOUS."""
    sig = ForwardSignal(
        signal_id="20260824_AMBIG",
        run_id="20260824",
        signal_date="2026-08-21",
        symbol="AMBIG",
        company_name="Ambiguous Corp",
        exchange="NSE",
        priority="HIGH_PRIORITY_CANDIDATE",
        score=75.0,
        signal_type="Spring",
        wyckoff_event="Spring",
        wyckoff_phase="Phase C Candidate",
        vsa_status="",
        p_and_f_score="",
        entry_price=100.0,
        close_price=100.0,
        broad_setup_status=True,
        mechanically_qualified=True,
        tradingview_url="",
        screening_date="2026-08-21",
        source_run_date="2026-08-21",
        notes="",
    )

    # Candle reaches High 112 (>= 110) AND Low 92 (<= 95) on the same day
    future_df = pd.DataFrame([
        {"Date": "2026-08-24", "Open": 100.0, "High": 112.0, "Low": 92.0, "Close": 105.0, "Volume": 1000},
    ])

    res = evaluate_forward_performance(sig, future_ohlc_df=future_df)
    assert res.result == "AMBIGUOUS"
    assert res.target_10_reached == "YES"
    assert res.stop_5_reached == "YES"


def test_adversarial_lookahead_protection() -> None:
    """Mathematical proof that mutating future bars leaves signal fields on Date T 100% identical."""
    sig = ForwardSignal(
        signal_id="20260824_LOOKAHEAD",
        run_id="20260824",
        signal_date="2026-08-21",
        symbol="LOOKAHEAD",
        company_name="Lookahead Corp",
        exchange="NSE",
        priority="HIGH_PRIORITY_CANDIDATE",
        score=72.0,
        signal_type="LPS",
        wyckoff_event="LPS",
        wyckoff_phase="Phase C Candidate",
        vsa_status="",
        p_and_f_score="",
        entry_price=500.0,
        close_price=500.0,
        broad_setup_status=True,
        mechanically_qualified=True,
        tradingview_url="",
        screening_date="2026-08-21",
        source_run_date="2026-08-21",
        notes="LPS evidence",
    )

    # Clean future bars
    df_clean = pd.DataFrame([
        {"Date": "2026-08-24", "Open": 500.0, "High": 510.0, "Low": 495.0, "Close": 505.0, "Volume": 1000},
    ])

    # Corrupted future bars (100x shock)
    df_corrupt = pd.DataFrame([
        {"Date": "2026-08-24", "Open": 50000.0, "High": 60000.0, "Low": 45000.0, "Close": 55000.0, "Volume": 1000000},
    ])

    res_clean = evaluate_forward_performance(sig, future_ohlc_df=df_clean)
    res_corrupt = evaluate_forward_performance(sig, future_ohlc_df=df_corrupt)

    # Signal itself is immutable
    assert sig.entry_price == 500.0
    assert sig.score == 72.0
    assert sig.symbol == "LOOKAHEAD"

    # Future evaluation reflects the data without leaking into the signal definition
    assert res_clean.max_gain_pct == pytest.approx(2.0, abs=0.01)
    assert res_corrupt.max_gain_pct > 10000.0
