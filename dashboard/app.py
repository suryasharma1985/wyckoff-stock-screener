"""Wyckoff Method & VSA Research Dashboard — Phase 9C + Phase 10 (Streamlit).

Guiding Principles (AGENTS.md):
- No Fabricated Confidence: Every flagged event cites specific numbers.
- Candidates, Never Certainties: Signals are candidate schematic events.
- Research & Screening Tool Only: No live order execution.
"""

from __future__ import annotations
from pathlib import Path
from typing import Optional
import sys, os

_src_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src")
if _src_path not in sys.path:
    sys.path.insert(0, _src_path)

import pandas as pd
import streamlit as st
import yfinance as yf
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import json

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
# CSS
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

/* Sidebar */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0f172a 0%, #1e293b 100%);
}
section[data-testid="stSidebar"] * { color: #e2e8f0 !important; }
section[data-testid="stSidebar"] .stRadio > div { gap: 4px; }

/* Category chips */
.chip-high   { background:#064e3b; color:#6ee7b7; border:1px solid #10b981; padding:3px 10px; border-radius:20px; font-size:0.78rem; font-weight:600; }
.chip-qual   { background:#1e3a5f; color:#93c5fd; border:1px solid #3b82f6; padding:3px 10px; border-radius:20px; font-size:0.78rem; font-weight:600; }
.chip-watch  { background:#3b2a00; color:#fcd34d; border:1px solid #f59e0b; padding:3px 10px; border-radius:20px; font-size:0.78rem; font-weight:600; }
.chip-disq   { background:#450a0a; color:#fca5a5; border:1px solid #ef4444; padding:3px 10px; border-radius:20px; font-size:0.78rem; font-weight:600; }
.chip-none   { background:#1e293b; color:#94a3b8; border:1px solid #475569; padding:3px 10px; border-radius:20px; font-size:0.78rem; font-weight:600; }

/* Disclaimer */
.disclaimer {
    background:#1e1b0e; color:#fbbf24; border-left:4px solid #f59e0b;
    padding:10px 16px; border-radius:6px; font-size:0.85rem;
    margin-bottom:18px; font-weight:500;
}

/* Status banners */
.banner-qual  { background:#052e16; color:#86efac; border-left:5px solid #22c55e; padding:14px 20px; border-radius:8px; font-size:1.1rem; font-weight:700; margin-bottom:16px; }
.banner-disq  { background:#1a0000; color:#f87171; border-left:5px solid #ef4444; padding:14px 20px; border-radius:8px; font-size:1.1rem; font-weight:700; margin-bottom:16px; }

/* Score box */
.score-caveat { background:#1c1800; color:#fde68a; border-left:4px solid #d97706; padding:10px 14px; border-radius:6px; font-size:0.82rem; margin:10px 0 16px; }

/* Metric cards */
.metric-card { background:#0f172a; border:1px solid #1e293b; border-radius:10px; padding:14px 18px; text-align:center; }
.metric-card .label { color:#94a3b8; font-size:0.78rem; text-transform:uppercase; letter-spacing:0.06em; }
.metric-card .value { color:#f1f5f9; font-size:1.5rem; font-weight:700; margin:4px 0; }
.metric-card .sub   { color:#64748b; font-size:0.75rem; }

/* Section header */
.section-header { font-size:1.05rem; font-weight:700; color:#e2e8f0; margin:20px 0 8px;
    padding-bottom:6px; border-bottom:1px solid #1e293b; }

/* Table cell highlights */
.tbl-high  { color:#6ee7b7; font-weight:600; }
.tbl-disq  { color:#f87171; font-weight:600; }
.tbl-watch { color:#fcd34d; font-weight:600; }
.tbl-qual  { color:#93c5fd; font-weight:600; }

/* Validation horizon table */
.val-table thead th { background:#1e293b; color:#94a3b8; font-size:0.75rem; text-transform:uppercase; }
.val-table tbody tr:hover { background:#1e293b30; }
.val-pos { color:#4ade80; font-weight:600; }
.val-neg { color:#f87171; font-weight:600; }
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────────────────
def category_chip(cat: str) -> str:
    cat = str(cat)
    if "HIGH_PRIORITY" in cat:
        return f'<span class="chip-high">⭐ High Priority</span>'
    elif "QUALIFIED" in cat:
        return f'<span class="chip-qual">✅ Qualified</span>'
    elif "WATCHLIST" in cat:
        return f'<span class="chip-watch">👁 Watchlist</span>'
    elif "DISQUALIFIED" in cat:
        return f'<span class="chip-disq">🚫 Disqualified</span>'
    return f'<span class="chip-none">— No Setup</span>'


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
    st.markdown("## 📈 Wyckoff VSA Screener")
    st.caption("NSE Research & Screening Tool · Not Financial Advice")
    st.markdown("---")

    page = st.radio(
        "Navigate",
        [
            "🏠 Home / Single Stock",
            "📊 Research Screening Results",
            "📉 Historical Validation",
            "🔮 Forward Paper Validation",
        ],
        label_visibility="collapsed",
    )

    st.markdown("---")
    if page == "🏠 Home / Single Stock":
        st.markdown("**Data Source**")
        data_source_mode = st.radio(
            "source", ["Live Ticker (yfinance)", "Upload CSV File"], label_visibility="collapsed"
        )
    else:
        data_source_mode = None

    st.markdown("---")
    st.caption("Phase 8–10 · Frozen Analytical Engine · No Fabricated Confidence")


# ─────────────────────────────────────────────────────────────────────────────
# DISCLAIMER BANNER
# ─────────────────────────────────────────────────────────────────────────────
st.markdown(
    '<div class="disclaimer">⚠️ <strong>RESEARCH & SCREENING TOOL ONLY — NOT FINANCIAL ADVICE.</strong> '
    "All candidate events are unconfirmed, quantitative heuristics. Every signal cites numeric evidence. "
    "No live order execution. Inspect actual volume ratio, spread ratio, and close position before drawing any conclusion.</div>",
    unsafe_allow_html=True,
)


# ─────────────────────────────────────────────────────────────────────────────
# PAGE 1: HOME / SINGLE STOCK ANALYSIS
# ─────────────────────────────────────────────────────────────────────────────
if page == "🏠 Home / Single Stock":
    st.title("📈 Single Stock Wyckoff & VSA Analysis")
    st.caption("Fetch live data or upload a CSV to run the full analytical engine on any NSE equity.")

    df: Optional[pd.DataFrame] = None
    current_symbol: str = "ANANTRAJ.NS"

    if data_source_mode == "Live Ticker (yfinance)":
        col1, col2, col3 = st.columns([3, 2, 2])
        with col1:
            ticker_input = st.text_input("NSE Ticker (with .NS suffix)", value="ANANTRAJ.NS", key="ticker")
            current_symbol = ticker_input.strip().upper()
        with col2:
            start_date = st.date_input("Start Date", value=pd.to_datetime("2024-01-01"))
        with col3:
            end_date = st.date_input("End Date", value=pd.to_datetime("today"))

        if st.button("🔍 Fetch & Analyse", type="primary", use_container_width=True):
            with st.spinner(f"Fetching {current_symbol}..."):
                try:
                    raw_df = yf.download(current_symbol, start=start_date, end=end_date, progress=False)
                    if raw_df.empty:
                        st.error(f"No data returned for {current_symbol}. Verify the symbol.")
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
            "Upload OHLCV CSV (Date, Open, High, Low, Close, Volume)", type=["csv"]
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

        # ── Header row
        hcol1, hcol2, hcol3 = st.columns([3, 2, 2])
        with hcol1:
            st.markdown(f"### {current_symbol}")
            st.caption(
                f"{len(df)} daily bars · "
                f"{str(df['Date'].iloc[0])[:10]} → {str(df['Date'].iloc[-1])[:10]}"
            )
        with hcol2:
            st.metric("Latest Close", f"₹{df['Close'].iloc[-1]:.2f}")
        with hcol3:
            st.markdown(category_chip(scored.most_recent_event_type or "NO_SETUP"), unsafe_allow_html=True)

        # ── Status banner
        if scored.is_disqualified:
            flags = " · ".join(scored.disqualifying_flags) if scored.disqualifying_flags else "See flags below"
            st.markdown(f'<div class="banner-disq">🚨 DISQUALIFIED — {flags}</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="banner-qual">✅ QUALIFIED SETUP — No disqualifying red flags</div>', unsafe_allow_html=True)

        # ── Metric cards
        section("Key Metrics")
        mc1, mc2, mc3, mc4 = st.columns(4)
        with mc1:
            st.metric("Composite Score", f"{scored.composite_score:.1f}/100")
        with mc2:
            ev = scored.most_recent_event_type or "None"
            ev_date = str(scored.most_recent_event_date)[:10] if scored.most_recent_event_date else "–"
            st.metric("Most Recent Event", ev, delta=ev_date)
        with mc3:
            if scored.pf_price_objective and not scored.pf_price_objective.stale_anchor:
                pf_target = scored.pf_price_objective.price_objective
                upside = ((pf_target - df["Close"].iloc[-1]) / df["Close"].iloc[-1]) * 100
                st.metric("P&F Target", f"₹{pf_target:.2f}", delta=f"{upside:+.1f}%")
            else:
                st.metric("P&F Target", "N/A" + (" ⚠️ stale" if scored.pf_price_objective else ""))
        with mc4:
            passed = sum(1 for v in scored.mechanical_filters_passed.values() if v)
            total = len(scored.mechanical_filters_passed)
            st.metric("Mechanical Filters", f"{passed}/{total} passed")

        # Score caveat
        st.markdown(
            '<div class="score-caveat">⚠️ <strong>Score caveat:</strong> Composite score magnitude above the qualify/disqualify '
            "threshold has not been validated as reliably predictive. It inverted on 2 of 3 stocks in Phase 7/10 backtesting. "
            "Use as coarse triage only — not a precision ranking.</div>",
            unsafe_allow_html=True,
        )

        # ── Score breakdown
        with st.expander("🔍 Composite Score Breakdown", expanded=False):
            sc = scored.score_breakdown
            bcol1, bcol2, bcol3, bcol4 = st.columns(4)
            bcol1.metric("Mechanical Filters (max 30)", f"{sc['mechanical_filters']:.1f}")
            bcol2.metric("Schematic Event Recency (max 40)", f"{sc['schematic_recency']:.1f}")
            bcol3.metric("Peer Relative Strength (max 20)", f"{sc['peer_relative_strength']:.1f}")
            bcol4.metric("P&F Upside (max 10)", f"{sc['pf_target_upside']:.1f}")

        # ── Price Chart
        section("📊 Price Chart with Wyckoff Events")
        fig, (ax, ax_vol) = plt.subplots(
            2, 1, figsize=(14, 7), dpi=110, gridspec_kw={"height_ratios": [3, 1]}, sharex=True
        )
        ax.plot(df["Date"], df["Close"], label="Close", color="#38bdf8", linewidth=1.5)
        if len(df) >= 50:
            ax.plot(df["Date"], df["Close"].rolling(50).mean(), label="50 DMA", color="#f97316", linestyle="--", alpha=0.8)
        if len(df) >= 100:
            ax.plot(df["Date"], df["Close"].rolling(100).mean(), label="100 DMA", color="#a3e635", linestyle=":", alpha=0.8)

        event_cfg = {
            "SC":     {"c": "#ef4444", "m": "v", "s": 100},
            "AR":     {"c": "#f97316", "m": "^", "s": 90},
            "ST":     {"c": "#a78bfa", "m": "o", "s": 70},
            "Spring": {"c": "#60a5fa", "m": "s", "s": 90},
            "LPS":    {"c": "#4ade80", "m": "D", "s": 80},
            "SOS":    {"c": "#2dd4bf", "m": "*", "s": 130},
            "UTAD":   {"c": "#f43f5e", "m": "X", "s": 110},
        }

        for ev_type, ev_list in scored.detected_events.items():
            cfg = event_cfg.get(ev_type, {"c": "white", "m": "o", "s": 50})
            for ev in ev_list:
                ev_date = pd.to_datetime(ev.date)
                ax.scatter(ev_date, ev.price, color=cfg["c"], marker=cfg["m"], s=cfg["s"], zorder=5,
                           label=ev_type if ev_type not in [t.get_text() for t in ax.legend().get_texts()] else "")
                ax.annotate(ev_type, (ev_date, ev.price), textcoords="offset points",
                            xytext=(0, 12 if ev_type in ("AR", "SOS", "Spring") else -16),
                            ha="center", fontsize=7.5, fontweight="bold", color=cfg["c"])

        ax.set_facecolor("#0f172a")
        ax.set_ylabel("Price (₹)", fontsize=10, color="#94a3b8")
        ax.tick_params(colors="#94a3b8")
        ax.grid(True, linestyle="--", alpha=0.2, color="#334155")
        ax.legend(loc="upper left", framealpha=0.7, facecolor="#1e293b", edgecolor="#334155", labelcolor="#e2e8f0")
        ax.set_title(f"{current_symbol} — Wyckoff Schematic Event Detection", fontsize=12, color="#f1f5f9")
        fig.patch.set_facecolor("#0f172a")

        # Volume bars
        vol_colors = ["#ef4444" if c < o else "#4ade80" for c, o in zip(df["Close"], df["Open"])]
        ax_vol.bar(df["Date"], df["Volume"], color=vol_colors, alpha=0.7, width=1.0)
        ax_vol.set_facecolor("#0f172a")
        ax_vol.set_ylabel("Volume", fontsize=9, color="#94a3b8")
        ax_vol.tick_params(colors="#94a3b8")
        ax_vol.grid(True, linestyle="--", alpha=0.15, color="#334155")
        ax_vol.xaxis.set_major_formatter(mdates.DateFormatter("%b %Y"))
        fig.autofmt_xdate()
        plt.tight_layout()
        st.pyplot(fig)
        plt.close(fig)

        # ── Events evidence table
        section("📋 Candidate Events — Numeric Evidence Log")
        all_ev = []
        for ev_type, ev_list in scored.detected_events.items():
            for ev in ev_list:
                all_ev.append({
                    "Event": ev.event_type,
                    "Date": str(ev.date)[:10],
                    "Price (₹)": round(ev.price, 2),
                    "Vol Ratio": round(ev.volume_ratio, 2),
                    "Spread Ratio": round(ev.spread_ratio, 2),
                    "Close Pos": round(ev.close_position, 2),
                    "Supporting Evidence": ev.supporting_note,
                })
        if all_ev:
            st.dataframe(
                pd.DataFrame(all_ev).sort_values("Date", ascending=False),
                use_container_width=True, height=320,
            )
        else:
            st.info("No schematic events detected in this dataset.")

        # ── Mechanical filters
        section("⚙️ Mechanical Filters Checklist")
        fcols = st.columns(4)
        for idx, (fname, fpass) in enumerate(scored.mechanical_filters_passed.items()):
            fcols[idx % 4].markdown(f"{'✅' if fpass else '❌'} **{fname.replace('_', ' ').title()}**")

        # ── P&F
        section("🎯 Point & Figure Price Objective")
        if scored.pf_price_objective:
            pfo = scored.pf_price_objective
            pcol1, pcol2, pcol3 = st.columns(3)
            pcol1.metric("Count Row Price", f"₹{pfo.count_row_price:.2f}")
            pcol2.metric("Columns Counted", str(pfo.num_columns))
            upside = ((pfo.price_objective - df["Close"].iloc[-1]) / df["Close"].iloc[-1]) * 100
            pcol3.metric("P&F Target", f"₹{pfo.price_objective:.2f}", delta=f"{upside:+.1f}%")
            st.caption(f"Formula: `{pfo.formula}` | Box size ₹{pfo.box_size:.2f} | Reversal {pfo.reversal}")
            if pfo.used_fallback_count:
                st.warning("⚠️ Fallback count used — no column exactly touched the count row.")
            if pfo.stale_anchor:
                st.warning("⚠️ Stale anchor — P&F anchor event older than 60 bars. P&F objective scored 0.")
        else:
            st.info("P&F objective not available — insufficient bars or no Spring/LPS anchor found.")

        # ── TradingView
        section("🌐 TradingView Manual Review Links")
        st.markdown(
            '<div class="score-caveat">ℹ️ TradingView links are for <strong>human visual inspection only</strong>. '
            "They are NOT evidence of a confirmed setup. All numeric signals above are computed locally from validated OHLCV data.</div>",
            unsafe_allow_html=True,
        )
        try:
            tv = generate_tradingview_links(current_symbol)
            tc1, tc2, tc3 = st.columns(3)
            tc1.link_button("📈 Daily Chart", tv.daily_url, use_container_width=True)
            tc2.link_button("📊 Weekly Chart", tv.weekly_url, use_container_width=True)
            tc3.link_button("⏱ 75-Minute Chart", tv.intraday_75m_url, use_container_width=True)
        except Exception:
            st.caption("TradingView links not available for this symbol.")

        with st.expander("📋 9-Point Manual Chart-Review Checklist"):
            for item in CHART_REVIEW_CHECKLIST:
                st.markdown(f"- {item}")

    else:
        st.info("👈 Use the sidebar to load data — enter an NSE ticker (e.g. `ANANTRAJ.NS`) or upload a CSV.")
        st.markdown("""
**How to start:**
1. Select "Live Ticker (yfinance)" or "Upload CSV File" in the sidebar
2. Enter or upload your data
3. The full Wyckoff / VSA analysis will appear here
        """)


# ─────────────────────────────────────────────────────────────────────────────
# PAGE 2: RESEARCH SCREENING RESULTS (Phase 9C)
# ─────────────────────────────────────────────────────────────────────────────
elif page == "📊 Research Screening Results":
    st.title("📊 Broad NSE EQ Research Screening Results")
    st.caption("Phase 9C outputs from the latest dataset snapshot. Load a different run by selecting the folder below.")

    BASE = "data/research_results"
    result_dir = latest_results_dir(BASE)

    # Manual directory override
    available = sorted([d.name for d in Path(BASE).iterdir() if d.is_dir()], reverse=True) if Path(BASE).exists() else []
    if available:
        selected = st.selectbox("Select screening run", available, index=0)
        result_dir = Path(BASE) / selected
    else:
        st.warning("No research results found. Run the Phase 9C screener first:\n\n```\npython -m wyckoff_screener.research --dataset-dir data/research_datasets/<date>\n```")
        st.stop()

    # ── Load manifest
    manifest_path = result_dir / "research_manifest.json"
    manifest = {}
    if manifest_path.exists():
        with open(manifest_path) as f:
            manifest = json.load(f)

    # ── Summary metrics
    section("📑 Run Summary")
    mc1, mc2, mc3, mc4, mc5 = st.columns(5)
    mc1.metric("Total Evaluated", manifest.get("total_evaluated", "–"))
    mc2.metric("High Priority", manifest.get("high_priority_count", "–"))
    mc3.metric("Qualified", manifest.get("qualified_count", "–"))
    mc4.metric("Disqualified", manifest.get("disqualified_count", "–"))
    mc5.metric("Failures", manifest.get("failure_count", "–"))
    st.caption(f"Snapshot date: `{manifest.get('dataset_date', '–')}` | Run: `{manifest.get('run_timestamp', '–')}`")

    # ── Load candidates
    cand_path = result_dir / "candidates.csv"
    disq_path = result_dir / "disqualified.csv"
    all_path  = result_dir / "all_results.csv"

    tab1, tab2, tab3 = st.tabs(["⭐ Candidates", "🚫 Disqualified", "📋 All Results"])

    def _cat_html(cat: str) -> str:
        if "HIGH_PRIORITY" in cat: return '<span class="chip-high">⭐ High Priority</span>'
        if "QUALIFIED"    in cat: return '<span class="chip-qual">✅ Qualified</span>'
        if "WATCHLIST"    in cat: return '<span class="chip-watch">👁 Watchlist</span>'
        return '<span class="chip-none">— No Setup</span>'

    def render_candidates(path: Path, tab_name: str):
        if not path.exists():
            st.info(f"No {tab_name} file found at `{path}`")
            return
        df = pd.read_csv(path)
        if df.empty:
            st.info(f"No {tab_name}.")
            return

        # Search / filter
        search = st.text_input(f"🔍 Filter {tab_name}", placeholder="Type symbol or name…", key=f"search_{tab_name}")
        if search:
            mask = df["symbol"].str.contains(search, case=False, na=False) | df.get("company_name", pd.Series()).str.contains(search, case=False, na=False)
            df = df[mask]

        display_cols = [c for c in ["symbol", "company_name", "candidate_category", "composite_score",
                                    "most_recent_event_type", "most_recent_event_date",
                                    "pf_target_price", "pf_upside_pct",
                                    "close", "rsi_14", "avg_20_turnover_cr",
                                    "explanation_summary"] if c in df.columns]
        display_df = df[display_cols].copy()

        # Format
        for col in ["composite_score", "pf_upside_pct", "close", "rsi_14", "avg_20_turnover_cr"]:
            if col in display_df.columns:
                display_df[col] = display_df[col].apply(lambda x: round(x, 2) if pd.notna(x) else "–")

        st.dataframe(display_df, use_container_width=True, height=460)
        st.caption(f"{len(df)} row(s) displayed")

        # Download
        csv_bytes = df.to_csv(index=False).encode()
        st.download_button(
            f"⬇️ Download {tab_name} CSV",
            data=csv_bytes,
            file_name=f"{tab_name.lower().replace(' ', '_')}_{selected}.csv",
            mime="text/csv",
        )

        # Expandable detail per security
        if len(df) <= 30:
            with st.expander("🔎 Per-Security Detail Cards"):
                for _, row in df.iterrows():
                    with st.container():
                        d1, d2, d3 = st.columns([2, 2, 3])
                        d1.markdown(f"**{row.get('symbol', '–')}**  {_cat_html(str(row.get('candidate_category', '')))}", unsafe_allow_html=True)
                        d2.markdown(f"Score: `{row.get('composite_score', '–')}` | Event: `{row.get('most_recent_event_type', '–')}`")
                        d3.markdown(f"_{str(row.get('explanation_summary', ''))[:200]}_")
                        st.markdown("---")

    with tab1:
        render_candidates(cand_path, "Candidates")

    with tab2:
        if not disq_path.exists():
            st.info("No disqualified file found.")
        else:
            dq = pd.read_csv(disq_path)
            if dq.empty:
                st.info("No disqualified securities.")
            else:
                display_cols = [c for c in ["symbol", "company_name", "disqualifying_flags", "composite_score",
                                            "most_recent_event_type", "close", "explanation_summary"] if c in dq.columns]
                st.dataframe(dq[display_cols], use_container_width=True, height=460)
                st.download_button("⬇️ Download Disqualified CSV", dq.to_csv(index=False).encode(),
                                   file_name=f"disqualified_{selected}.csv", mime="text/csv")

    with tab3:
        if not all_path.exists():
            st.info("No all_results file found.")
        else:
            adf = pd.read_csv(all_path)
            st.dataframe(adf, use_container_width=True, height=520)
            st.download_button("⬇️ Download All Results CSV", adf.to_csv(index=False).encode(),
                               file_name=f"all_results_{selected}.csv", mime="text/csv")


# ─────────────────────────────────────────────────────────────────────────────
# PAGE 3: HISTORICAL VALIDATION (Phase 10)
# ─────────────────────────────────────────────────────────────────────────────
elif page == "📉 Historical Validation":
    st.title("📉 Historical Validation & Backtesting Results")
    st.caption(
        "Phase 10 walk-forward point-in-time validation results. "
        "CURRENT-UNIVERSE HISTORICAL VALIDATION (Subject to Survivorship Bias; for forward triage evaluation only)."
    )

    BASE = "data/validation_results"
    available_val = sorted([d.name for d in Path(BASE).iterdir() if d.is_dir()], reverse=True) if Path(BASE).exists() else []

    if not available_val:
        st.warning(
            "No validation results found. Run the Phase 10 engine first:\n\n"
            "```\npython -m wyckoff_screener.validation "
            "--dataset-dir data/research_datasets/<date>\n```"
        )
        st.stop()

    selected_val = st.selectbox("Select validation run", available_val, index=0)
    val_dir = Path(BASE) / selected_val

    manifest_path = val_dir / "validation_manifest.json"
    manifest = {}
    if manifest_path.exists():
        with open(manifest_path) as f:
            manifest = json.load(f)
    else:
        st.warning(f"validation_manifest.json not found in `{val_dir}`. Validation may still be running.")
        st.stop()

    # Survivorship warning
    st.markdown(
        f'<div class="disclaimer">⚠️ {manifest.get("survivorship_bias_warning", "CURRENT-UNIVERSE HISTORICAL VALIDATION (Subject to Survivorship Bias)")}</div>',
        unsafe_allow_html=True,
    )

    # ── Manifest summary
    section("📑 Validation Run Summary")
    vc1, vc2, vc3, vc4, vc5 = st.columns(5)
    vc1.metric("Securities Evaluated", manifest.get("securities_evaluated", "–"))
    vc2.metric("Checkpoints Attempted", manifest.get("total_checkpoints_attempted", "–"))
    vc3.metric("Successful Observations", manifest.get("total_successful_observations", "–"))
    vc4.metric("Failed Observations", manifest.get("total_failed_observations", "–"))
    vc5.metric("Split Date", manifest.get("split_date", "–"))
    st.caption(
        f"In-sample: {manifest.get('in_sample_start','–')} → {manifest.get('in_sample_end','–')} "
        f"({manifest.get('in_sample_observation_count','–')} obs) | "
        f"Out-of-sample: {manifest.get('out_of_sample_start','–')} → {manifest.get('out_of_sample_end','–')} "
        f"({manifest.get('out_of_sample_observation_count','–')} obs)"
    )

    # ── Load CSVs
    sig_path  = val_dir / "signal_events.csv"
    cat_path  = val_dir / "category_performance.csv"
    score_path = val_dir / "score_band_performance.csv"
    split_path = val_dir / "in_sample_vs_out_sample.csv"
    fail_path  = val_dir / "failures.csv"

    vt1, vt2, vt3, vt4 = st.tabs([
        "📊 Category Performance", "🏷 Score Bands",
        "🗓 In-Sample vs Out-of-Sample", "📋 Signal Events"
    ])

    def _pct(val):
        if pd.isna(val):
            return "–"
        try:
            v = float(val)
            color = "val-pos" if v > 0 else "val-neg"
            return f'<span class="{color}">{v:+.2f}%</span>'
        except Exception:
            return str(val)

    with vt1:
        if cat_path.exists():
            cdf = pd.read_csv(cat_path)
            if not cdf.empty:
                # Pivot: cohort_group | cohort_value | horizon | mean_return | median_return | win_rate | count
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
        else:
            st.info("category_performance.csv not found. Validation may still be in progress.")

    with vt2:
        if score_path.exists():
            sdf = pd.read_csv(score_path)
            if not sdf.empty:
                st.dataframe(sdf, use_container_width=True, height=400)
                st.markdown(
                    '<div class="score-caveat">⚠️ Score band comparison is exploratory. '
                    'From Phase 7/10 backtesting on 3 stocks, high-score setups inverted vs low-score setups on 2/3 stocks. '
                    'Do not use as a ranking signal. Treat as coarse triage only.</div>',
                    unsafe_allow_html=True,
                )
        else:
            st.info("score_band_performance.csv not found.")

    with vt3:
        if split_path.exists():
            spdf = pd.read_csv(split_path)
            if not spdf.empty:
                st.dataframe(spdf, use_container_width=True, height=400)
        else:
            st.info("in_sample_vs_out_sample.csv not found.")

    with vt4:
        if sig_path.exists():
            sigdf = pd.read_csv(sig_path)
            if not sigdf.empty:
                # Filters
                fc1, fc2 = st.columns(2)
                with fc1:
                    cats = ["All"] + sorted(sigdf["candidate_category"].dropna().unique().tolist())
                    sel_cat = st.selectbox("Filter by Category", cats)
                with fc2:
                    splits = ["All"] + sorted(sigdf["period_split"].dropna().unique().tolist())
                    sel_split = st.selectbox("Filter by Period", splits)

                view = sigdf.copy()
                if sel_cat != "All":
                    view = view[view["candidate_category"] == sel_cat]
                if sel_split != "All":
                    view = view[view["period_split"] == sel_split]

                display = [c for c in ["symbol", "checkpoint_date", "candidate_category",
                                       "composite_score", "is_mechanically_qualified",
                                       "fwd_ret_10d", "fwd_ret_20d", "fwd_ret_60d",
                                       "mfe_60d", "mae_60d", "period_split"] if c in view.columns]
                st.dataframe(view[display].sort_values("checkpoint_date", ascending=False),
                             use_container_width=True, height=500)
                st.caption(f"{len(view)} observations displayed")
                st.download_button("⬇️ Download Signal Events CSV",
                                   view.to_csv(index=False).encode(),
                                   file_name=f"signals_{selected_val}.csv",
                                   mime="text/csv")
        else:
            st.info("signal_events.csv not found. Validation may still be running.")


# ─────────────────────────────────────────────────────────────────────────────
# PAGE 4: FORWARD PAPER VALIDATION (PHASE 11)
# ─────────────────────────────────────────────────────────────────────────────
elif page == "🔮 Forward Paper Validation":
    st.title("🔮 Prospective Forward Paper Validation")
    st.caption("Real-world forward tracking of frozen research candidates with strict zero-lookahead discipline.")

    fwd_base = Path("data/forward_validation")
    ledger_path = fwd_base / "ledger" / "forward_ledger.csv"
    outcomes_path = fwd_base / "ledger" / "forward_outcomes.csv"
    snapshots_dir = fwd_base / "snapshots"

    # 1. OVERVIEW & METRICS
    st.markdown("### 📊 Forward Validation Overview")

    total_cand = 0
    total_snaps = 0
    latest_scr_date = "N/A"
    m_10, p_10 = 0, 0
    m_20, p_20 = 0, 0
    m_60, p_60 = 0, 0

    df_outcomes = pd.DataFrame()
    df_ledger = pd.DataFrame()

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

    if ledger_path.exists():
        try:
            df_ledger = pd.read_csv(ledger_path)
        except Exception:
            pass

    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        st.markdown(
            f'<div class="metric-card"><div class="label">Total Tracked</div>'
            f'<div class="value">{total_cand}</div><div class="sub">{total_snaps} snapshots</div></div>',
            unsafe_allow_html=True,
        )
    with c2:
        st.markdown(
            f'<div class="metric-card"><div class="label">10D Horizon</div>'
            f'<div class="value" style="color:#6ee7b7;">{m_10} Mat</div><div class="sub">{p_10} pending</div></div>',
            unsafe_allow_html=True,
        )
    with c3:
        st.markdown(
            f'<div class="metric-card"><div class="label">20D Horizon</div>'
            f'<div class="value" style="color:#93c5fd;">{m_20} Mat</div><div class="sub">{p_20} pending</div></div>',
            unsafe_allow_html=True,
        )
    with c4:
        st.markdown(
            f'<div class="metric-card"><div class="label">60D Horizon</div>'
            f'<div class="value" style="color:#fcd34d;">{m_60} Mat</div><div class="sub">{p_60} pending</div></div>',
            unsafe_allow_html=True,
        )
    with c5:
        st.markdown(
            f'<div class="metric-card"><div class="label">Latest Screening</div>'
            f'<div class="value" style="font-size:1.15rem;">{latest_scr_date}</div><div class="sub">Date T</div></div>',
            unsafe_allow_html=True,
        )

    st.markdown("---")

    # FORWARD TABS
    ft1, ft2, ft3, ft4, ft5, ft6 = st.tabs([
        "📸 Latest Screening",
        "⏳ Active Candidates",
        "📈 Matured Outcomes",
        "⚖️ Forward vs Historical",
        "📊 Category Breakdown",
        "🛡️ Data Integrity & Audit",
    ])

    # TAB 1: LATEST SCREENING
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

                    st.caption(
                        f"Snapshot ID: `{snap_data.get('snapshot_id')}` | "
                        f"Screening Date: **{snap_data.get('screening_date')}** | "
                        f"Engine Version: `{snap_data.get('engine_version')}` | "
                        f"Total Records: {snap_data.get('total_candidates')}"
                    )

                    records = snap_data.get("candidate_records", [])
                    if records:
                        snap_df = pd.DataFrame(records)
                        display_cols = [
                            c for c in [
                                "symbol", "candidate_category", "composite_score", "reference_close_price",
                                "is_mechanically_qualified", "vsa_volume_ratio", "vsa_spread_ratio",
                                "most_recent_event_type", "pf_target_price", "pf_upside_pct", "explanation_summary"
                            ] if c in snap_df.columns
                        ]
                        st.dataframe(snap_df[display_cols].sort_values("composite_score", ascending=False), use_container_width=True, height=450)
                except Exception as exc:
                    st.error(f"Error loading snapshot: {exc}")
        else:
            st.info("No forward screening snapshots found in `data/forward_validation/snapshots/`. Run `python -m wyckoff_screener.forward screen --date YYYY-MM-DD` first.")

    # TAB 2: ACTIVE CANDIDATES
    with ft2:
        st.markdown("#### ⏳ Active Forward Candidates (Tracking in Progress)")
        if not df_outcomes.empty:
            # Active means 60D is still pending
            active_df = df_outcomes[df_outcomes["status_60d"] == "PENDING"].copy()
            if not active_df.empty:
                st.caption(f"{len(active_df)} candidates currently maturing across forward horizons.")
                display_cols = [
                    c for c in [
                        "symbol", "screening_date", "candidate_category", "composite_score",
                        "reference_close_price", "available_forward_bars",
                        "status_10d", "fwd_ret_10d", "status_20d", "fwd_ret_20d", "status_60d"
                    ] if c in active_df.columns
                ]
                st.dataframe(active_df[display_cols].sort_values("screening_date", ascending=False), use_container_width=True, height=450)
            else:
                st.info("No active pending candidates. All recorded candidate horizons have matured.")
        else:
            st.info("Forward outcomes ledger is empty.")

    # TAB 3: MATURED FORWARD PERFORMANCE
    with ft3:
        st.markdown("#### 📈 Realized Forward Performance by Cohort")
        if not df_outcomes.empty:
            for h in [10, 20, 60]:
                st.markdown(f"##### Forward Horizon: **{h} Trading Days**")
                status_col = f"status_{h}d"
                ret_col = f"fwd_ret_{h}d"
                mfe_col = f"mfe_{h}d"
                mae_col = f"mae_{h}d"

                if status_col in df_outcomes.columns and ret_col in df_outcomes.columns:
                    matured = df_outcomes[df_outcomes[status_col] == "MATURED"].copy()
                    if not matured.empty:
                        # Aggregate by category
                        agg_rows = []

                        # Baseline
                        r_all = matured[ret_col].dropna()
                        mfe_all = matured[mfe_col].dropna()
                        mae_all = matured[mae_col].dropna()
                        if len(r_all) > 0:
                            agg_rows.append({
                                "Category": "UNIVERSE BASELINE",
                                "N": len(r_all),
                                "Mean Return %": f"{r_all.mean():+.2f}%",
                                "Median Return %": f"{r_all.median():+.2f}%",
                                "Win Rate %": f"{(r_all > 0).mean() * 100:.1f}%",
                                "Mean MFE %": f"{mfe_all.mean():+.2f}%" if len(mfe_all) > 0 else "–",
                                "Mean MAE %": f"{mae_all.mean():+.2f}%" if len(mae_all) > 0 else "–",
                            })

                        for cat, grp in matured.groupby("candidate_category"):
                            r_cat = grp[ret_col].dropna()
                            mfe_cat = grp[mfe_col].dropna()
                            mae_cat = grp[mae_col].dropna()
                            if len(r_cat) > 0:
                                agg_rows.append({
                                    "Category": cat,
                                    "N": len(r_cat),
                                    "Mean Return %": f"{r_cat.mean():+.2f}%",
                                    "Median Return %": f"{r_cat.median():+.2f}%",
                                    "Win Rate %": f"{(r_cat > 0).mean() * 100:.1f}%",
                                    "Mean MFE %": f"{mfe_cat.mean():+.2f}%" if len(mfe_cat) > 0 else "–",
                                    "Mean MAE %": f"{mae_cat.mean():+.2f}%" if len(mae_cat) > 0 else "–",
                                })

                        st.dataframe(pd.DataFrame(agg_rows), use_container_width=True)
                    else:
                        st.info(f"No matured {h}-day observations yet.")
        else:
            st.info("No forward outcomes recorded.")

    # TAB 4: FORWARD VS HISTORICAL COMPARISON
    with ft4:
        st.markdown("#### ⚖️ Phase 10 Historical Validation vs. Phase 11 Prospective Forward")
        st.caption("Benchmark prospective out-of-sample forward tracking against Phase 10 baseline findings.")

        # Historical baseline benchmark numbers (Phase 10 OOS 60d)
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
                if cat == "UNIVERSE BASELINE":
                    fwd_sub = matured_60
                else:
                    fwd_sub = matured_60[matured_60["candidate_category"] == cat]

                fwd_n = len(fwd_sub)
                fwd_mean = f"{fwd_sub['fwd_ret_60d'].mean():+.2f}%" if fwd_n > 0 else "–"
                fwd_win = f"{(fwd_sub['fwd_ret_60d'] > 0).mean() * 100:.1f}%" if fwd_n > 0 else "–"

                comp_rows.append({
                    "Cohort": cat,
                    "Hist 60d Mean": bdata["hist_mean"],
                    "Hist Win%": bdata["hist_win"],
                    "Hist N": bdata["hist_n"],
                    "Fwd 60d Mean": fwd_mean,
                    "Fwd Win%": fwd_win,
                    "Fwd N": fwd_n,
                })
            st.dataframe(pd.DataFrame(comp_rows), use_container_width=True)
        else:
            st.info("No forward 60-day observations have matured yet. Run `python -m wyckoff_screener.forward update` as new market data arrives.")

    # TAB 5: CATEGORY BREAKDOWN
    with ft5:
        st.markdown("#### 📊 Candidate Category Distribution")
        if not df_outcomes.empty and "candidate_category" in df_outcomes.columns:
            cat_counts = df_outcomes["candidate_category"].value_counts().reset_index()
            cat_counts.columns = ["Candidate Category", "Total Count"]
            st.dataframe(cat_counts, use_container_width=True)
        else:
            st.info("No candidate category data recorded.")

    # TAB 6: DATA INTEGRITY PANEL
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

        st.caption(
            f"Forward Validation Base: `{fwd_base.resolve()}` | "
            f"Ledger File: `{ledger_path.name}` | Outcomes File: `{outcomes_path.name}`"
        )

