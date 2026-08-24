"""UI Explainer and Educational Presentation Components for Wyckoff Screener Dashboard.

Implements beginner-friendly explanations, structured chart checklists, visual score
breakdowns, and risk invalidation disclosures based strictly on verified engine metrics.
"""

from typing import Any, Dict, Optional
import os
import sys
import streamlit as st

_repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_src_path = os.path.join(_repo_root, "src")
_dashboard_path = os.path.join(_repo_root, "dashboard")

for _p in [_repo_root, _src_path, _dashboard_path]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

try:
    from dashboard.glossary import WYCKOFF_GLOSSARY
except ImportError:
    from glossary import WYCKOFF_GLOSSARY


def render_why_selected_card(
    symbol: str,
    category: str,
    composite_score: float,
    event_type: str,
    event_date: str,
    vol_ratio: float,
    spread_ratio: float,
    close_pos: float,
    mechanical_passed: bool,
    filter_details: Dict[str, Any],
    pf_target: Optional[float] = None,
    pf_upside: Optional[float] = None,
    pf_is_stale: bool = False,
    is_disqualified: bool = False,
    disqualifying_flags: str = "None",
    explanation_summary: str = "",
    beginner_mode: bool = True,
) -> None:
    """Render the 'Why did the system select this stock?' explanation section."""
    st.markdown("### 🧠 Why did the system select this stock?")

    # 1. High-level plain-English narrative
    if is_disqualified:
        st.error(
            f"🚫 **DISQUALIFIED SETUP**: The engine flagged severe red flags (`{disqualifying_flags}`). "
            f"Even if individual price/volume bars look attractive, this setup is disqualified because distribution or structural failure was detected."
        )
    elif category == "HIGH_PRIORITY_CANDIDATE":
        st.success(
            f"⭐ **HIGH PRIORITY CANDIDATE (Score: {composite_score:.1f}/100)**: "
            f"This stock passed all mechanical trend/momentum filters and formed a recent **{event_type}** candidate setup "
            f"supported by constructive volume-spread interaction."
        )
    elif category == "QUALIFIED_CANDIDATE":
        st.info(
            f"✅ **QUALIFIED CANDIDATE (Score: {composite_score:.1f}/100)**: "
            f"This stock passed key mechanical qualification filters and exhibits accumulation characteristics, though some secondary components may have lower scores."
        )
    elif category == "WATCHLIST":
        st.warning(
            f"👁 **WATCHLIST (Score: {composite_score:.1f}/100)**: "
            f"A candidate Wyckoff event was detected, but one or more mechanical trend/momentum filters failed or turnover is lower than primary candidates."
        )
    else:
        st.caption(f"**Research Status**: Category `{category}` with Composite Score `{composite_score:.1f}/100`.")

    # 2. Detailed Evidence Points
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("##### 🟢 Positive Supporting Evidence")
        evidence_list = []
        if event_type and event_type != "None":
            evidence_list.append(f"**Wyckoff Event Detected**: Candidate `{event_type}` identified on `{event_date}`.")
        if vol_ratio >= 1.5:
            evidence_list.append(f"**Elevated Volume**: Volume ratio is `{vol_ratio:.2f}x` 20-period average (indicates elevated trading effort).")
        elif vol_ratio < 0.75:
            evidence_list.append(f"**Volume Dry-Up**: Volume ratio is `{vol_ratio:.2f}x` 20-period average (indicates diminished trading volume).")
        else:
            evidence_list.append(f"**Normal Volume**: Volume ratio is `{vol_ratio:.2f}x` 20-period average.")

        if close_pos >= 0.70:
            evidence_list.append(f"**Strong Close**: Closed in top `{close_pos*100:.0f}%` of the day's range (buyers dominated).")
        elif close_pos <= 0.30:
            evidence_list.append(f"**Weak Close**: Closed in bottom `{close_pos*100:.0f}%` of the day's range (sellers dominated).")

        if mechanical_passed:
            evidence_list.append("**Mechanical Filters**: Passed technical trend, momentum, and turnover gates.")

        if pf_target and pf_upside and pf_upside > 0:
            evidence_list.append(f"**P&F Cause & Effect**: Bruce Fraser horizontal count indicates analytical upside of `+{pf_upside:.1f}%` (Target: ₹{pf_target:.2f}).")

        for item in evidence_list:
            st.markdown(f"- {item}")

    with c2:
        st.markdown("##### 🟡 Weaknesses, Caveats & Un-Evaluated Factors")
        caveats = []
        if is_disqualified:
            caveats.append(f"**Disqualifying Flag**: `{disqualifying_flags}`.")
        if pf_is_stale:
            caveats.append("**Stale P&F Count**: The Point & Figure count row anchor is older than 60 bars (awarded 0 points).")
        if not filter_details.get("dma_50_above_100", True):
            caveats.append("**Moving Average Lag**: 50 DMA is not above 100 DMA.")
        if not filter_details.get("rsi_in_band", True):
            caveats.append("**RSI Outside Optimal Zone**: 14-period RSI is not within the 55–70 bullish momentum band.")
        if not filter_details.get("atr_contracting", True) and not filter_details.get("vcp_bbw_contracting", True):
            caveats.append("**No Volatility Contraction**: ATR and Bollinger Bandwidth are not contracting.")

        caveats.append("**Not evaluated by current engine**: Fundamental valuation, earnings announcements, intraday order flow, broader index sentiment.")

        for item in caveats:
            st.markdown(f"- {item}")

    if explanation_summary:
        st.caption(f"**Engine Summary Note**: {explanation_summary}")


def render_wyckoff_interpretation_card(
    event_type: str,
    event_date: str,
    vol_ratio: float,
    spread_ratio: float,
    close_pos: float,
    beginner_mode: bool = True,
) -> None:
    """Render the '📚 Wyckoff Interpretation' section with non-certainty language."""
    st.markdown("### 📚 Wyckoff Structural Interpretation")

    interp_map = {
        "Spring": {
            "title": "Phase C — Potential Spring & Shakeout",
            "desc": "The engine detected a bar that undercut prior trading range support intrabar before closing back inside the range.",
            "wyckoff_context": "In classical Wyckoff accumulation theory, a Spring tests remaining supply and traps premature short-sellers. If supply is completely absorbed, a markup rally typically follows.",
            "next_confirmation": "Look for a low-volume retest (Secondary Test / LPS) holding above the Spring low, followed by an expansion in volume and spread (Sign of Strength).",
            "invalidation": "A decisive close below the Spring low on heavy volume invalidates the accumulation premise.",
        },
        "LPS": {
            "title": "Phase C/D — Potential Last Point of Support (LPS)",
            "desc": "The engine detected a pullback holding at a higher low above support on diminished volume.",
            "wyckoff_context": "An LPS demonstrates that institutional buyers are willing to support price at higher levels and sellers are exhausted (dry volume).",
            "next_confirmation": "Look for an impulsive up-move breaking above trading range resistance (SOS / Jump Across the Creek).",
            "invalidation": "A breakdown through prior trading range support invalidates the LPS.",
        },
        "SOS": {
            "title": "Phase D/E — Potential Sign of Strength (SOS / Breakout)",
            "desc": "The engine detected a wide-spread bar breaking above resistance on elevated institutional volume.",
            "wyckoff_context": "An SOS signals that demand has overcome overhead supply, transitioning the stock from the accumulation trading range into an active markup uptrend.",
            "next_confirmation": "Look for a low-volume 'Backup' / pullback holding near former resistance (now acting as new support).",
            "invalidation": "A fast collapse back below resistance on heavy volume (Upthrust / UTAD) invalidates the breakout.",
        },
        "SC": {
            "title": "Phase A — Potential Selling Climax (SC)",
            "desc": "The engine detected heavy volume on wide spread after a prolonged decline.",
            "wyckoff_context": "Marks potential initial absorption of panicked retail supply by institutional buyers.",
            "next_confirmation": "Look for an Automatic Rally (AR) followed by a Secondary Test (ST) on lower volume.",
            "invalidation": "Continued heavy selling slicing through the low without a bounce.",
        },
        "UTAD": {
            "title": "Distribution Alert — Potential Upthrust After Distribution (UTAD)",
            "desc": "The engine detected a breakout above resistance that failed and closed back inside the range on high volume.",
            "wyckoff_context": "A UTAD is a major distribution signal where smart money sells into breakout buyer liquidity before a markdown downtrend.",
            "next_confirmation": "Watch for breakdown below trading range support.",
            "invalidation": "A strong recovery reclaiming high ground on heavy volume.",
        },
    }

    info = interp_map.get(event_type, {
        "title": f"Candidate Event: {event_type}",
        "desc": f"The engine identified candidate event `{event_type}` based on price spread and volume metrics.",
        "wyckoff_context": "Wyckoff analysis focuses on the interaction between smart money accumulation and retail supply.",
        "next_confirmation": "Requires confirmation across multi-timeframe daily and weekly charts.",
        "invalidation": "A violation of structural support or resistance invalidates the setup.",
    })

    st.markdown(f"#### {info['title']}")
    st.write(info["desc"])

    if beginner_mode:
        st.info(f"💡 **Beginner Concept**: {info['wyckoff_context']}")

    wc1, wc2 = st.columns(2)
    with wc1:
        st.markdown("**🔍 What Confirmation to Look for Next:**")
        st.write(info["next_confirmation"])
    with wc2:
        st.markdown("**⚠️ Structural Invalidation Level:**")
        st.write(info["invalidation"])

    st.caption("⚠️ **Scientific Notice**: All Wyckoff schematic events are quantitative candidates, never certainties. Always verify with human visual chart inspection.")


def render_chart_checklist_card(
    filter_details: Dict[str, Any],
    vol_ratio: float,
    spread_ratio: float,
    close_pos: float,
    event_type: str,
    pf_target: Optional[float] = None,
    pf_is_stale: bool = False,
    is_disqualified: bool = False,
) -> None:
    """Render the 'What should I look at on the chart?' inspection checklist."""
    st.markdown("### 🎯 What Should I Look At On The Chart?")
    st.caption("Use this visual checklist when inspecting the daily and weekly charts on TradingView.")

    items = []

    # 1. Price Structure & Trend
    weekly_up = filter_details.get("weekly_uptrend", False)
    dma_ok = filter_details.get("dma_50_above_100", False)
    if weekly_up and dma_ok:
        items.append(("✅", "Macro Price Structure", "Strong trend alignment: Weekly Close > 30-week SMA and 50 DMA > 100 DMA."))
    elif weekly_up or dma_ok:
        items.append(("⚠️", "Macro Price Structure", "Mixed trend alignment: One of Weekly trend or 50/100 DMA is lagging."))
    else:
        items.append(("❌", "Macro Price Structure", "Weak trend alignment: Price is below key moving averages."))

    # 2. Volume & VSA
    if vol_ratio >= 2.0:
        items.append(("✅", "Volume Confirmation", f"Climactic volume ({vol_ratio:.2f}x) showing decisive institutional effort."))
    elif vol_ratio >= 1.5:
        items.append(("✅", "Volume Confirmation", f"Elevated volume ({vol_ratio:.2f}x) showing above-average participation."))
    elif vol_ratio < 0.75:
        items.append(("✅", "Volume Dry-Up", f"Dry volume ({vol_ratio:.2f}x) showing lack of selling pressure on pullback."))
    else:
        items.append(("ℹ️", "Volume Interaction", f"Average volume ({vol_ratio:.2f}x) — neither climactic nor dried up."))

    # 3. Wyckoff Candidate Event
    if is_disqualified:
        items.append(("❌", "Wyckoff Event Context", "Disqualified setup: Red flag or UTAD warning present."))
    elif event_type in ["LPS", "Spring", "SOS"]:
        items.append(("✅", "Wyckoff Event Context", f"Bullish candidate `{event_type}` identified within the trading range structure."))
    else:
        items.append(("ℹ️", "Wyckoff Event Context", f"Event `{event_type}` recorded."))

    # 4. Volatility Contraction (VCP)
    atr_ok = filter_details.get("atr_contracting", False)
    vcp_ok = filter_details.get("vcp_bbw_contracting", False)
    if atr_ok and vcp_ok:
        items.append(("✅", "Volatility Contraction (VCP)", "Both ATR and Bollinger Bandwidth are contracting (price tightening into base)."))
    elif atr_ok or vcp_ok:
        items.append(("✅", "Volatility Contraction", "Partial volatility contraction observed."))
    else:
        items.append(("⚠️", "Volatility Contraction", "Volatility is expanding or wide; price swings have not tightened yet."))

    # 5. Point & Figure Cause & Effect
    if pf_target and not pf_is_stale:
        items.append(("✅", "Point & Figure Base", f"Valid horizontal count row identified with upside target of ₹{pf_target:.2f}."))
    elif pf_is_stale:
        items.append(("⚠️", "Point & Figure Base", "P&F anchor is older than 60 bars (stale count)."))
    else:
        items.append(("ℹ️", "Point & Figure Base", "No horizontal count target calculated."))

    for icon, label, note in items:
        st.markdown(f"**{icon} {label}**: {note}")


def render_score_breakdown_card(
    composite_score: float,
    score_breakdown: Dict[str, float],
    beginner_mode: bool = True,
) -> None:
    """Render the score component breakdown with exact weights and research caveats."""
    st.markdown("### 📊 Composite Score Breakdown")

    # Score components (Exact 100-point allocation):
    # 30 pts Mechanical Filters (4 x 7.5)
    # 40 pts Schematic Recency
    # 20 pts Peer Relative Strength
    # 10 pts P&F Upside
    mech_pts = score_breakdown.get("mechanical_filters_pts", 0.0)
    rec_pts = score_breakdown.get("schematic_recency_pts", 0.0)
    peer_pts = score_breakdown.get("peer_relative_strength_pts", 0.0)
    pf_pts = score_breakdown.get("pf_upside_pts", 0.0)

    st.markdown(f"#### Overall Composite Score: **{composite_score:.1f} / 100**")

    c1, c2 = st.columns(2)
    with c1:
        st.write(f"**1. Mechanical Filters**: `{mech_pts:.1f} / 30.0 pts`")
        st.progress(min(max(mech_pts / 30.0, 0.0), 1.0))
        st.caption("Evaluates 50>100 DMA, Weekly trend, RSI momentum band, and ATR/VCP contraction (7.5 pts each).")

        st.write(f"**2. Wyckoff Event Recency**: `{rec_pts:.1f} / 40.0 pts`")
        st.progress(min(max(rec_pts / 40.0, 0.0), 1.0))
        st.caption("Awards points based on how recently a candidate Spring, LPS, SOS, ST, or SC occurred.")

    with c2:
        st.write(f"**3. Peer Relative Strength**: `{peer_pts:.1f} / 20.0 pts`")
        st.progress(min(max(peer_pts / 20.0, 0.0), 1.0))
        st.caption("Compares low-to-low slope progression against industry peers (0.0 if skipped).")

        st.write(f"**4. Point & Figure Upside**: `{pf_pts:.1f} / 10.0 pts`")
        st.progress(min(max(pf_pts / 10.0, 0.0), 1.0))
        st.caption("Tiered points based on horizontal count upside percentage (>=20% = 10 pts, >=10% = 6 pts).")

    st.markdown(
        '<div class="score-caveat">⚠️ <strong>Critical Scientific Disclosure</strong>: '
        'This score is a <em>research prioritization ranking</em>, NOT a mathematical win probability or price guarantee. '
        'Historical validation revealed that score magnitude above the qualification threshold is non-monotonic on individual stocks. '
        'Treat setups with scores >= 40 as qualified for human review, not as guaranteed winners.</div>',
        unsafe_allow_html=True,
    )


def render_screening_checklist_expander(
    filter_details: Dict[str, Any],
    vol_ratio: float,
    spread_ratio: float,
    close_pos: float,
) -> None:
    """Render the expandable '🔍 Screening Checklist' table."""
    with st.expander("🔍 Screening Checklist & Technical Conditions", expanded=False):
        st.caption("Evaluates each mechanical filter condition and volume-spread ratio.")

        chk_data = [
            {
                "Condition": "Turnover Filter (Liquidity)",
                "Status": "✅ PASSED" if filter_details.get("pass_turnover", True) else "❌ FAILED",
                "Value": f"₹{filter_details.get('avg_turnover_cr', 0.0):.2f} Cr" if "avg_turnover_cr" in filter_details else "Pass",
                "Description": "Requires minimum 20-day average daily turnover (default ₹1.0 Cr).",
            },
            {
                "Condition": "50 DMA above 100 DMA",
                "Status": "✅ PASSED" if filter_details.get("dma_50_above_100", False) else "❌ FAILED",
                "Value": "True" if filter_details.get("dma_50_above_100", False) else "False",
                "Description": "Intermediate moving average alignment showing medium-term trend health.",
            },
            {
                "Condition": "Weekly Macro Uptrend",
                "Status": "✅ PASSED" if filter_details.get("weekly_uptrend", False) else "❌ FAILED",
                "Value": "True" if filter_details.get("weekly_uptrend", False) else "False",
                "Description": "Latest weekly close holds above the 30-week simple moving average.",
            },
            {
                "Condition": "RSI in Bullish Momentum Zone",
                "Status": "✅ PASSED" if filter_details.get("rsi_in_band", False) else "❌ FAILED",
                "Value": f"{filter_details.get('rsi_14', 0.0):.1f}" if "rsi_14" in filter_details else "In Band" if filter_details.get("rsi_in_band") else "Outside",
                "Description": "14-period RSI is within the 55–70 bullish expansion zone (not oversold, not extreme).",
            },
            {
                "Condition": "ATR Volatility Contraction",
                "Status": "✅ PASSED" if filter_details.get("atr_contracting", False) else "❌ FAILED",
                "Value": "Contracting" if filter_details.get("atr_contracting", False) else "Expanding",
                "Description": "Current 20-period ATR is below its historical average (price volatility calming).",
            },
            {
                "Condition": "Bollinger Bandwidth Contraction (VCP)",
                "Status": "✅ PASSED" if filter_details.get("vcp_bbw_contracting", False) else "❌ FAILED",
                "Value": "Contracting" if filter_details.get("vcp_bbw_contracting", False) else "Expanding",
                "Description": "20-period BBW is contracting relative to its 50-period mean (tightening base).",
            },
            {
                "Condition": "20-period Volume Ratio",
                "Status": "✅ CLIMACTIC / HIGH" if vol_ratio >= 1.5 else "✅ DRY VOLUME" if vol_ratio < 0.75 else "ℹ️ AVERAGE",
                "Value": f"{vol_ratio:.2f}x",
                "Description": "Volume compared to 20-day average. >= 2.0x is Climactic; < 0.75x is Dry.",
            },
            {
                "Condition": "20-period Spread Ratio",
                "Status": "✅ WIDE" if spread_ratio >= 1.5 else "ℹ️ AVERAGE" if spread_ratio >= 0.6 else "ℹ️ NARROW",
                "Value": f"{spread_ratio:.2f}x",
                "Description": "Bar range (High - Low) compared to 20-day ATR. >= 1.5x is Wide spread.",
            },
            {
                "Condition": "Bar Close Position",
                "Status": "✅ STRONG" if close_pos >= 0.70 else "❌ WEAK" if close_pos <= 0.30 else "ℹ️ MID",
                "Value": f"{close_pos:.2f} ({close_pos*100:.0f}%)",
                "Description": "Location of close within bar range (0.0 = low, 1.0 = high).",
            },
        ]
        import pandas as pd
        st.dataframe(pd.DataFrame(chk_data), use_container_width=True)


def render_risks_and_invalidations_card(
    event_type: str,
    support_level: Optional[float] = None,
    resistance_level: Optional[float] = None,
    is_disqualified: bool = False,
    disqualifying_flags: str = "None",
) -> None:
    """Render the '⚠️ What could invalidate this setup / Risks' section."""
    st.markdown("### ⚠️ What Could Invalidate This Setup? (Risks & Invalidation Levels)")

    st.write(
        "Every Wyckoff accumulation thesis has specific price and volume conditions that prove the hypothesis wrong. "
        "Monitor these structural risk factors:"
    )

    r1, r2 = st.columns(2)
    with r1:
        st.markdown("##### 🛑 Structural Breakdown Levels")
        if support_level:
            st.markdown(f"- **Support Breach**: A daily close below **₹{support_level:.2f}** indicates supply has overwhelmed demand, invalidating the base.")
        else:
            st.markdown("- **Support Breach**: A decisive close below the trading range low invalidates accumulation.")

        if is_disqualified:
            st.markdown(f"- **Disqualification Trigger**: Setup is already flagged for `{disqualifying_flags}`.")
        else:
            st.markdown("- **UTAD Formation**: If price attempts to break above resistance but collapses back inside on high volume, distribution is active.")

    with r2:
        st.markdown("##### 📉 Volume & Momentum Warnings")
        st.markdown("- **Heavy Volume on Pullbacks**: If subsequent pullbacks experience heavy expanding volume (supply), institutional absorption has failed.")
        st.markdown("- **No Demand on Rallies**: If attempted rallies show narrow spreads and declining volume (No Demand), buyers lack commitment.")
        st.markdown("- **Market / Sector Headwinds**: Broad Nifty 50 or sectoral sell-offs can overpower individual stock accumulation.")
