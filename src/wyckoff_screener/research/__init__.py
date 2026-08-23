"""Phase 9C Broad NSE EQ Research Screening & Candidate Intelligence Package."""

from wyckoff_screener.research.explanation import generate_candidate_explanation
from wyckoff_screener.research.models import (
    CandidateCategory,
    ResearchCandidateResult,
    ResearchScreeningManifest,
    ResearchScreeningResult,
)
from wyckoff_screener.research.screening_engine import (
    DEFAULT_HIGH_PRIORITY_THRESHOLD,
    DEFAULT_QUALIFIED_THRESHOLD,
    DEFAULT_RESULTS_BASE_DIR,
    DEFAULT_WATCHLIST_THRESHOLD,
    run_research_screening,
)

__all__ = [
    "CandidateCategory",
    "ResearchCandidateResult",
    "ResearchScreeningManifest",
    "ResearchScreeningResult",
    "generate_candidate_explanation",
    "run_research_screening",
    "DEFAULT_RESULTS_BASE_DIR",
    "DEFAULT_HIGH_PRIORITY_THRESHOLD",
    "DEFAULT_QUALIFIED_THRESHOLD",
    "DEFAULT_WATCHLIST_THRESHOLD",
]
