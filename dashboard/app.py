"""Wyckoff Method + VSA Screener & Research Dashboard (Streamlit).

Guiding Principles (AGENTS.md):
- No Fabricated Confidence: Every flagged event cites specific numbers.
- Candidates, Never Certainties: Signals are candidate schematic events.
- Research & Screening Tool Only: No live order execution.
"""

from typing import Any, Optional
import sys, os

# Ensure src/ is on the path when running via `streamlit run dashboard/app.py`
# both locally and on Streamlit Community Cloud
_src_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src")
if _src_path not in sys.path:
    sys.path.insert(0, _src_path)

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st
import yfinance as yf


from wyckoff_screener.data_loader import validate_ohlcv_dataframe
from wyckoff_screener.pointfigure.pf_chart import build_point_and_figure_chart, count_price_objective
from wyckoff_screener.scoring.setup_scorer import score_setup
from wyckoff_screener.wyckoff.schematic_events import detect_all_schematic_events

# Page Configuration
st.set_page_config(
    page_title="Wyckoff & VSA Research Screener (NSE)",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom Styling
st.markdown(
    """
    <style>
    .disclaimer-banner {
        background-color: #ffebe6;
        color: #bf2600;
        padding: 12px 16px;
        border-radius: 6px;
        border-left: 5px solid #ff5630;
        font-weight: 500;
        margin-bottom: 20px;
    }
    .metric-box {
        background-color: #f4f5f7;
        padding: 16px;
        border-radius: 8px;
        border: 1px solid #dfe1e6;
    }
    .red-flag-box {
        background-color: #fff0f0;
        color: #de350b;
        padding: 12px 16px;
        border-radius: 6px;
        border: 1px solid #ff8f73;
        margin-bottom: 15px;
    }
    .status-qualified {
        background-color: #e3fcef;
        color: #006644;
        padding: 14px 20px;
        border-radius: 8px;
        border-left: 6px solid #00875a;
        font-size: 1.2rem;
        font-weight: 700;
        margin-bottom: 18px;
    }
    .status-disqualified {
        background-color: #ffebe6;
        color: #bf2600;
        padding: 14px 20px;
        border-radius: 8px;
        border-left: 6px solid #de350b;
        font-size: 1.2rem;
        font-weight: 700;
        margin-bottom: 18px;
    }
    .score-caveat {
        background-color: #fffae6;
        color: #7a5100;
        padding: 10px 14px;
        border-radius: 6px;
        border-left: 4px solid #f0c400;
        font-size: 0.85rem;
        margin-top: 10px;
        margin-bottom: 16px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# Persistent Mandatory Disclaimer Banner (AGENTS.md)
st.markdown(
    """
    <div class="disclaimer-banner">
        ⚠️ <strong>RESEARCH & SCREENING TOOL ONLY:</strong> Not financial advice. No live order execution.
        All flagged schematic events and phases are <em>unconfirmed candidates</em> based on quantitative heuristics.
        Always inspect the specific numeric evidence (volume ratio, spread ratio, close position) before drawing conclusions.
    </div>
    """,
    unsafe_allow_html=True,
)

st.title("📈 Wyckoff Method & Volume Spread Analysis Screener")
st.caption("Quantitative Wyckoff Phase & Event Detection for NSE-Listed Indian Equities")

# -------------------------------------------------------------
# Sidebar: Data Source & Inputs
# -------------------------------------------------------------
st.sidebar.header("Data Source")
data_source_mode = st.sidebar.radio("Select Data Source:", ["Live Ticker (yfinance)", "Upload CSV File"])

df: Optional[pd.DataFrame] = None
current_symbol: str = "ANANTRAJ.NS"

if data_source_mode == "Live Ticker (yfinance)":
    ticker_input = st.sidebar.text_input("NSE Ticker (with .NS suffix):", value="ANANTRAJ.NS")
    current_symbol = ticker_input.strip().upper()
    start_date = st.sidebar.date_input("Start Date", value=pd.to_datetime("2024-01-01"))
    end_date = st.sidebar.date_input("End Date", value=pd.to_datetime("today"))

    if st.sidebar.button("Fetch & Analyze", type="primary"):
        with st.spinner(f"Fetching {current_symbol} historical data..."):
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
    uploaded_file = st.sidebar.file_uploader("Upload OHLCV CSV (Date, Open, High, Low, Close, Volume):", type=["csv"])
    if uploaded_file is not None:
        try:
            raw_df = pd.read_csv(uploaded_file)
            df = validate_ohlcv_dataframe(raw_df)
            current_symbol = uploaded_file.name.replace(".csv", "").upper()
            st.session_state["loaded_df"] = df
            st.session_state["symbol"] = current_symbol
        except Exception as exc:
            st.error(f"CSV Validation Error: {exc}")

# Retrieve state if available
if "loaded_df" in st.session_state:
    df = st.session_state["loaded_df"]
    current_symbol = st.session_state.get("symbol", current_symbol)

# -------------------------------------------------------------
# Main Analysis Dashboard
# -------------------------------------------------------------
if df is not None and not df.empty:
    st.subheader(f"Analysis Summary for {current_symbol}")
    st.write(f"Dataset: **{len(df)} daily bars** from **{df['Date'].iloc[0].strftime('%Y-%m-%d')}** to **{df['Date'].iloc[-1].strftime('%Y-%m-%d')}** | Latest Close: **₹{df['Close'].iloc[-1]:.2f}**")

    # Run Scoring Engine
    scored = score_setup(df, symbol=current_symbol)

    # ── PRIMARY STATUS BANNER (leads the UI) ──────────────────────
    if scored.is_disqualified:
        flag_text = " &nbsp;|&nbsp; ".join(scored.disqualifying_flags) if scored.disqualifying_flags else "See flags below"
        st.markdown(
            f'<div class="status-disqualified">🚨 RED FLAG — DISQUALIFIED &nbsp;·&nbsp; <span style="font-weight:400;font-size:0.9rem">{flag_text}</span></div>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            '<div class="status-qualified">✅ QUALIFIED SETUP — No disqualifying flags detected</div>',
            unsafe_allow_html=True,
        )

    # ── SUPPORTING METRICS (secondary to status) ──────────────────
    m1, m2, m3 = st.columns(3)
    with m1:
        st.metric(
            label="Most Recent Event",
            value=scored.most_recent_event_type or "None",
            delta=str(scored.most_recent_event_date)[:10] if scored.most_recent_event_date else None,
        )
    with m2:
        if scored.pf_price_objective:
            upside = ((scored.pf_price_objective.price_objective - df['Close'].iloc[-1]) / df['Close'].iloc[-1]) * 100.0
            pf_label = "P&F Price Objective" + (" ⚠️ stale" if scored.pf_price_objective.stale_anchor else "")
            st.metric(
                label=pf_label,
                value=f"₹{scored.pf_price_objective.price_objective:.2f}",
                delta=f"{upside:+.1f}% upside",
            )
        else:
            st.metric(label="P&F Price Objective", value="N/A")
    with m3:
        peer_note = "(skipped — no peer data)" if scored.peer_analysis_skipped else ""
        st.metric(
            label="Peer Analysis",
            value=f"Rank #{scored.peer_rank}" if scored.peer_rank else f"Not run {peer_note}",
        )

    # ── COMPOSITE SCORE (de-emphasised — supporting detail only) ──
    st.markdown("#### 🔍 Composite Score — Supporting Detail")
    sb_cols = st.columns(5)
    sb_cols[0].metric("Total Score", f"{scored.composite_score:.1f} / 100")
    sb_cols[1].write(f"**Mechanical Filters (max 30):** {scored.score_breakdown['mechanical_filters']:.1f}")
    sb_cols[2].write(f"**Schematic Event Recency (max 40):** {scored.score_breakdown['schematic_recency']:.1f}")
    sb_cols[3].write(f"**Peer Relative Strength (max 20):** {scored.score_breakdown['peer_relative_strength']:.1f}")
    sb_cols[4].write(f"**P&F Upside (max 10):** {scored.score_breakdown['pf_target_upside']:.1f}")
    st.markdown(
        '<div class="score-caveat">'
        '⚠️ <strong>Validation caveat:</strong> Composite score ranking has not been validated as reliable '
        'above the qualify/disqualify threshold — in Phase 7 backtesting it inverted on 2 of 3 stocks at the 60-bar horizon. '
        'Treat as supporting evidence, not a ranking you can trust to pick the best of several qualified setups. '
        'See <code>AGENTS.md § Validated Findings</code> for details.'
        '</div>',
        unsafe_allow_html=True,
    )

    # -------------------------------------------------------------
    # Matplotlib Price & Wyckoff Overlaid Chart
    # -------------------------------------------------------------
    st.markdown("---")
    st.markdown("### 📊 Price Chart with Wyckoff Schematic Events")

    fig, ax = plt.subplots(figsize=(14, 6), dpi=120)
    ax.plot(df["Date"], df["Close"], label="Close Price", color="#1f77b4", linewidth=1.5)

    # Plot SMAs
    if len(df) >= 50:
        ax.plot(df["Date"], df["Close"].rolling(50).mean(), label="50 DMA", color="#ff7f0e", linestyle="--", alpha=0.7)
    if len(df) >= 100:
        ax.plot(df["Date"], df["Close"].rolling(100).mean(), label="100 DMA", color="#2ca02c", linestyle=":", alpha=0.7)

    # Overlay Wyckoff Events
    event_markers = {
        "SC": {"color": "darkred", "marker": "v", "size": 90},
        "AR": {"color": "darkorange", "marker": "^", "size": 80},
        "ST": {"color": "purple", "marker": "o", "size": 60},
        "Spring": {"color": "blue", "marker": "s", "size": 80},
        "LPS": {"color": "green", "marker": "D", "size": 75},
        "SOS": {"color": "teal", "marker": "*", "size": 120},
        "UTAD": {"color": "red", "marker": "X", "size": 100},
    }

    detected_counts: dict[str, int] = {}
    for ev_type, ev_list in scored.detected_events.items():
        detected_counts[ev_type] = len(ev_list)
        cfg = event_markers.get(ev_type, {"color": "black", "marker": "o", "size": 50})
        for ev in ev_list:
            ev_date = pd.to_datetime(ev.date)
            ax.scatter(
                ev_date,
                ev.price,
                color=cfg["color"],
                marker=cfg["marker"],
                s=cfg["size"],
                zorder=5,
                label=ev_type if ev_type not in ax.get_legend_handles_labels()[1] else "",
            )
            ax.annotate(
                f"{ev_type}",
                (ev_date, ev.price),
                textcoords="offset points",
                xytext=(0, 10 if ev_type in ("AR", "SOS", "Spring") else -15),
                ha="center",
                fontsize=8,
                fontweight="bold",
                color=cfg["color"],
            )

    ax.set_title(f"{current_symbol} — Daily Price & Detected Wyckoff Schematic Events", fontsize=14, fontweight="bold")
    ax.set_ylabel("Price (INR)", fontsize=11)
    ax.grid(True, linestyle="--", alpha=0.4)
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %Y"))
    ax.legend(loc="upper left", framealpha=0.8)
    fig.autofmt_xdate()

    st.pyplot(fig)
    plt.close(fig)

    # -------------------------------------------------------------
    # Event Counts & Detailed Evidence Table
    # -------------------------------------------------------------
    st.markdown("---")
    st.markdown("### 📋 Detected Candidate Events & Evidence Log")
    st.write("Event Counts: " + ", ".join([f"**{k}**: {v}" for k, v in detected_counts.items()]))

    all_events_table = []
    for ev_type, ev_list in scored.detected_events.items():
        for ev in ev_list:
            all_events_table.append({
                "Event": ev.event_type,
                "Date": ev.date.strftime("%Y-%m-%d") if hasattr(ev.date, "strftime") else str(ev.date),
                "Price (₹)": f"{ev.price:.2f}",
                "Volume Ratio": f"{ev.volume_ratio:.2f}x",
                "Spread Ratio": f"{ev.spread_ratio:.2f}x",
                "Close Position": f"{ev.close_position:.2f}",
                "Supporting Evidence / Numeric Rationale": ev.supporting_note,
            })

    if all_events_table:
        events_df = pd.DataFrame(all_events_table).sort_values(by="Date", ascending=False)
        st.dataframe(events_df, use_container_width=True, height=350)
    else:
        st.info("No schematic events detected in this time range.")

    # -------------------------------------------------------------
    # Point & Figure Details Card
    # -------------------------------------------------------------
    st.markdown("---")
    st.markdown("### 🎯 Point & Figure (P&F) Horizontal Price Objective")
    if scored.pf_price_objective:
        pfo = scored.pf_price_objective
        st.write(f"- **Count Row Price:** ₹{pfo.count_row_price:.2f}")
        st.write(f"- **Box Size:** ₹{pfo.box_size:.2f} (1% dynamic scaling) | **Reversal:** {pfo.reversal} boxes")
        st.write(f"- **Columns Counted:** {pfo.num_columns} (Column indices: `{pfo.columns_counted[:10]}`...)")
        st.write(f"- **Formula:** `{pfo.formula}`")
        if pfo.used_fallback_count:
            st.warning("⚠️ Fallback Count Used: No column exactly touched the specified count row.")
        else:
            st.success("✅ Exact Touch Count: Horizontal base columns directly spanned the count row.")
        st.write(f"- **Derived Objective:** **₹{pfo.price_objective:.2f}**")
    else:
        st.info("Point & Figure objective calculation requires additional bars.")

    # -------------------------------------------------------------
    # Mechanical Filters Checklist
    # -------------------------------------------------------------
    st.markdown("---")
    st.markdown("### ⚙️ Mechanical Trend & Momentum Filters")
    f_cols = st.columns(4)
    for idx, (f_name, f_pass) in enumerate(scored.mechanical_filters_passed.items()):
        col = f_cols[idx % 4]
        icon = "✅" if f_pass else "❌"
        col.write(f"{icon} **{f_name.replace('_', ' ').title()}**")

else:
    st.info("👈 Please load data via the sidebar (fetch live ticker or upload a CSV) to begin analysis.")
