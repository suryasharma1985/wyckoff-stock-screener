"""Evidence-first explanation generator for Phase 9C Research Screening Engine."""

from typing import Any, Optional


def generate_candidate_explanation(
    symbol: str,
    is_mechanically_qualified: bool,
    filter_flags: dict[str, bool],
    filter_values: dict[str, Any],
    vsa_volume_ratio: float,
    vsa_close_position: float,
    is_stopping_volume: bool,
    is_no_supply: bool,
    is_no_demand: bool,
    most_recent_event_type: Optional[str],
    numeric_evidence: str,
    pf_target_price: Optional[float],
    pf_upside_pct: Optional[float],
    composite_score: float,
    is_disqualified: bool,
    disqualifying_flags: list[str],
    candidate_category: str,
) -> str:
    """Generate a structured, evidence-first explanation narrative for a screened security.

    Args:
        symbol: Ticker symbol.
        is_mechanically_qualified: Compound 3-gate mechanical qualification outcome.
        filter_flags: Boolean results for each mechanical filter.
        filter_values: Exact numerical values for indicators.
        vsa_volume_ratio: 20-day rolling volume ratio.
        vsa_close_position: Position of close within bar range.
        is_stopping_volume: Absorption flag.
        is_no_supply: Supply dry-up flag.
        is_no_demand: Demand dry-up flag.
        most_recent_event_type: Name of most recent candidate schematic event.
        numeric_evidence: Detailed evidence string for the event.
        pf_target_price: Calculated Point & Figure price objective.
        pf_upside_pct: Potential upside percentage to target.
        composite_score: Setup composite score (0-100).
        is_disqualified: True if structural red flags present.
        disqualifying_flags: Specific disqualifying reasons.
        candidate_category: Assigned triage category.

    Returns:
        Structured string summarizing exact numeric and structural evidence.
    """
    parts = []

    # 1. Classification & Score
    parts.append(f"[{candidate_category}] Score: {composite_score:.1f}/100.0")

    # 2. Red Flags / Disqualification
    if is_disqualified:
        flags_str = ", ".join(disqualifying_flags) if disqualifying_flags else "Structural Red Flag"
        parts.append(f"DISQUALIFIED: {flags_str}")
        return " | ".join(parts)

    # 3. Mechanical Filter Evidence
    mech_str = "Mech Qual: PASS" if is_mechanically_qualified else "Mech Qual: FAIL"
    sub_parts = []
    if filter_flags.get("weekly_uptrend"):
        w30 = filter_values.get("wma_30")
        w40 = filter_values.get("wma_40")
        sub_parts.append(f"Weekly WMA(30/40) Up ({w30:.1f}>{w40:.1f})" if w30 and w40 else "Weekly WMA Up")
    if filter_flags.get("dma_50_above_100"):
        d50 = filter_values.get("dma_50")
        d100 = filter_values.get("d100", filter_values.get("dma_100"))
        sub_parts.append(f"Daily DMA(50/100) Up ({d50:.1f}>{d100:.1f})" if d50 and d100 else "Daily DMA Up")
    if filter_flags.get("rsi_in_band"):
        rsi_val = filter_values.get("rsi_14")
        sub_parts.append(f"RSI(14) Bullish ({rsi_val:.1f})" if rsi_val is not None else "RSI Bullish")
    if filter_flags.get("atr_contracting"):
        atr_r = filter_values.get("atr_contraction_ratio")
        sub_parts.append(f"ATR Contraction ({atr_r:.2f}<1.0)" if atr_r is not None else "ATR Contracting")
    if filter_flags.get("vcp_bbw_contracting"):
        sub_parts.append("BBW Contraction")

    if sub_parts:
        parts.append(f"{mech_str} ({', '.join(sub_parts)})")
    else:
        parts.append(mech_str)

    # 4. VSA Physics Evidence
    vsa_notes = []
    vsa_notes.append(f"Vol Ratio: {vsa_volume_ratio:.2f}x")
    vsa_notes.append(f"Close Pos: {vsa_close_position:.2f}")
    if is_stopping_volume:
        vsa_notes.append("Stopping Volume (Absorption)")
    if is_no_supply:
        vsa_notes.append("No Supply (Dry-up)")
    if is_no_demand:
        vsa_notes.append("No Demand")
    parts.append("VSA: " + ", ".join(vsa_notes))

    # 5. Wyckoff Schematic Candidate Evidence
    if most_recent_event_type and most_recent_event_type != "None":
        ev_str = f"Candidate Event: {most_recent_event_type}"
        if numeric_evidence:
            ev_str += f" ({numeric_evidence})"
        parts.append(ev_str)

    # 6. Point & Figure Evidence
    if pf_target_price is not None and pf_upside_pct is not None:
        parts.append(f"P&F Target: ₹{pf_target_price:.2f} (+{pf_upside_pct:.1f}% upside)")

    return " | ".join(parts)
