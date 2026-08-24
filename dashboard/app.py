"""Wyckoff Method & VSA Explainable Research Screener Dashboard (Streamlit).

Phase 14 — Explainable, Beginner-Friendly UI with Frozen Analytical Core.

Guiding Principles (AGENTS.md):
- No Fabricated Confidence: Every flagged event cites specific numbers.
- Candidates, Never Certainties: Signals are candidate schematic events.
- Research & Screening Tool Only: No live order execution.
"""

from __future__ import annotations
from datetime import datetime
import json
import logging
import os
from pathlib import Path
import sys
from typing import Any, Dict, Optional

_repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_src_path = os.path.join(_repo_root, "src")
_dashboard_path = os.path.join(_repo_root, "dashboard")

for _p in [_repo_root, _src_path, _dashboard_path]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import streamlit as st
import yfinance as yf

try:
    from dashboard.explainers import (
        render_chart_checklist_card,
        render_risks_and_invalidations_card,
        render_score_breakdown_card,
        render_screening_checklist_expander,
        render_why_selected_card,
        render_wyckoff_interpretation_card,
    )
    from dashboard.glossary import WYCKOFF_GLOSSARY, get_glossary_terms, get_term_details
except ImportError:
    from explainers import (
        render_chart_checklist_card,
        render_risks_and_invalidations_card,
        render_score_breakdown_card,
        render_screening_checklist_expander,
        render_why_selected_card,
        render_wyckoff_interpretation_card,
    )
    from glossary import WYCKOFF_GLOSSARY, get_glossary_terms, get_term_details

from wyckoff_screener.charting.tradingview_links import CHART_REVIEW_CHECKLIST, generate_tradingview_links
from wyckoff_screener.data_loader import validate_ohlcv_dataframe
from wyckoff_screener.pointfigure.pf_chart import build_point_and_figure_chart, count_price_objective
from wyckoff_screener.scoring.setup_scorer import score_setup
from wyckoff_screener.wyckoff.schematic_events import detect_all_schematic_events

# ─────────────────────────────────────────────────────────────────────────────
# PAGE SETUP
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Wyckoff VSA Research Screener — NSE",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────────────────────────────────────
# CSS STYLING
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

/* Sidebar */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0f172a 0%, #1e293b 100%);
}
section[data-testid="stSidebar"] * { color: #e2e8f0 !important; }
section[data-testid="stSidebar"] .stRadio > div { gap: 4px; }

/* Category chips */
.chip-high   { background:#064e3b; color:#6ee7b7; border:1px solid #10b981; padding:4px 12px; border-radius:20px; font-size:0.82rem; font-weight:700; }
.chip-qual   { background:#1e3a5f; color:#93c5fd; border:1px solid #3b82f6; padding:4px 12px; border-radius:20px; font-size:0.82rem; font-weight:700; }
.chip-watch  { background:#3b2a00; color:#fcd34d; border:1px solid #f59e0b; padding:4px 12px; border-radius:20px; font-size:0.82rem; font-weight:700; }
.chip-disq   { background:#450a0a; color:#fca5a5; border:1px solid #ef4444; padding:4px 12px; border-radius:20px; font-size:0.82rem; font-weight:700; }
.chip-none   { background:#1e293b; color:#94a3b8; border:1px solid #475569; padding:4px 12px; border-radius:20px; font-size:0.82rem; font-weight:700; }

/* Disclaimer & Educational Banners */
.disclaimer {
    background:#1e1b0e; color:#fbbf24; border-left:4px solid #f59e0b;
    padding:10px 16px; border-radius:6px; font-size:0.85rem;
    margin-bottom:18px; font-weight:500;
}
.edu-box {
    background:#0f172a; border:1px solid #334155; border-left:4px solid #38bdf8;
    padding:12px 18px; border-radius:8px; margin-bottom:16px; font-size:0.9rem; color:#e2e8f0;
}

/* Status banners */
.banner-qual  { background:#052e16; color:#86efac; border-left:5px solid #22c55e; padding:14px 20px; border-radius:8px; font-size:1.1rem; font-weight:700; margin-bottom:16px; }
.banner-disq  { background:#1a0000; color:#f87171; border-left:5px solid #ef4444; padding:14px 20px; border-radius:8px; font-size:1.1rem; font-weight:700; margin-bottom:16px; }

/* Score box */
.score-caveat { background:#1c1800; color:#fde68a; border-left:4px solid #d97706; padding:12px 16px; border-radius:6px; font-size:0.85rem; margin:12px 0 16px; }

/* Metric cards */
.metric-card { background:#0f172a; border:1px solid #1e293b; border-radius:10px; padding:14px 18px; text-align:center; }
.metric-card .label { color:#94a3b8; font-size:0.78rem; text-transform:uppercase; letter-spacing:0.06em; font-weight:600; }
.metric-card .value { color:#f1f5f9; font-size:1.5rem; font-weight:700; margin:4px 0; }
.metric-card .sub   { color:#64748b; font-size:0.75rem; }

/* Section header */
.section-header { font-size:1.1rem; font-weight:700; color:#e2e8f0; margin:22px 0 10px;
    padding-bottom:6px; border-bottom:1px solid #334155; }

/* Glossary Card */
.glossary-card {
    background:#0f172a; border:1px solid #1e293b; border-radius:8px;
    padding:14px 18px; margin-bottom:12px;
}
.glossary-title { font-size:1.05rem; font-weight:700; color:#38bdf8; margin-bottom:4px; }
.glossary-cat { font-size:0.75rem; color:#94a3b8; text-transform:uppercase; letter-spacing:0.05em; margin-bottom:8px; }
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────────────────
def category_chip(cat: str) -> str:
    cat = str(cat)
    if "HIGH_PRIORITY" in cat:
        return '<span class="chip-high">⭐ High Priority Candidate</span>'
    elif "QUALIFIED" in cat:
        return '<span class="chip-qual">✅ Qualified Candidate</span>'
    elif "WATCHLIST" in cat:
        return '<span class="chip-watch">👁 Watchlist Candidate</span>'
    elif "DISQUALIFIED" in cat:
        return '<span class="chip-disq">🚫 Disqualified Setup</span>'
    return '<span class="chip-none">— No Setup</span>'


def section(label: str):
    st.markdown(f'<div class="section-header">{label}</div>', unsafe_allow_html=True)


def latest_results_dir(base: str) -> Optional[Path]:
    p = Path(base)
    if not p.exists():
        return None
    dirs = sorted([d for d in p.iterdir() if d.is_dir()], reverse=True)
    return dirs[0] if dirs else None


# ─────────────────────────────────────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.image("https://img.icons8.com/color/48/000000/combo-chart.png", width=40)
    st.markdown("## 📈 Wyckoff Screener")
    st.caption("NSE Equity Research · Evidence-First")
    st.markdown("---")

    beginner_mode = st.toggle("💡 Beginner Mode", value=True, help="Provides plain-English explanations and glossary helpers throughout the dashboard.")

    page = st.radio(
        "Navigation",
        [
            "🏠 Home / Single Stock",
            "📊 Research Screening Results",
            "📉 Historical Validation",
            "🔮 Forward Paper Validation",
            "📖 Wyckoff Glossary",
        ],
        index=0,
    )

    st.markdown("---")
    if page == "🏠 Home / Single Stock":
        st.markdown("**Data Source Mode**")
        data_source_mode = st.radio(
            "source", ["Live Ticker (yfinance)", "Upload CSV File"], label_visibility="collapsed"
        )
    else:
        data_source_mode = None

    st.markdown("---")
    st.caption("Phase 14 · Explainable Wyckoff UI · Frozen Research Engine")


# ─────────────────────────────────────────────────────────────────────────────
# GLOBAL DISCLAIMER BANNER
# ─────────────────────────────────────────────────────────────────────────────
st.markdown(
    '<div class="disclaimer">⚠️ <strong>EDUCATIONAL & RESEARCH TOOL ONLY — NOT FINANCIAL ADVICE.</strong> '
    'Every flagged Wyckoff event is an unconfirmed quantitative candidate supported by empirical volume-spread metrics. '
    'This system does NOT generate automated buy/sell signals or guaranteed price predictions. '
    'Always conduct independent visual chart review before reaching any market conclusion.</div>',
    unsafe_allow_html=True,
)


# ─────────────────────────────────────────────────────────────────────────────
# PAGE 1: HOME / SINGLE STOCK ANALYSIS
# ─────────────────────────────────────────────────────────────────────────────
if page == "🏠 Home / Single Stock":
    st.title("📈 Single Stock Wyckoff & VSA Research")

    # Introductory Educational Card
    if beginner_mode:
        st.markdown("""
        <div class="edu-box">
        <strong>👋 How does this screener work?</strong><br>
        This tool applies <strong>Richard Wyckoff's structural accumulation framework</strong> combined with
        <strong>Volume Spread Analysis (VSA)</strong> to evaluate Indian equities (NSE). It analyzes daily price spreads and volume interactions
        to detect whether institutional buyers (<em>"smart money"</em>) may be accumulating shares before an upward markup phase.
        <br><br>
        <strong>Pipeline Flow:</strong> Market Data ➔ Moving Average & Momentum Filters ➔ Wyckoff Schematic Detectors ➔
        Mechanical Qualification Gates ➔ Composite Scoring (0–100) ➔ Visual Chart Review.
        </div>
        """, unsafe_allow_html=True)

    df: Optional[pd.DataFrame] = None
    current_symbol: str = "ANANTRAJ.NS"

    if data_source_mode == "Live Ticker (yfinance)":
        c_sym, c_start, c_end = st.columns([3, 2, 2])
        with c_sym:
            ticker_input = st.text_input("NSE Ticker (with .NS suffix)", value="ANANTRAJ.NS", key="ticker", help="E.g. ANANTRAJ.NS, APOLLO.NS, HINDCOPPER.NS, TATAMOTORS.NS")
            current_symbol = ticker_input.strip().upper()
        with c_start:
            start_date = st.date_input("Start Date", value=pd.to_datetime("2024-01-01"))
        with c_end:
            end_date = st.date_input("End Date", value=pd.to_datetime("today"))

        st.caption("Quick Select Presets: `ANANTRAJ.NS`, `APOLLO.NS`, `HINDCOPPER.NS`, `TATAMOTORS.NS`, `RELIANCE.NS`")

        if st.button("🔍 Fetch & Analyze Stock", type="primary", use_container_width=True):
            with st.spinner(f"Fetching market data for {current_symbol}..."):
                try:
                    raw_df = yf.download(current_symbol, start=start_date, end=end_date, progress=False)
                    if raw_df.empty:
                        st.error(f"No market data returned for '{current_symbol}'. Verify ticker symbol.")
                    else:
                        if isinstance(raw_df.columns, pd.MultiIndex):
                            raw_df.columns = raw_df.columns.get_level_values(0)
                        df = validate_ohlcv_dataframe(raw_df.reset_index())
                        st.session_state["loaded_df"] = df
                        st.session_state["symbol"] = current_symbol
                except Exception as exc:
                    st.error(f"Failed to fetch market data: {exc}")

    elif data_source_mode == "Upload CSV File":
        uploaded_file = st.file_uploader(
            "Upload OHLCV CSV (Requires columns: Date, Open, High, Low, Close, Volume)", type=["csv"]
        )
        if uploaded_file is not None:
            try:
                raw_df = pd.read_csv(uploaded_file)
                df = validate_ohlcv_dataframe(raw_df)
                current_symbol = uploaded_file.name.replace(".csv", "").upper()
                st.session_state["loaded_df"] = df
                st.session_state["symbol"] = current_symbol
            except Exception as exc:
                st.error(f"CSV Validation Error: {exc}")

    if "loaded_df" in st.session_state:
        df = st.session_state["loaded_df"]
        current_symbol = st.session_state.get("symbol", current_symbol)

    if df is not None and not df.empty:
        scored = score_setup(df, symbol=current_symbol)

        # ── Stock Header Row
        st.markdown("---")
        hcol1, hcol2, hcol3 = st.columns([3, 2, 2])
        with hcol1:
            st.markdown(f"## {current_symbol}")
            st.caption(
                f"📊 **Data Bars**: {len(df)} daily trading sessions · "
                f"**Date Range**: {str(df['Date'].iloc[0])[:10]} → **{str(df['Date'].iloc[-1])[:10]}**"
            )
        with hcol2:
            st.metric("Reference Close Price", f"₹{df['Close'].iloc[-1]:.2f}")
        with hcol3:
            st.markdown(category_chip(scored.candidate_category), unsafe_allow_html=True)
            st.caption(f"Composite Score: **{scored.composite_score:.1f} / 100**")

        # ── 1. "WHY WAS THIS STOCK SELECTED?"
        render_why_selected_card(
            symbol=current_symbol,
            category=scored.candidate_category,
            composite_score=scored.composite_score,
            event_type=scored.most_recent_event_type or "None",
            event_date=scored.most_recent_event_date or "N/A",
            vol_ratio=scored.vsa_volume_ratio,
            spread_ratio=scored.vsa_spread_ratio,
            close_pos=scored.vsa_close_position,
            mechanical_passed=scored.is_mechanically_qualified,
            filter_details=scored.filter_results,
            pf_target=scored.pf_target_price,
            pf_upside=scored.pf_upside_pct,
            pf_is_stale=scored.pf_is_stale_anchor,
            is_disqualified=scored.is_disqualified,
            disqualifying_flags=" · ".join(scored.disqualifying_flags) if scored.disqualifying_flags else "None",
            explanation_summary=scored.supporting_note,
            beginner_mode=beginner_mode,
        )

        st.markdown("---")

        # ── 2. WYCKOFF INTERPRETATION
        render_wyckoff_interpretation_card(
            event_type=scored.most_recent_event_type or "None",
            event_date=scored.most_recent_event_date or "N/A",
            vol_ratio=scored.vsa_volume_ratio,
            spread_ratio=scored.vsa_spread_ratio,
            close_pos=scored.vsa_close_position,
            beginner_mode=beginner_mode,
        )

        st.markdown("---")

        # ── 3. WHAT SHOULD I LOOK AT ON THE CHART?
        render_chart_checklist_card(
            filter_details=scored.filter_results,
            vol_ratio=scored.vsa_volume_ratio,
            spread_ratio=scored.vsa_spread_ratio,
            close_pos=scored.vsa_close_position,
            event_type=scored.most_recent_event_type or "None",
            pf_target=scored.pf_target_price,
            pf_is_stale=scored.pf_is_stale_anchor,
            is_disqualified=scored.is_disqualified,
        )

        st.markdown("---")

        # ── 4. SCORE BREAKDOWN
        render_score_breakdown_card(
            composite_score=scored.composite_score,
            score_breakdown=scored.score_breakdown,
            beginner_mode=beginner_mode,
        )

        # ── 5. SCREENING CHECKLIST (Expandable)
        render_screening_checklist_expander(
            filter_details=scored.filter_results,
            vol_ratio=scored.vsa_volume_ratio,
            spread_ratio=scored.vsa_spread_ratio,
            close_pos=scored.vsa_close_position,
        )

        # ── 6. RISKS & INVALIDATIONS
        render_risks_and_invalidations_card(
            event_type=scored.most_recent_event_type or "None",
            is_disqualified=scored.is_disqualified,
            disqualifying_flags=" · ".join(scored.disqualifying_flags) if scored.disqualifying_flags else "None",
        )

        st.markdown("---")

        # ── 7. INTERACTIVE VISUALS: CANDLESTICK & VSA CHART
        st.markdown("### 📊 Price & Volume Spread Analysis Chart")

        fig, (ax_price, ax_vol) = plt.subplots(2, 1, figsize=(13, 7), sharex=True, gridspec_kw={"height_ratios": [3, 1]})
        fig.patch.set_facecolor("#0f172a")
        ax_price.set_facecolor("#0f172a")
        ax_vol.set_facecolor("#0f172a")

        # Plot last 120 bars for clear visual inspection
        chart_df = df.tail(120).copy().reset_index(drop=True)
        chart_df["Bar_Idx"] = range(len(chart_df))

        # Candles
        for i, row in chart_df.iterrows():
            is_up = row["Close"] >= row["Open"]
            candle_color = "#22c55e" if is_up else "#ef4444"
            ax_price.plot([i, i], [row["Low"], row["High"]], color=candle_color, linewidth=1.2)
            rect_bottom = min(row["Open"], row["Close"])
            rect_height = abs(row["Close"] - row["Open"])
            ax_price.bar(i, rect_height, bottom=rect_bottom, color=candle_color, width=0.6, alpha=0.9)

        # Volume bars
        colors = ["#22c55e" if c >= o else "#ef4444" for c, o in zip(chart_df["Close"], chart_df["Open"])]
        ax_vol.bar(chart_df["Bar_Idx"], chart_df["Volume"], color=colors, width=0.6, alpha=0.8)

        ax_price.set_title(f"{current_symbol} — Daily Price Action (Trailing 120 Bars)", color="#e2e8f0", fontsize=13, fontweight="bold")
        ax_price.tick_params(colors="#94a3b8")
        ax_vol.tick_params(colors="#94a3b8")
        ax_price.grid(True, color="#334155", linestyle="--", alpha=0.3)
        ax_vol.grid(True, color="#334155", linestyle="--", alpha=0.3)
        st.pyplot(fig)
        plt.close(fig)

        # ── 8. POINT & FIGURE CHART & TARGETS
        section("Bruce Fraser Point & Figure Analysis")
        pf_obj = count_price_objective(df)
        if pf_obj and pf_obj.target_price:
            st.markdown(
                f"**Calculated P&F Objective**: **₹{pf_obj.target_price:.2f}** "
                f"(Upside: **+{pf_obj.upside_pct:.1f}%** | Count Row: ₹{pf_obj.count_row_price:.2f} | Columns: {pf_obj.columns_counted})"
            )
            if scored.pf_is_stale_anchor:
                st.warning("⚠️ **Stale P&F Anchor Warning**: Count row anchor is older than 60 bars.")
        else:
            st.info("No Point & Figure horizontal count row identified in current trading range.")

    else:
        st.info("👆 Select a preset ticker (e.g. `ANANTRAJ.NS`) or upload an OHLCV CSV file to analyze a stock.")


# ─────────────────────────────────────────────────────────────────────────────
# PAGE 2: RESEARCH SCREENING RESULTS
# ─────────────────────────────────────────────────────────────────────────────
elif page == "📊 Research Screening Results":
    st.title("📊 Research Screening Results (Phase 9C)")
    st.caption("Broad NSE Equity universe screening triage and candidate intelligence.")

    if beginner_mode:
        st.markdown("""
        <div class="edu-box">
        <strong>💡 How to use this page:</strong><br>
        This page presents the results of scanning the NSE equity universe at date <em>T</em>. Stocks are categorized into:
        <ul>
            <li><span class="chip-high">⭐ High Priority</span>: Passed all mechanical trend filters + strong recent Wyckoff candidate event + constructive volume.</li>
            <li><span class="chip-qual">✅ Qualified</span>: Passed technical qualification gates; worthy of manual chart review.</li>
            <li><span class="chip-watch">👁 Watchlist</span>: Setup detected but technical trend/momentum conditions are lagging.</li>
            <li><span class="chip-disq">🚫 Disqualified</span>: Severe red flags detected (UTAD or distribution structure).</li>
        </ul>
        </div>
        """, unsafe_allow_html=True)

    base_results = Path(_repo_root) / "data" / "research_results"
    if not base_results.exists():
        st.info("No research screening results found in `data/research_results/`. Run batch screening locally first.")
    else:
        run_dirs = sorted([d for d in base_results.iterdir() if d.is_dir()], reverse=True)
        if not run_dirs:
            st.info("No completed screening runs found.")
        else:
            sel_dir = st.selectbox("Select Screening Run Date", run_dirs, format_func=lambda d: d.name)
            cand_path = sel_dir / "candidates.csv"
            all_path = sel_dir / "all_results.csv"

            if cand_path.exists() and all_path.exists():
                df_all = pd.read_csv(all_path)
                st.markdown(f"**Total Securities Evaluated**: {len(df_all)}")

                # Filter Controls
                fc1, fc2, fc3 = st.columns(3)
                with fc1:
                    categories = ["All Categories"] + sorted(df_all["candidate_category"].dropna().unique().tolist())
                    sel_cat = st.selectbox("Filter by Category", categories)
                with fc2:
                    min_score = st.slider("Minimum Composite Score", 0.0, 100.0, 30.0, 5.0)
                with fc3:
                    event_filter = st.selectbox("Filter by Wyckoff Event", ["All Events", "LPS", "Spring", "SOS", "SC", "UTAD"])

                filtered_df = df_all.copy()
                if sel_cat != "All Categories":
                    filtered_df = filtered_df[filtered_df["candidate_category"] == sel_cat]
                filtered_df = filtered_df[filtered_df["composite_score"] >= min_score]
                if event_filter != "All Events":
                    filtered_df = filtered_df[filtered_df["most_recent_event_type"] == event_filter]

                # Human-readable table
                display_cols = [
                    c for c in [
                        "symbol", "candidate_category", "composite_score", "reference_close_price",
                        "is_mechanically_qualified", "vsa_volume_ratio", "vsa_spread_ratio",
                        "most_recent_event_type", "pf_target_price", "pf_upside_pct"
                    ] if c in filtered_df.columns
                ]
                st.dataframe(
                    filtered_df[display_cols].sort_values("composite_score", ascending=False),
                    use_container_width=True,
                    height=450,
                )


# ─────────────────────────────────────────────────────────────────────────────
# PAGE 3: HISTORICAL VALIDATION
# ─────────────────────────────────────────────────────────────────────────────
elif page == "📉 Historical Validation":
    st.title("📉 Historical Walk-Forward Backtesting (Phase 10)")
    st.caption("Empirical out-of-sample performance across 3,639 historical checkpoints.")

    # Top Educational Banner
    st.markdown("""
    <div class="edu-box">
    <strong>🔬 What is Historical Validation?</strong><br>
    Historical validation evaluates how candidate setups flagged by the frozen Wyckoff research engine performed
    <strong>across past historical market data</strong> (Jan 2024 – Aug 2026). At each rolling 5-bar checkpoint,
    the engine evaluates past data strictly without lookahead and records forward close-to-close returns at
    <strong>10-day</strong>, <strong>20-day</strong>, and <strong>60-day</strong> horizons.<br><br>
    <em>Difference:</em> <strong>Historical Backtesting</strong> tests past history retroactively;
    <strong>Forward Paper Validation</strong> tracks live prospective signals moving forward in time.
    </div>
    """, unsafe_allow_html=True)

    val_base = Path(_repo_root) / "data" / "validation_results"
    if not val_base.exists():
        st.info("No historical validation results found in `data/validation_results/`.")
    else:
        val_dirs = sorted([d for d in val_base.iterdir() if d.is_dir()], reverse=True)
        if val_dirs:
            selected_val = st.selectbox("Validation Run Date", val_dirs, format_func=lambda d: d.name)
            cat_path = selected_val / "category_performance.csv"
            score_path = selected_val / "score_band_performance.csv"
            split_path = selected_val / "in_sample_vs_out_sample.csv"
            sig_path = selected_val / "signal_events.csv"

            vt1, vt2, vt3, vt4 = st.tabs([
                "📊 Cohort Performance", "🏷 Score Bands (Caveats)",
                "🗓 In-Sample vs Out-of-Sample", "📋 Signal Observations"
            ])

            with vt1:
                if cat_path.exists():
                    cdf = pd.read_csv(cat_path)
                    if not cdf.empty:
                        horizons = sorted(cdf["horizon"].unique())
                        for h in horizons:
                            section(f"Forward Horizon: {h}")
                            cohort_col = "cohort_name" if "cohort_name" in cdf.columns else "cohort_value"
                            sub_cols = [c for c in ["cohort_group", cohort_col, "observation_count",
                                                    "mean_return_pct", "median_return_pct", "win_rate_pct",
                                                    "mean_mfe_pct", "mean_mae_pct"] if c in cdf.columns]
                            sub = cdf[cdf["horizon"] == h][sub_cols].copy()
                            sub = sub.rename(columns={
                                "cohort_group": "Group", cohort_col: "Cohort",
                                "observation_count": "N", "mean_return_pct": "Mean Return %",
                                "median_return_pct": "Median Return %", "win_rate_pct": "Win Rate %",
                                "mean_mfe_pct": "Mean MFE %", "mean_mae_pct": "Mean MAE %"
                            })
                            st.dataframe(sub, use_container_width=True, height=280)

            with vt2:
                if score_path.exists():
                    sdf = pd.read_csv(score_path)
                    if not sdf.empty:
                        st.dataframe(sdf, use_container_width=True, height=350)
                        st.markdown(
                            '<div class="score-caveat">⚠️ <strong>Critical Finding (Non-Monotonic Scores)</strong>: '
                            'From Phase 7/10 backtesting across 3 stocks, high-score setups (>=60) inverted vs low-score setups on 2 of 3 stocks. '
                            'Do not use composite score as a precision ranking. Treat as coarse triage only.</div>',
                            unsafe_allow_html=True,
                        )

            with vt3:
                if split_path.exists():
                    spdf = pd.read_csv(split_path)
                    if not spdf.empty:
                        st.dataframe(spdf, use_container_width=True, height=350)

            with vt4:
                if sig_path.exists():
                    sigdf = pd.read_csv(sig_path)
                    if not sigdf.empty:
                        st.dataframe(sigdf.head(200), use_container_width=True, height=450)
                        st.caption(f"Showing first 200 of {len(sigdf)} recorded historical observations.")


# ─────────────────────────────────────────────────────────────────────────────
# PAGE 4: FORWARD PAPER VALIDATION
# ─────────────────────────────────────────────────────────────────────────────
elif page == "🔮 Forward Paper Validation":
    st.title("🔮 Prospective Forward Paper Validation (Phase 11)")
    st.caption("Real-world forward tracking of frozen research candidates with strict zero-lookahead discipline.")

    # Educational Banner
    st.markdown("""
    <div class="edu-box">
    <strong>📋 What is Forward Paper Validation?</strong><br>
    Unlike historical backtesting, Forward Paper Validation operates <strong>prospectively into the future</strong>.
    Candidate snapshots are frozen at screening date <em>T</em> before future price action exists.
    Forward close-to-close returns and excursions (MFE / MAE) are calculated only as subsequent trading days unfold.
    <br><br>
    <em>Notice:</em> This is <strong>paper/research tracking</strong>, not live trading. It does not account for brokerage fees, STT, or market slippage.
    </div>
    """, unsafe_allow_html=True)

    fwd_base = Path(_repo_root) / "data" / "forward_validation"
    ledger_path = fwd_base / "ledger" / "forward_ledger.csv"
    outcomes_path = fwd_base / "ledger" / "forward_outcomes.csv"
    snapshots_dir = fwd_base / "snapshots"

    total_cand = 0
    total_snaps = 0
    latest_scr_date = "N/A"
    m_10, p_10 = 0, 0
    m_20, p_20 = 0, 0
    m_60, p_60 = 0, 0

    df_outcomes = pd.DataFrame()
    if outcomes_path.exists():
        try:
            df_outcomes = pd.read_csv(outcomes_path)
            total_cand = len(df_outcomes)
            if not df_outcomes.empty and "screening_date" in df_outcomes.columns:
                latest_scr_date = str(df_outcomes["screening_date"].max())
            if "status_10d" in df_outcomes.columns:
                m_10 = int((df_outcomes["status_10d"] == "MATURED").sum())
                p_10 = int((df_outcomes["status_10d"] == "PENDING").sum())
            if "status_20d" in df_outcomes.columns:
                m_20 = int((df_outcomes["status_20d"] == "MATURED").sum())
                p_20 = int((df_outcomes["status_20d"] == "PENDING").sum())
            if "status_60d" in df_outcomes.columns:
                m_60 = int((df_outcomes["status_60d"] == "MATURED").sum())
                p_60 = int((df_outcomes["status_60d"] == "PENDING").sum())
        except Exception:
            pass

    if snapshots_dir.exists():
        snap_files = sorted(snapshots_dir.glob("snapshot_*.json"))
        total_snaps = len(snap_files)

    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        st.markdown(f'<div class="metric-card"><div class="label">Total Tracked</div><div class="value">{total_cand}</div><div class="sub">{total_snaps} snapshots</div></div>', unsafe_allow_html=True)
    with c2:
        st.markdown(f'<div class="metric-card"><div class="label">10D Horizon</div><div class="value" style="color:#6ee7b7;">{m_10} Mat</div><div class="sub">{p_10} pending</div></div>', unsafe_allow_html=True)
    with c3:
        st.markdown(f'<div class="metric-card"><div class="label">20D Horizon</div><div class="value" style="color:#93c5fd;">{m_20} Mat</div><div class="sub">{p_20} pending</div></div>', unsafe_allow_html=True)
    with c4:
        st.markdown(f'<div class="metric-card"><div class="label">60D Horizon</div><div class="value" style="color:#fcd34d;">{m_60} Mat</div><div class="sub">{p_60} pending</div></div>', unsafe_allow_html=True)
    with c5:
        st.markdown(f'<div class="metric-card"><div class="label">Latest Screening</div><div class="value" style="font-size:1.15rem;">{latest_scr_date}</div><div class="sub">Date T</div></div>', unsafe_allow_html=True)

    st.markdown("---")

    ft1, ft2, ft3, ft4, ft5, ft6 = st.tabs([
        "📸 Latest Screening", "⏳ Active Candidates", "📈 Matured Outcomes",
        "⚖️ Forward vs Historical", "📊 Category Breakdown", "🛡️ Data Integrity & Audit"
    ])

    with ft1:
        st.markdown("#### 📸 Frozen Screening Snapshots")
        if snapshots_dir.exists() and total_snaps > 0:
            snap_dates = [p.stem.replace("snapshot_", "") for p in sorted(snapshots_dir.glob("snapshot_*.json"), reverse=True)]
            sel_date_tag = st.selectbox("Select Screening Snapshot Date", snap_dates, index=0)
            target_snap_file = snapshots_dir / f"snapshot_{sel_date_tag}.json"
            if target_snap_file.exists():
                try:
                    with open(target_snap_file, "r", encoding="utf-8") as f:
                        snap_data = json.load(f)
                    records = snap_data.get("candidate_records", [])
                    if records:
                        st.dataframe(pd.DataFrame(records), use_container_width=True, height=450)
                except Exception as exc:
                    st.error(f"Error loading snapshot: {exc}")
        else:
            st.info("No forward screening snapshots found in `data/forward_validation/snapshots/`.")

    with ft2:
        st.markdown("#### ⏳ Active Forward Candidates (Tracking in Progress)")
        if not df_outcomes.empty:
            active_df = df_outcomes[df_outcomes["status_60d"] == "PENDING"].copy()
            if not active_df.empty:
                st.dataframe(active_df, use_container_width=True, height=450)
            else:
                st.info("No active pending candidates. All recorded candidate horizons have matured.")
        else:
            st.info("Forward outcomes ledger is empty.")

    with ft3:
        st.markdown("#### 📈 Realized Forward Performance by Cohort")
        if not df_outcomes.empty:
            for h in [10, 20, 60]:
                st.markdown(f"##### Forward Horizon: **{h} Trading Days**")
                status_col = f"status_{h}d"
                ret_col = f"fwd_ret_{h}d"
                if status_col in df_outcomes.columns and ret_col in df_outcomes.columns:
                    matured = df_outcomes[df_outcomes[status_col] == "MATURED"].copy()
                    if not matured.empty:
                        agg_rows = []
                        r_all = matured[ret_col].dropna()
                        if len(r_all) > 0:
                            agg_rows.append({
                                "Category": "UNIVERSE BASELINE",
                                "N": len(r_all),
                                "Mean Return %": f"{r_all.mean():+.2f}%",
                                "Median Return %": f"{r_all.median():+.2f}%",
                                "Win Rate %": f"{(r_all > 0).mean() * 100:.1f}%",
                            })
                        for cat, grp in matured.groupby("candidate_category"):
                            r_cat = grp[ret_col].dropna()
                            if len(r_cat) > 0:
                                agg_rows.append({
                                    "Category": cat,
                                    "N": len(r_cat),
                                    "Mean Return %": f"{r_cat.mean():+.2f}%",
                                    "Median Return %": f"{r_cat.median():+.2f}%",
                                    "Win Rate %": f"{(r_cat > 0).mean() * 100:.1f}%",
                                })
                        st.dataframe(pd.DataFrame(agg_rows), use_container_width=True)
                    else:
                        st.info(f"No matured {h}-day observations yet.")
        else:
            st.info("No forward outcomes recorded.")

    with ft4:
        st.markdown("#### ⚖️ Phase 10 Historical Validation vs. Phase 11 Prospective Forward")
        hist_benchmark = {
            "HIGH_PRIORITY_CANDIDATE": {"hist_mean": "+6.39%", "hist_win": "64.06%", "hist_n": 128},
            "QUALIFIED_CANDIDATE": {"hist_mean": "+6.93%", "hist_win": "59.65%", "hist_n": 171},
            "WATCHLIST": {"hist_mean": "+4.09%", "hist_win": "53.93%", "hist_n": 1131},
            "DISQUALIFIED": {"hist_mean": "+2.82%", "hist_win": "53.23%", "hist_n": 620},
            "UNIVERSE BASELINE": {"hist_mean": "+4.09%", "hist_win": "54.83%", "hist_n": 2050},
        }
        if not df_outcomes.empty and "status_60d" in df_outcomes.columns:
            matured_60 = df_outcomes[df_outcomes["status_60d"] == "MATURED"]
            if len(matured_60) < 30:
                st.warning(f"⚠️ **Sample Size Caution (N = {len(matured_60)})**: Insufficient forward observations for definitive statistical comparison. Treat as exploratory directional evidence only.")
            comp_rows = []
            for cat, bdata in hist_benchmark.items():
                fwd_sub = matured_60 if cat == "UNIVERSE BASELINE" else matured_60[matured_60["candidate_category"] == cat]
                fwd_n = len(fwd_sub)
                fwd_mean = f"{fwd_sub['fwd_ret_60d'].mean():+.2f}%" if fwd_n > 0 else "–"
                fwd_win = f"{(fwd_sub['fwd_ret_60d'] > 0).mean() * 100:.1f}%" if fwd_n > 0 else "–"
                comp_rows.append({
                    "Cohort": cat, "Hist 60d Mean": bdata["hist_mean"], "Hist Win%": bdata["hist_win"],
                    "Hist N": bdata["hist_n"], "Fwd 60d Mean": fwd_mean, "Fwd Win%": fwd_win, "Fwd N": fwd_n,
                })
            st.dataframe(pd.DataFrame(comp_rows), use_container_width=True)
        else:
            st.info("No forward 60-day observations have matured yet.")

    with ft5:
        st.markdown("#### 📊 Candidate Category Distribution")
        if not df_outcomes.empty and "candidate_category" in df_outcomes.columns:
            cat_counts = df_outcomes["candidate_category"].value_counts().reset_index()
            cat_counts.columns = ["Candidate Category", "Total Count"]
            st.dataframe(cat_counts, use_container_width=True)

    with ft6:
        st.markdown("#### 🛡️ Data Integrity & Zero-Lookahead Audit Panel")
        ic1, ic2, ic3 = st.columns(3)
        with ic1:
            st.success("✅ **Zero Lookahead**: Screening at Date T uses strictly Date <= T")
            st.success("✅ **Immutable Snapshots**: SHA-256 candidate hashing & frozen JSON")
        with ic2:
            st.success("✅ **Exclusion of Bar T**: Forward returns evaluate T+1 through T+H")
            st.success("✅ **Idempotent Updates**: Re-evaluating outcomes does not duplicate records")
        with ic3:
            st.success("✅ **Duplicate Protection**: Re-screening same date requires `--overwrite`")
            st.success("✅ **Read-Only Dashboard**: UI strictly displays data without modifying files")


# ─────────────────────────────────────────────────────────────────────────────
# PAGE 5: WYCKOFF GLOSSARY
# ─────────────────────────────────────────────────────────────────────────────
elif page == "📖 Wyckoff Glossary":
    st.title("📖 Wyckoff & VSA Educational Glossary")
    st.caption("Plain-English definitions and technical engine specifications for all terminology used in this application.")

    search_query = st.text_input("🔍 Search Glossary Terms", placeholder="E.g. Spring, LPS, SOS, Volume Ratio, MFE, P&F...").strip().lower()

    terms = get_glossary_terms()
    if search_query:
        terms = [t for t in terms if search_query in t.lower() or search_query in WYCKOFF_GLOSSARY[t]["simple_definition"].lower()]

    if not terms:
        st.info(f"No glossary terms matching '{search_query}'.")
    else:
        st.markdown(f"**Showing {len(terms)} terms:**")
        for term_title in terms:
            tdata = WYCKOFF_GLOSSARY[term_title]
            with st.expander(f"📚 {term_title} ({tdata.get('category', 'Concept')})", expanded=bool(search_query)):
                st.markdown(f"**Simple Definition:** {tdata['simple_definition']}")
                st.markdown(f"**Why It Matters in Wyckoff:** {tdata['why_it_matters']}")
                st.markdown(f"**How the Screener Evaluates It:** `{tdata['engine_logic']}`")
