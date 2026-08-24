"""Wyckoff Method & VSA Educational Glossary for Streamlit UI.

Provides structured plain-English explanations for beginners and technical definitions
for experienced analysts, strictly covering terminology used in the application.
"""

from typing import Dict, Any, List

WYCKOFF_GLOSSARY: Dict[str, Dict[str, str]] = {
    "Selling Climax (SC)": {
        "short": "SC",
        "category": "Wyckoff Schematic Event",
        "simple_definition": "A sharp, panicky sell-off where institutional buyers step in to absorb large amounts of panicked retail selling.",
        "why_it_matters": "Marks the potential end of a prolonged downtrend and the potential beginning of Phase A in an accumulation trading range.",
        "engine_logic": "Detected on down-close bars with Wide spread (spread_ratio >= 1.5) and Climactic volume (volume_ratio >= 2.0) occurring after a clear prior decline (>= 3% over 10 bars).",
    },
    "Automatic Rally (AR)": {
        "short": "AR",
        "category": "Wyckoff Schematic Event",
        "simple_definition": "A sharp rebound that immediately follows a Selling Climax as intense selling pressure suddenly evaporates and short-sellers cover.",
        "why_it_matters": "Defines the initial upper resistance boundary of the newly formed trading range.",
        "engine_logic": "Detected as a sharp up-close bar occurring immediately (within 1–5 bars) after an SC candidate, with volume_ratio >= 1.0.",
    },
    "Secondary Test (ST)": {
        "short": "ST",
        "category": "Wyckoff Schematic Event",
        "simple_definition": "A price pullback that revisits the area of the Selling Climax low to test whether heavy selling pressure has genuinely dried up.",
        "why_it_matters": "Confirms that supply is diminishing if the retest holds near support on lower volume than the original climax.",
        "engine_logic": "Detected when price tests within 3% of the prior SC low within 15 bars, with volume_ratio strictly lower than the SC candidate's volume ratio.",
    },
    "Spring": {
        "short": "Spring",
        "category": "Wyckoff Schematic Event",
        "simple_definition": "A temporary false breakdown below trading range support that quickly reverses and closes back inside the range.",
        "why_it_matters": "In Phase C, smart money uses this false breakdown to flush out remaining weak-handed sellers and test for leftover supply before a markup.",
        "engine_logic": "Detected when a bar's low dips below prior trading range support intrabar, but the bar closes firmly back above that support level.",
    },
    "Last Point of Support (LPS)": {
        "short": "LPS",
        "category": "Wyckoff Schematic Event",
        "simple_definition": "A higher pullback low that holds firmly above support on low volume (lack of selling pressure) before a markup rally.",
        "why_it_matters": "Represents the ideal low-risk entry location in Phase C/D where pullbacks hold at higher levels on reduced volume.",
        "engine_logic": "Detected when a higher low forms above prior Spring/ST support with low volume_ratio (< 0.75 or dry volume) within 20 bars of the anchor.",
    },
    "Sign of Strength (SOS)": {
        "short": "SOS",
        "category": "Wyckoff Schematic Event",
        "simple_definition": "A wide, powerful up-move on high volume that breaks above trading range resistance.",
        "why_it_matters": "Demonstrates that institutional demand has completely overwhelmed supply and a new uptrend (markup phase) is beginning.",
        "engine_logic": "Detected when close price breaks above trading range resistance on elevated volume (volume_ratio >= 1.5) with a strong close in the top 30% of the bar (close_position > 0.7).",
    },
    "Upthrust After Distribution (UTAD)": {
        "short": "UTAD",
        "category": "Wyckoff Schematic Event (Bearish Warning)",
        "simple_definition": "A false breakout above resistance that fails and closes back inside or below the range, trapping late buyers.",
        "why_it_matters": "Indicates institutional distribution (selling) and severe downside risk. In this screener, a recent UTAD acts as a disqualifying red flag.",
        "engine_logic": "Detected when a bar's high penetrates resistance intrabar but closes back below it on elevated volume (volume_ratio >= 1.5). Sets is_disqualified = True.",
    },
    "Volume Ratio": {
        "short": "Vol Ratio",
        "category": "VSA Metric",
        "simple_definition": "Compares today's trading volume to the average volume over the last 20 trading days.",
        "why_it_matters": "High volume shows institutional participation (effort); low volume shows lack of interest or lack of selling pressure (dry-up).",
        "engine_logic": "volume_ratio = bar_volume / rolling_20_period_avg_volume. >= 2.0 is Climactic, 1.5–2.0 is High, 0.75–1.5 is Average, < 0.75 is Low/Dry.",
    },
    "Spread Ratio": {
        "short": "Spread",
        "category": "VSA Metric",
        "simple_definition": "The price range (High minus Low) of today's bar compared to the average true range over the last 20 days.",
        "why_it_matters": "Wide spreads show strong price movement; narrow spreads indicate absorption, pausing, or contraction.",
        "engine_logic": "spread_ratio = (High - Low) / rolling_20_period_ATR. >= 1.5 is Wide, 0.6–1.5 is Average, < 0.6 is Narrow.",
    },
    "Close Position": {
        "short": "Close Pos",
        "category": "VSA Metric",
        "simple_definition": "Where the price closed within today's range, expressed from 0.0 (exact low) to 1.0 (exact high).",
        "why_it_matters": "A close near the high (>0.70) shows buyers won the bar; a close near the low (<0.30) shows sellers dominated.",
        "engine_logic": "close_position = (Close - Low) / (High - Low). > 0.70 is Strong (Near High), < 0.30 is Weak (Near Low), 0.30–0.70 is Mid-range.",
    },
    "Stopping Volume": {
        "short": "Stopping Vol",
        "category": "VSA Pattern",
        "simple_definition": "High volume on a narrow or average spread bar during a decline, indicating institutional absorption of retail selling.",
        "why_it_matters": "Shows heavy buying entering the market to stop downward price momentum.",
        "engine_logic": "volume_ratio >= 1.5 and spread_ratio < 1.0 on a down bar.",
    },
    "No Supply": {
        "short": "No Supply",
        "category": "VSA Pattern",
        "simple_definition": "A down-close bar with narrow spread and very low volume, showing sellers have disappeared.",
        "why_it_matters": "Confirms lack of selling pressure before a potential rally (often seen on LPS pullbacks).",
        "engine_logic": "Down-close bar with spread_ratio < 1.0 (or < 0.6) and volume_ratio < 1.0 (or < 0.75).",
    },
    "No Demand": {
        "short": "No Demand",
        "category": "VSA Pattern",
        "simple_definition": "An up-close bar with narrow spread and very low volume, showing buyers lack conviction.",
        "why_it_matters": "Warning sign that an up-move lacks institutional participation.",
        "engine_logic": "Up-close bar with spread_ratio < 1.0 and volume_ratio < 1.0.",
    },
    "Effort vs Result Flag": {
        "short": "Effort vs Result",
        "category": "VSA Pattern",
        "simple_definition": "A mismatch between the volume invested (effort) and the resulting price progress.",
        "why_it_matters": "Huge volume with zero price gain suggests hidden selling (churn); tiny volume with huge price gain suggests lack of liquidity.",
        "engine_logic": "Flagged when volume_ratio >= 1.5 but spread_ratio < 0.8 and close position is contradictory.",
    },
    "Point & Figure (P&F) Count": {
        "short": "P&F Target",
        "category": "Price Objective Method",
        "simple_definition": "A timeless horizontal counting method developed by Bruce Fraser to estimate potential upside price objectives based on the width of accumulation.",
        "why_it_matters": "Wyckoff's Law of Cause and Effect: the wider the horizontal base (Cause), the larger the potential vertical move (Effect).",
        "engine_logic": "Constructs algorithmic 3-box reversal P&F chart, identifies count row at LPS/Spring level, counts columns across trading range: Target = Count_Row_Price + (Columns * Box_Size * 3).",
    },
    "Volatility Contraction Pattern (VCP / BBW)": {
        "short": "VCP / ATR Contraction",
        "category": "Volatility Filter",
        "simple_definition": "A progressive decrease in price volatility (smaller daily swings) as supply is absorbed across a base.",
        "why_it_matters": "Shows price is tightening into a tight consolidation before an explosive directional breakout.",
        "engine_logic": "Evaluates 20-period ATR ratio < 1.0 and Bollinger Bandwidth (BBW) contracting relative to its 50-period average.",
    },
    "Maximum Favorable Excursion (MFE)": {
        "short": "MFE",
        "category": "Forward Performance Metric",
        "simple_definition": "The highest percentage gain the stock reached at any point during the forward holding period.",
        "why_it_matters": "Measures the maximum profit potential that was available before the horizon concluded.",
        "engine_logic": "MFE = (max(High[T+1 ... T+H]) - Close[T]) / Close[T] * 100.",
    },
    "Maximum Adverse Excursion (MAE)": {
        "short": "MAE",
        "category": "Forward Performance Metric",
        "simple_definition": "The largest percentage drop the stock experienced at any point during the forward holding period.",
        "why_it_matters": "Measures the maximum drawndown risk and pain a trader had to endure during the holding period.",
        "engine_logic": "MAE = (min(Low[T+1 ... T+H]) - Close[T]) / Close[T] * 100.",
    },
    "Composite Score": {
        "short": "Composite Score",
        "category": "Screening Metric",
        "simple_definition": "A 0–100 point research ranking combining mechanical filters, Wyckoff event recency, peer strength, and P&F upside.",
        "why_it_matters": "Used for coarse triage and candidate ranking. It is NOT a win probability or guaranteed predictor of profit.",
        "engine_logic": "30 pts Mechanical Filters (4 x 7.5) + 40 pts Schematic Recency + 20 pts Peer Strength + 10 pts P&F Upside.",
    },
}


def get_glossary_terms() -> List[str]:
    """Return sorted list of glossary term titles."""
    return sorted(list(WYCKOFF_GLOSSARY.keys()))


def get_term_details(term: str) -> Dict[str, str]:
    """Return details dict for a specific term."""
    return WYCKOFF_GLOSSARY.get(term, {})
