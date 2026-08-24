"""Unit tests for Phase 14 Explainable UI, Glossary, and Explainer components."""

import pytest
from dashboard.glossary import WYCKOFF_GLOSSARY, get_glossary_terms, get_term_details
from dashboard.explainers import (
    render_why_selected_card,
    render_wyckoff_interpretation_card,
    render_chart_checklist_card,
    render_score_breakdown_card,
    render_screening_checklist_expander,
    render_risks_and_invalidations_card,
)


def test_glossary_terms_and_completeness():
    """Verify that glossary contains all core Wyckoff and VSA terms with required fields."""
    terms = get_glossary_terms()
    assert len(terms) >= 15

    expected_terms = [
        "Selling Climax (SC)",
        "Automatic Rally (AR)",
        "Secondary Test (ST)",
        "Spring",
        "Last Point of Support (LPS)",
        "Sign of Strength (SOS)",
        "Upthrust After Distribution (UTAD)",
        "Volume Ratio",
        "Spread Ratio",
        "Close Position",
        "Stopping Volume",
        "No Supply",
        "No Demand",
        "Point & Figure (P&F) Count",
        "Maximum Favorable Excursion (MFE)",
        "Maximum Adverse Excursion (MAE)",
        "Composite Score",
    ]
    for term in expected_terms:
        assert term in terms, f"Missing term: {term}"
        details = get_term_details(term)
        assert "simple_definition" in details
        assert "why_it_matters" in details
        assert "engine_logic" in details


def test_explainer_renderers_smoke():
    """Verify that explainer card renderers can be called with mock data without exceptions."""
    filter_details = {
        "pass_turnover": True,
        "dma_50_above_100": True,
        "weekly_uptrend": True,
        "rsi_in_band": True,
        "atr_contracting": True,
        "vcp_bbw_contracting": True,
    }
    score_breakdown = {
        "mechanical_filters_pts": 30.0,
        "schematic_recency_pts": 40.0,
        "peer_relative_strength_pts": 0.0,
        "pf_upside_pts": 10.0,
    }

    # Test why_selected
    render_why_selected_card(
        symbol="ANANTRAJ",
        category="HIGH_PRIORITY_CANDIDATE",
        composite_score=80.0,
        event_type="LPS",
        event_date="2026-08-20",
        vol_ratio=2.2,
        spread_ratio=1.6,
        close_pos=0.85,
        mechanical_passed=True,
        filter_details=filter_details,
        pf_target=900.0,
        pf_upside=20.0,
        beginner_mode=True,
    )

    # Test wyckoff interpretation
    render_wyckoff_interpretation_card(
        event_type="Spring",
        event_date="2026-08-15",
        vol_ratio=1.8,
        spread_ratio=1.2,
        close_pos=0.75,
        beginner_mode=True,
    )

    # Test chart checklist
    render_chart_checklist_card(
        filter_details=filter_details,
        vol_ratio=1.8,
        spread_ratio=1.2,
        close_pos=0.75,
        event_type="Spring",
        pf_target=900.0,
    )

    # Test score breakdown
    render_score_breakdown_card(
        composite_score=80.0,
        score_breakdown=score_breakdown,
        beginner_mode=True,
    )

    # Test screening checklist
    render_screening_checklist_expander(
        filter_details=filter_details,
        vol_ratio=1.8,
        spread_ratio=1.2,
        close_pos=0.75,
    )

    # Test risks & invalidations
    render_risks_and_invalidations_card(
        event_type="LPS",
        support_level=750.0,
        resistance_level=850.0,
    )
