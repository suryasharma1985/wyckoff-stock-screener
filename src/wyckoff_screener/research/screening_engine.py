"""Broad NSE EQ Research Screening Engine orchestrating frozen analytical layers over Phase 9B datasets."""

from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
import json
import os
from pathlib import Path
from typing import Any, Final, Optional, Sequence, Union
import numpy as np
import pandas as pd

from wyckoff_screener.charting.tradingview_links import generate_tradingview_links
from wyckoff_screener.data_loader import DataValidationError, validate_ohlcv_dataframe
from wyckoff_screener.indicators.vsa_metrics import (
    NO_DEMAND_SPREAD_MAX,
    NO_DEMAND_VOL_MAX,
    NO_SUPPLY_SPREAD_MAX,
    NO_SUPPLY_VOL_MAX,
    STOPPING_SPREAD_RATIO_MAX,
    STOPPING_VOL_RATIO_MIN,
    classify_close_position,
    classify_spread_ratio,
    classify_volume_ratio,
    close_position,
    spread_ratio,
    volume_ratio,
)
from wyckoff_screener.research.explanation import generate_candidate_explanation
from wyckoff_screener.research.models import (
    CandidateCategory,
    ResearchCandidateResult,
    ResearchScreeningManifest,
    ResearchScreeningResult,
)
from wyckoff_screener.scanning.broad_filter import (
    DEFAULT_MIN_AVG_TURNOVER_CR,
    evaluate_broad_setup,
)
from wyckoff_screener.scoring.setup_scorer import score_setup
from wyckoff_screener.wyckoff.schematic_events import detect_all_schematic_events

DEFAULT_RESULTS_BASE_DIR: Final[str] = "data/research_results"
DEFAULT_HIGH_PRIORITY_THRESHOLD: Final[float] = 60.0
DEFAULT_QUALIFIED_THRESHOLD: Final[float] = 40.0
DEFAULT_WATCHLIST_THRESHOLD: Final[float] = 30.0


def _evaluate_single_security(
    symbol: str,
    yf_ticker: str,
    company_name: str,
    csv_path: Path,
    dataset_snapshot_name: str,
    dataset_date_str: str,
    min_avg_turnover_cr: float,
    high_priority_score_threshold: float,
    qualified_score_threshold: float,
    watchlist_score_threshold: float,
) -> tuple[Optional[ResearchCandidateResult], Optional[dict[str, Any]], Optional[str]]:
    """Evaluate all frozen analytical layers for a single security.

    Returns:
        (result, failure_dict, tv_error_message)
    """
    stage = "DATA_LOAD"
    try:
        if not csv_path.exists():
            raise FileNotFoundError(f"Canonical data file not found: {csv_path}")

        raw_df = pd.read_csv(csv_path)
        stage = "VALIDATION"
        df = validate_ohlcv_dataframe(raw_df, reject_duplicates=True)
        data_bars = len(df)
        as_of_date = str(df["Date"].iloc[-1])[:10] if not df.empty else "N/A"

        # 1. Broad Mechanical Filtering
        stage = "BROAD_FILTER"
        broad_res = evaluate_broad_setup(
            df,
            symbol=yf_ticker,
            company_name=company_name,
            min_avg_turnover_cr=min_avg_turnover_cr,
        )
        is_mech_qual = broad_res.is_mechanically_qualified
        filter_flags = broad_res.filter_results
        filter_values = broad_res.filter_values

        # 2. VSA Bar Physics (Latest Bar)
        stage = "VSA"
        vr_s = volume_ratio(df)
        sr_s = spread_ratio(df)
        cp_s = close_position(df)
        vol_r = float(vr_s.iloc[-1]) if not vr_s.empty and pd.notna(vr_s.iloc[-1]) else 1.0
        spd_r = float(sr_s.iloc[-1]) if not sr_s.empty and pd.notna(sr_s.iloc[-1]) else 1.0
        cls_p = float(cp_s.iloc[-1]) if not cp_s.empty and pd.notna(cp_s.iloc[-1]) else 0.5

        is_up_bar = bool(df["Close"].iloc[-1] > df["Close"].iloc[-2]) if len(df) >= 2 else False
        is_down_bar = bool(df["Close"].iloc[-1] < df["Close"].iloc[-2]) if len(df) >= 2 else False

        stop_v = bool(vol_r >= STOPPING_VOL_RATIO_MIN and spd_r <= STOPPING_SPREAD_RATIO_MAX)
        no_d = bool(is_up_bar and spd_r <= NO_DEMAND_SPREAD_MAX and vol_r <= NO_DEMAND_VOL_MAX)
        no_s = bool(is_down_bar and spd_r <= NO_SUPPLY_SPREAD_MAX and vol_r <= NO_SUPPLY_VOL_MAX)
        ev_r = bool((vol_r >= 1.5 and spd_r < 0.6) or (vol_r >= 1.5 and is_up_bar and cls_p < 0.3) or (vol_r >= 1.5 and is_down_bar and cls_p > 0.7))

        # 3. Setup Scoring & Point & Figure Price Objective
        stage = "SCORING"
        scored = score_setup(df, symbol=yf_ticker)
        composite_score = float(scored.composite_score)
        score_breakdown = scored.score_breakdown
        is_disq = scored.is_disqualified
        disq_flags = scored.disqualifying_flags

        # 4. Wyckoff Schematic Events (Reused from ScoredSetup and BroadScreeningResult)
        stage = "WYCKOFF"
        events_dict = scored.detected_events
        summary_ev = broad_res.candidate_event_summary
        most_recent_ev = summary_ev.get("candidate_event_detected")
        most_recent_dt = summary_ev.get("event_date")
        possible_lps = bool(summary_ev.get("is_possible_LPS", False))
        possible_sos = bool(summary_ev.get("is_possible_SOS", False))
        possible_spring = bool(summary_ev.get("is_possible_Spring", False))
        is_utad = bool(summary_ev.get("is_UTAD_warning", False))
        total_events = sum(len(ev_list) for ev_list in events_dict.values())
        numeric_ev = str(summary_ev.get("numeric_evidence", ""))

        pf_obj = scored.pf_price_objective
        pf_target = float(pf_obj.price_objective) if pf_obj else None
        cur_close = float(df["Close"].iloc[-1]) if not df.empty else 0.0
        pf_upside = (
            float(((pf_obj.price_objective - cur_close) / cur_close) * 100.0)
            if (pf_obj and cur_close > 0)
            else None
        )
        pf_cols = int(pf_obj.num_columns) if pf_obj else None
        pf_stale = bool(pf_obj.stale_anchor) if pf_obj else False

        # 6. Candidate Categorization (Strict Precedence)
        stage = "CATEGORIZATION"
        has_bullish_event = possible_lps or possible_sos or possible_spring or (most_recent_ev is not None)
        if is_disq:
            category = CandidateCategory.DISQUALIFIED.value
        elif is_mech_qual and composite_score >= high_priority_score_threshold and (possible_lps or possible_sos or possible_spring):
            category = CandidateCategory.HIGH_PRIORITY_CANDIDATE.value
        elif is_mech_qual and composite_score >= qualified_score_threshold:
            category = CandidateCategory.QUALIFIED_CANDIDATE.value
        elif is_mech_qual or has_bullish_event or composite_score >= watchlist_score_threshold:
            category = CandidateCategory.WATCHLIST.value
        else:
            category = CandidateCategory.NO_SETUP.value

        # 7. Explanation Synthesis
        stage = "EXPLANATION"
        explanation = generate_candidate_explanation(
            symbol=symbol,
            is_mechanically_qualified=is_mech_qual,
            filter_flags=filter_flags,
            filter_values=filter_values,
            vsa_volume_ratio=vol_r,
            vsa_close_position=cls_p,
            is_stopping_volume=stop_v,
            is_no_supply=no_s,
            is_no_demand=no_d,
            most_recent_event_type=most_recent_ev,
            numeric_evidence=numeric_ev,
            pf_target_price=pf_target,
            pf_upside_pct=pf_upside,
            composite_score=composite_score,
            is_disqualified=is_disq,
            disqualifying_flags=disq_flags,
            candidate_category=category,
        )

        # 8. Optional TradingView Review Layer (Strictly Isolated)
        stage = "TRADINGVIEW"
        tv_daily = ""
        tv_weekly = ""
        tv_75m = ""
        tv_err = None
        try:
            tv_links = generate_tradingview_links(symbol, exchange="NSE")
            tv_daily = tv_links.daily_url
            tv_weekly = tv_links.weekly_url
            tv_75m = tv_links.intraday_75m_url
        except Exception as exc:
            tv_err = f"TradingView link generation error: {exc}"

        candidate_record = ResearchCandidateResult(
            symbol=symbol,
            yfinance_ticker=yf_ticker,
            company_name=company_name,
            as_of_date=as_of_date,
            data_bars=data_bars,
            dataset_snapshot_path=dataset_snapshot_name,
            dataset_date=dataset_date_str,
            candidate_category=category,
            is_research_eligible=True,
            is_mechanically_qualified=is_mech_qual,
            is_disqualified=is_disq,
            disqualifying_flags=disq_flags,
            composite_score=composite_score,
            score_breakdown=score_breakdown,
            peer_analysis_skipped=scored.peer_analysis_skipped,
            filter_flags=filter_flags,
            filter_values=filter_values,
            vsa_volume_ratio=vol_r,
            vsa_spread_ratio=spd_r,
            vsa_close_position=cls_p,
            is_stopping_volume=stop_v,
            is_no_demand=no_d,
            is_no_supply=no_s,
            is_effort_vs_result=ev_r,
            most_recent_event_type=most_recent_ev,
            most_recent_event_date=most_recent_dt,
            possible_LPS=possible_lps,
            possible_SOS=possible_sos,
            possible_Spring=possible_spring,
            is_UTAD_warning=is_utad,
            total_events_detected=total_events,
            numeric_evidence=numeric_ev,
            pf_target_price=pf_target,
            pf_upside_pct=pf_upside,
            pf_count_columns=pf_cols,
            pf_is_stale_anchor=pf_stale,
            explanation_summary=explanation,
            tradingview_daily_url=tv_daily,
            tradingview_weekly_url=tv_weekly,
            tradingview_75m_url=tv_75m,
            chart_review_status="pending",
            screening_errors=[tv_err] if tv_err else [],
        )

        return candidate_record, None, tv_err

    except Exception as exc:
        now_utc = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        failure = {
            "symbol": symbol,
            "yfinance_ticker": yf_ticker,
            "stage": stage,
            "exception_type": type(exc).__name__,
            "error_message": str(exc),
            "timestamp_utc": now_utc,
        }
        return None, failure, None


def run_research_screening(
    dataset_dir: Union[str, Path],
    output_base_dir: Union[str, Path] = DEFAULT_RESULTS_BASE_DIR,
    custom_date_tag: Optional[str] = None,
    min_avg_turnover_cr: float = DEFAULT_MIN_AVG_TURNOVER_CR,
    high_priority_score_threshold: float = DEFAULT_HIGH_PRIORITY_THRESHOLD,
    qualified_score_threshold: float = DEFAULT_QUALIFIED_THRESHOLD,
    watchlist_score_threshold: float = DEFAULT_WATCHLIST_THRESHOLD,
    max_workers: int = 4,
) -> ResearchScreeningResult:
    """Execute complete research screening across 100% of securities in a Phase 9B dataset.

    Args:
        dataset_dir: Path to Phase 9B research dataset directory.
        output_base_dir: Base directory for storing research screening results.
        custom_date_tag: Optional folder name tag (defaults to YYYYMMDD).
        min_avg_turnover_cr: Minimum 20-day turnover in INR Crores for liquidity gate (default 1.0).
        high_priority_score_threshold: Composite score threshold for HIGH_PRIORITY_CANDIDATE (default 60.0).
        qualified_score_threshold: Composite score threshold for QUALIFIED_CANDIDATE (default 40.0).
        watchlist_score_threshold: Composite score threshold for WATCHLIST (default 30.0).
        max_workers: Thread worker pool limit (default 4).

    Returns:
        ResearchScreeningResult containing manifest, all_results_df, candidates_df, disqualified_df, failures_df.
    """
    ds_path = Path(dataset_dir)
    if not ds_path.exists():
        raise FileNotFoundError(f"Research dataset directory not found at: {ds_path}")

    symbols_csv = ds_path / "symbols.csv"
    data_dir = ds_path / "data"

    if not symbols_csv.exists():
        raise FileNotFoundError(f"Required symbols.csv not found in dataset: {symbols_csv}")
    if not data_dir.exists():
        raise FileNotFoundError(f"Required data directory not found in dataset: {data_dir}")

    now_utc = datetime.now(timezone.utc)
    date_tag = custom_date_tag or now_utc.strftime("%Y%m%d")
    results_dir = Path(output_base_dir) / date_tag
    results_dir.mkdir(parents=True, exist_ok=True)

    df_symbols = pd.read_csv(symbols_csv)
    total_input_securities = len(df_symbols)

    dataset_manifest_path = ds_path / "manifest.json"
    dataset_date_str = date_tag
    if dataset_manifest_path.exists():
        try:
            with open(dataset_manifest_path, "r", encoding="utf-8") as f:
                d_man = json.load(f)
                dataset_date_str = d_man.get("source_universe_date", date_tag)
        except Exception:
            pass

    dataset_snapshot_name = str(ds_path.as_posix())

    # Build evaluation tasks
    tasks = []
    for _, row in df_symbols.iterrows():
        sym = str(row.get("symbol", "")).strip().upper()
        yf_ticker = str(row.get("yfinance_ticker", f"{sym}.NS")).strip().upper()
        if not yf_ticker.endswith(".NS"):
            yf_ticker = f"{yf_ticker}.NS"
        company = str(row.get("company_name", sym)).strip()
        csv_file = data_dir / f"{yf_ticker}.csv"
        tasks.append((sym, yf_ticker, company, csv_file))

    successful_results: list[ResearchCandidateResult] = []
    failures_records: list[dict[str, Any]] = []
    tv_failure_count = 0

    # Execute batch screening with bounded concurrency
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_sym = {
            executor.submit(
                _evaluate_single_security,
                symbol=t[0],
                yf_ticker=t[1],
                company_name=t[2],
                csv_path=t[3],
                dataset_snapshot_name=dataset_snapshot_name,
                dataset_date_str=dataset_date_str,
                min_avg_turnover_cr=min_avg_turnover_cr,
                high_priority_score_threshold=high_priority_score_threshold,
                qualified_score_threshold=qualified_score_threshold,
                watchlist_score_threshold=watchlist_score_threshold,
            ): t[0]
            for t in tasks
        }

        for future in as_completed(future_to_sym):
            res_cand, res_fail, tv_err = future.result()
            if tv_err:
                tv_failure_count += 1
            if res_cand:
                successful_results.append(res_cand)
            elif res_fail:
                failures_records.append(res_fail)

    # Sort results by composite_score descending for deterministic order
    successful_results.sort(key=lambda x: (x.composite_score, x.symbol), reverse=True)

    # Build DataFrames
    all_records_dicts = [r.to_dict() for r in successful_results]
    df_all = pd.DataFrame(all_records_dicts)
    df_failures = pd.DataFrame(failures_records)

    # Filter candidate views
    if not df_all.empty:
        df_candidates = df_all[df_all["candidate_category"].isin([
            CandidateCategory.HIGH_PRIORITY_CANDIDATE.value,
            CandidateCategory.QUALIFIED_CANDIDATE.value,
        ])].copy()
        df_disqualified = df_all[df_all["candidate_category"] == CandidateCategory.DISQUALIFIED.value].copy()
    else:
        df_candidates = pd.DataFrame()
        df_disqualified = pd.DataFrame()

    # Category counts
    high_priority_count = sum(1 for r in successful_results if r.candidate_category == CandidateCategory.HIGH_PRIORITY_CANDIDATE.value)
    qualified_count = sum(1 for r in successful_results if r.candidate_category == CandidateCategory.QUALIFIED_CANDIDATE.value)
    watchlist_count = sum(1 for r in successful_results if r.candidate_category == CandidateCategory.WATCHLIST.value)
    no_setup_count = sum(1 for r in successful_results if r.candidate_category == CandidateCategory.NO_SETUP.value)
    disqualified_count = sum(1 for r in successful_results if r.candidate_category == CandidateCategory.DISQUALIFIED.value)
    mech_qual_count = sum(1 for r in successful_results if r.is_mechanically_qualified)

    # Output paths
    all_results_csv_path = results_dir / "all_results.csv"
    candidates_csv_path = results_dir / "candidates.csv"
    disqualified_csv_path = results_dir / "disqualified.csv"
    failures_csv_path = results_dir / "failures.csv"
    manifest_json_path = results_dir / "research_manifest.json"

    df_all.to_csv(all_results_csv_path, index=False)
    df_candidates.to_csv(candidates_csv_path, index=False)
    df_disqualified.to_csv(disqualified_csv_path, index=False)
    df_failures.to_csv(failures_csv_path, index=False)

    manifest = ResearchScreeningManifest(
        screening_run_id=f"research_screening_{date_tag}",
        dataset_snapshot_path=dataset_snapshot_name,
        dataset_date=dataset_date_str,
        generated_at_utc=now_utc.strftime("%Y-%m-%d %H:%M:%S UTC"),
        schema_version="1.0",
        total_input_securities=total_input_securities,
        attempted_evaluations=len(tasks),
        successful_evaluations=len(successful_results),
        failed_evaluations=len(failures_records),
        high_priority_candidates_count=high_priority_count,
        qualified_candidates_count=qualified_count,
        watchlist_candidates_count=watchlist_count,
        no_setup_count=no_setup_count,
        disqualified_count=disqualified_count,
        mechanically_qualified_count=mech_qual_count,
        tradingview_link_failures_count=tv_failure_count,
        screening_policy={
            "min_avg_turnover_cr": min_avg_turnover_cr,
            "high_priority_score_threshold": high_priority_score_threshold,
            "qualified_score_threshold": qualified_score_threshold,
            "watchlist_score_threshold": watchlist_score_threshold,
            "max_workers": max_workers,
        },
    )

    with open(manifest_json_path, "w", encoding="utf-8") as f:
        json.dump(manifest.to_dict(), f, indent=2)

    return ResearchScreeningResult(
        manifest=manifest,
        all_results_df=df_all,
        candidates_df=df_candidates,
        disqualified_df=df_disqualified,
        failures_df=df_failures,
        results_dir=results_dir,
    )
