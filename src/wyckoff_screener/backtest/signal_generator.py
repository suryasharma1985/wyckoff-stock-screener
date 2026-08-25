"""Historical Point-in-Time Signal Generation Engine for Google Sheets Backtesting.

Guiding Principle (AGENTS.md & Phase 16):
1. Strict Point-in-Time Execution:
   For historical signal date D, the signal is generated using ONLY OHLCV data on or before D (df[df['Date'] <= D]).
   No future data is ever visible during signal calculation.
2. Complete Separation of Signal and Future Performance:
   Signal export records "what the screener knew on date D".
   Future returns (+5d, +10d, +20d, +40d, +60d, MFE, MAE) are calculated downstream in Google Sheets.
3. Survivorship Bias Disclosure:
   Flagged explicitly as "Survivorship-biased historical research" when using current universe snapshots.
4. Entry Model:
   Default: "next_trading_day_open" (Signal on Date D close -> Entry on Date D+1 open).
"""

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any, Final, Optional, Sequence
import numpy as np
import pandas as pd

from wyckoff_screener.data_loader import validate_ohlcv_dataframe
from wyckoff_screener.indicators.vsa_metrics import (
    NO_DEMAND_SPREAD_MAX,
    NO_DEMAND_VOL_MAX,
    NO_SUPPLY_SPREAD_MAX,
    NO_SUPPLY_VOL_MAX,
    STOPPING_SPREAD_RATIO_MAX,
    STOPPING_VOL_RATIO_MIN,
    close_position,
    spread_ratio,
    volume_ratio,
)
from wyckoff_screener.research.models import CandidateCategory
from wyckoff_screener.scanning.broad_filter import evaluate_broad_setup
from wyckoff_screener.scoring.setup_scorer import score_setup


DEFAULT_MIN_BARS: Final[int] = 60
DEFAULT_MIN_TURNOVER_CR: Final[float] = 1.0
DEFAULT_HIGH_PRIORITY_THRESH: Final[float] = 60.0
DEFAULT_QUALIFIED_THRESH: Final[float] = 40.0
DEFAULT_WATCHLIST_THRESH: Final[float] = 30.0
DEFAULT_ENTRY_MODEL: Final[str] = "next_trading_day_open"
DEFAULT_SURVIVORSHIP_BIAS_STATUS: Final[str] = (
    "Survivorship-biased historical research: dataset uses current constituent snapshot"
)


def evaluate_point_in_time_signal(
    df: pd.DataFrame,
    symbol: str,
    as_of_date: str,
    yfinance_ticker: Optional[str] = None,
    company_name: Optional[str] = None,
    exchange: str = "NSE",
    security_series: str = "EQ",
    min_bars: int = DEFAULT_MIN_BARS,
    min_avg_turnover_cr: float = DEFAULT_MIN_TURNOVER_CR,
    high_priority_score_threshold: float = DEFAULT_HIGH_PRIORITY_THRESH,
    qualified_score_threshold: float = DEFAULT_QUALIFIED_THRESH,
    watchlist_score_threshold: float = DEFAULT_WATCHLIST_THRESH,
    backtest_run_id: str = "historical_export_default",
) -> Optional[dict[str, Any]]:
    """Evaluate a single stock strictly point-in-time as of a historical date D.

    Args:
        df: Full historical DataFrame (will be sliced strictly to Date <= as_of_date).
        symbol: Ticker symbol (e.g. 'RELIANCE').
        as_of_date: Target historical signal date (YYYY-MM-DD).
        yfinance_ticker: Yahoo Finance ticker (e.g. 'RELIANCE.NS').
        company_name: Company name.
        exchange: Exchange name (default 'NSE').
        security_series: Series name (default 'EQ').
        min_bars: Minimum bars required up to as_of_date.
        min_avg_turnover_cr: Liquidity filter in INR Crores.
        high_priority_score_threshold: Score threshold for high priority candidate.
        qualified_score_threshold: Score threshold for qualified candidate.
        watchlist_score_threshold: Score threshold for watchlist setup.
        backtest_run_id: Identifier for backtest provenance.

    Returns:
        Optional[dict[str, Any]]: Complete point-in-time signal dictionary, or None if insufficient bars.
    """
    yf_ticker = yfinance_ticker or (f"{symbol}.NS" if not symbol.endswith(".NS") else symbol)
    comp_name = company_name or symbol

    # 1. Strict Point-in-Time Slice: df.iloc where Date <= as_of_date
    wdf = df.copy()
    if "Date" not in wdf.columns:
        raise KeyError("Required column 'Date' not found in DataFrame.")

    wdf["Date"] = pd.to_datetime(wdf["Date"])
    target_dt = pd.to_datetime(as_of_date)
    pit_df = wdf[wdf["Date"] <= target_dt].sort_values(by="Date").reset_index(drop=True)

    if len(pit_df) < min_bars:
        return None

    # Validate point-in-time slice
    v_df = validate_ohlcv_dataframe(pit_df, reject_duplicates=True)
    data_bars = len(v_df)
    actual_signal_date = str(v_df["Date"].iloc[-1])[:10]

    # 2. Schematic Event Detection (Computed once per point-in-time slice)
    from wyckoff_screener.wyckoff.schematic_events import detect_all_schematic_events
    events = detect_all_schematic_events(v_df)

    # 3. Broad Mechanical Filtering
    broad_res = evaluate_broad_setup(
        v_df,
        symbol=yf_ticker,
        company_name=comp_name,
        min_avg_turnover_cr=min_avg_turnover_cr,
        events=events,
    )
    is_mech_qual = broad_res.is_mechanically_qualified
    filter_flags = broad_res.filter_results
    filter_values = broad_res.filter_values

    # 4. VSA Bar Physics on Signal Bar
    vr_s = volume_ratio(v_df)
    sr_s = spread_ratio(v_df)
    cp_s = close_position(v_df)
    vol_r = float(vr_s.iloc[-1]) if not vr_s.empty and pd.notna(vr_s.iloc[-1]) else 1.0
    spd_r = float(sr_s.iloc[-1]) if not sr_s.empty and pd.notna(sr_s.iloc[-1]) else 1.0
    cls_p = float(cp_s.iloc[-1]) if not cp_s.empty and pd.notna(cp_s.iloc[-1]) else 0.5

    is_up_bar = bool(v_df["Close"].iloc[-1] > v_df["Close"].iloc[-2]) if len(v_df) >= 2 else False
    is_down_bar = bool(v_df["Close"].iloc[-1] < v_df["Close"].iloc[-2]) if len(v_df) >= 2 else False

    stop_v = bool(vol_r >= STOPPING_VOL_RATIO_MIN and spd_r <= STOPPING_SPREAD_RATIO_MAX)
    no_d = bool(is_up_bar and spd_r <= NO_DEMAND_SPREAD_MAX and vol_r <= NO_DEMAND_VOL_MAX)
    no_s = bool(is_down_bar and spd_r <= NO_SUPPLY_SPREAD_MAX and vol_r <= NO_SUPPLY_VOL_MAX)
    ev_r = bool((vol_r >= 1.5 and spd_r < 0.6) or (vol_r >= 1.5 and is_up_bar and cls_p < 0.3) or (vol_r >= 1.5 and is_down_bar and cls_p > 0.7))

    # 5. Point-in-Time Setup Scoring & Point & Figure Price Objective
    scored = score_setup(v_df, symbol=yf_ticker, events=events)
    composite_score = float(scored.composite_score)
    is_disq = scored.is_disqualified
    disq_flags = scored.disqualifying_flags


    # 5. Wyckoff Schematic Events
    summary_ev = broad_res.candidate_event_summary
    most_recent_ev = summary_ev.get("candidate_event_detected")
    most_recent_dt = summary_ev.get("event_date")
    possible_lps = bool(summary_ev.get("is_possible_LPS", False))
    possible_sos = bool(summary_ev.get("is_possible_SOS", False))
    possible_spring = bool(summary_ev.get("is_possible_Spring", False))
    is_utad = bool(summary_ev.get("is_UTAD_warning", False))
    total_events = sum(len(ev_list) for ev_list in scored.detected_events.values())
    numeric_ev = str(summary_ev.get("numeric_evidence", ""))

    # 6. Candidate Categorization
    has_bullish_event = bool(possible_lps or possible_sos or possible_spring or (most_recent_ev in ("Spring", "LPS", "SOS", "ST")))

    if is_disq:
        category = CandidateCategory.DISQUALIFIED.value
    elif is_mech_qual and composite_score >= high_priority_score_threshold and has_bullish_event:
        category = CandidateCategory.HIGH_PRIORITY_CANDIDATE.value
    elif is_mech_qual and composite_score >= qualified_score_threshold:
        category = CandidateCategory.QUALIFIED_CANDIDATE.value
    elif composite_score >= watchlist_score_threshold or has_bullish_event:
        category = CandidateCategory.WATCHLIST.value
    else:
        category = CandidateCategory.NO_SETUP.value

    # 7. Point & Figure Fraser Metrics
    pf_obj = scored.pf_price_objective
    pf_target = float(pf_obj.price_objective) if pf_obj else None
    pf_cols = int(pf_obj.num_columns) if pf_obj else None
    pf_stale = bool(pf_obj.stale_anchor) if pf_obj else False
    sig_close = float(v_df["Close"].iloc[-1])
    pf_upside = round(((pf_target - sig_close) / sig_close) * 100.0, 1) if pf_target and sig_close > 0 else None

    # Signal Bar Prices
    sig_open = float(v_df["Open"].iloc[-1])
    sig_high = float(v_df["High"].iloc[-1])
    sig_low = float(v_df["Low"].iloc[-1])
    sig_vol = int(v_df["Volume"].iloc[-1])
    data_start = str(v_df["Date"].iloc[0])[:10]

    return {
        # 1. Identification
        "signal_date": actual_signal_date,
        "symbol": symbol,
        "yfinance_ticker": yf_ticker,
        "company_name": comp_name,
        "exchange": exchange,
        "security_series": security_series,
        # 2. Signal & Classification
        "composite_score": round(composite_score, 1),
        "candidate_category": category,
        "is_high_priority": category == CandidateCategory.HIGH_PRIORITY_CANDIDATE.value,
        "is_qualified": category == CandidateCategory.QUALIFIED_CANDIDATE.value,
        "is_candidate": category in (CandidateCategory.HIGH_PRIORITY_CANDIDATE.value, CandidateCategory.QUALIFIED_CANDIDATE.value),
        "is_watchlist": category == CandidateCategory.WATCHLIST.value,
        "is_disqualified": is_disq,
        "disqualifying_flags": "; ".join(disq_flags) if disq_flags else "None",
        "is_mechanically_qualified": is_mech_qual,
        # 3. Wyckoff Schematic Events
        "most_recent_event_type": most_recent_ev or "None",
        "most_recent_event_date": most_recent_dt or "None",
        "possible_LPS": possible_lps,
        "possible_SOS": possible_sos,
        "possible_Spring": possible_spring,
        "is_UTAD_warning": is_utad,
        "total_events_detected": total_events,
        "numeric_evidence": numeric_ev,
        # 4. VSA Physics
        "vsa_volume_ratio": round(vol_r, 2),
        "vsa_spread_ratio": round(spd_r, 2),
        "vsa_close_position": round(cls_p, 2),
        "is_stopping_volume": stop_v,
        "is_no_demand": no_d,
        "is_no_supply": no_s,
        "is_effort_vs_result": ev_r,
        # 5. Point & Figure Bruce Fraser Metrics
        "pf_target_price": round(pf_target, 2) if pf_target is not None else None,
        "pf_upside_pct": pf_upside,
        "pf_count_columns": pf_cols,
        "pf_is_stale_anchor": pf_stale,
        # 6. Price & Bar Context on Signal Date
        "signal_open": sig_open,
        "signal_high": sig_high,
        "signal_low": sig_low,
        "signal_close": sig_close,
        "signal_volume": sig_vol,
        "data_bars_available": data_bars,
        "data_start_date": data_start,
        "data_end_date": actual_signal_date,
        # 7. Mechanical Indicator Context
        "dma_50": filter_values.get("dma_50"),
        "dma_100": filter_values.get("dma_100"),
        "rsi_14": filter_values.get("rsi_14"),
        "atr_contraction_ratio": filter_values.get("atr_contraction_ratio"),
        "bb_width_20": filter_values.get("bb_width_20"),
        # 8. Provenance & Research Governance
        "entry_model": DEFAULT_ENTRY_MODEL,
        "survivorship_bias_status": DEFAULT_SURVIVORSHIP_BIAS_STATUS,
        "backtest_run_id": backtest_run_id,
    }


def determine_historical_signal_dates(
    all_trading_dates: Sequence[pd.Timestamp | str],
    start_date: str,
    end_date: str,
    frequency: str = "monthly",
) -> list[str]:
    """Determine clean historical screening dates aligned to actual trading days.

    Args:
        all_trading_dates: Sequence of available market trading dates.
        start_date: Start date string (YYYY-MM-DD).
        end_date: End date string (YYYY-MM-DD).
        frequency: 'monthly' (last trading day of month), 'weekly' (every 5 trading days / Friday), or 'daily'.

    Returns:
        list[str]: Sorted list of YYYY-MM-DD date strings.
    """
    ts_list = sorted(pd.to_datetime(all_trading_dates).unique())
    start_ts = pd.to_datetime(start_date)
    end_ts = pd.to_datetime(end_date)

    in_range = [d for d in ts_list if start_ts <= d <= end_ts]
    if not in_range:
        return []

    if frequency.lower() == "daily":
        return [d.strftime("%Y-%m-%d") for d in in_range]

    if frequency.lower() == "weekly":
        # Group by ISO year & week, take last available trading day of the week
        df_dates = pd.DataFrame({"Date": in_range})
        df_dates["YearWeek"] = df_dates["Date"].dt.strftime("%Y-%U")
        weekly_last = df_dates.groupby("YearWeek")["Date"].max()
        return [d.strftime("%Y-%m-%d") for d in sorted(weekly_last)]

    # Default 'monthly': Last available trading day in each calendar month
    df_dates = pd.DataFrame({"Date": in_range})
    df_dates["YearMonth"] = df_dates["Date"].dt.strftime("%Y-%m")
    monthly_last = df_dates.groupby("YearMonth")["Date"].max()
    return [d.strftime("%Y-%m-%d") for d in sorted(monthly_last)]


def generate_backtest_dataset(
    securities: list[tuple[str, pd.DataFrame, Optional[str], Optional[str]]],
    start_date: str,
    end_date: str,
    frequency: str = "monthly",
    min_bars: int = DEFAULT_MIN_BARS,
    min_avg_turnover_cr: float = DEFAULT_MIN_TURNOVER_CR,
    backtest_run_id: Optional[str] = None,
    universe_source: str = "custom_universe",
) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, Any]]:
    """Generate the complete historical signal dataset, historical price panel, and audit manifest.

    Args:
        securities: List of (symbol, full_ohlcv_df, yf_ticker, company_name) tuples.
        start_date: Backtest signal start date (YYYY-MM-DD).
        end_date: Backtest signal end date (YYYY-MM-DD).
        frequency: 'monthly', 'weekly', or 'daily'.
        min_bars: Minimum historical bars required before evaluating a checkpoint.
        min_avg_turnover_cr: Turnover gate.
        backtest_run_id: Optional run ID.
        universe_source: Descriptive universe source string.

    Returns:
        tuple[signals_df, prices_df, manifest_dict]
    """
    run_id = backtest_run_id or f"backtest_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"

    # 1. Collect all trading dates across all securities
    all_dates_set = set()
    for _, df, _, _ in securities:
        if not df.empty and "Date" in df.columns:
            all_dates_set.update(pd.to_datetime(df["Date"]))

    signal_dates = determine_historical_signal_dates(
        list(all_dates_set), start_date=start_date, end_date=end_date, frequency=frequency
    )

    # 2. Iterate through each historical signal date strictly point-in-time
    signals_records: list[dict[str, Any]] = []

    for sig_date in signal_dates:
        for sym, df, yf_t, comp_n in securities:
            res = evaluate_point_in_time_signal(
                df=df,
                symbol=sym,
                as_of_date=sig_date,
                yfinance_ticker=yf_t,
                company_name=comp_n,
                min_bars=min_bars,
                min_avg_turnover_cr=min_avg_turnover_cr,
                backtest_run_id=run_id,
            )
            if res is not None:
                signals_records.append(res)

    signals_df = pd.DataFrame(signals_records)

    # 3. Construct Panel Price Dataset for Google Sheets (Date, Symbol, Trading_Day_Num, OHLCV)
    prices_records: list[dict[str, Any]] = []
    for sym, df, _, _ in securities:
        if df.empty:
            continue
        v_df = validate_ohlcv_dataframe(df)
        v_df = v_df.sort_values(by="Date").reset_index(drop=True)
        for idx, row in v_df.iterrows():
            prices_records.append({
                "Date": str(row["Date"])[:10],
                "Symbol": sym,
                "Trading_Day_Num": idx + 1,
                "Open": round(float(row["Open"]), 2),
                "High": round(float(row["High"]), 2),
                "Low": round(float(row["Low"]), 2),
                "Close": round(float(row["Close"]), 2),
                "Volume": int(row["Volume"]),
            })

    prices_df = pd.DataFrame(prices_records)

    # 4. Construct Machine-Readable Audit Manifest
    total_signals = len(signals_df)
    hp_count = int((signals_df["is_high_priority"] == True).sum()) if not signals_df.empty else 0
    q_count = int((signals_df["is_qualified"] == True).sum()) if not signals_df.empty else 0
    w_count = int((signals_df["is_watchlist"] == True).sum()) if not signals_df.empty else 0
    disq_count = int((signals_df["is_disqualified"] == True).sum()) if not signals_df.empty else 0

    manifest = {
        "backtest_run_id": run_id,
        "generated_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
        "schema_version": "1.0",
        "start_date": start_date,
        "end_date": end_date,
        "frequency": frequency,
        "universe_source": universe_source,
        "survivorship_bias_disclosure": DEFAULT_SURVIVORSHIP_BIAS_STATUS,
        "entry_model": DEFAULT_ENTRY_MODEL,
        "forward_horizons_bars": [5, 10, 20, 40, 60],
        "total_symbols_evaluated": len(securities),
        "total_historical_dates_evaluated": len(signal_dates),
        "evaluated_signal_dates": signal_dates,
        "total_signals_generated": total_signals,
        "high_priority_signals_count": hp_count,
        "qualified_signals_count": q_count,
        "watchlist_signals_count": w_count,
        "disqualified_signals_count": disq_count,
        "configuration": {
            "min_bars": min_bars,
            "min_avg_turnover_cr": min_avg_turnover_cr,
            "high_priority_score_threshold": DEFAULT_HIGH_PRIORITY_THRESH,
            "qualified_score_threshold": DEFAULT_QUALIFIED_THRESH,
            "watchlist_score_threshold": DEFAULT_WATCHLIST_THRESH,
        },
    }

    return signals_df, prices_df, manifest


def export_backtest_dataset(
    signals_df: pd.DataFrame,
    prices_df: pd.DataFrame,
    manifest: dict[str, Any],
    export_dir: Path | str,
) -> tuple[Path, Path, Path]:
    """Export historical signals, panel prices, and manifest to disk.

    Args:
        signals_df: Signals DataFrame.
        prices_df: Historical prices panel DataFrame.
        manifest: Audit manifest dict.
        export_dir: Directory path.

    Returns:
        tuple[signals_path, prices_path, manifest_path]
    """
    out_dir = Path(export_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    sig_path = out_dir / "historical_signals.csv"
    prc_path = out_dir / "historical_prices.csv"
    man_path = out_dir / "backtest_manifest.json"

    signals_df.to_csv(sig_path, index=False)
    prices_df.to_csv(prc_path, index=False)

    with open(man_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    return sig_path, prc_path, man_path
