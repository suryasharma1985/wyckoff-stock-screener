"""Setup scoring and watchlist ranking engine."""

from wyckoff_screener.scoring.setup_scorer import (
    PF_ANCHOR_MAX_STALENESS_BARS,
    POINTS_PER_MECHANICAL_FILTER,
    WEIGHT_MECHANICAL_FILTERS,
    WEIGHT_PEER_RANK,
    WEIGHT_PF_UPSIDE,
    WEIGHT_RECENT_EVENT,
    ScoredSetup,
    rank_watchlist,
    score_setup,
)

__all__ = [
    "ScoredSetup",
    "score_setup",
    "rank_watchlist",
    "WEIGHT_MECHANICAL_FILTERS",
    "WEIGHT_RECENT_EVENT",
    "WEIGHT_PEER_RANK",
    "WEIGHT_PF_UPSIDE",
    "POINTS_PER_MECHANICAL_FILTER",
    "PF_ANCHOR_MAX_STALENESS_BARS",
]
