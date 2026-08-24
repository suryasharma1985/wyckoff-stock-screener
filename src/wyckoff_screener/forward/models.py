"""Data models and immutable records for Phase 11 Forward Validation."""

from dataclasses import asdict, dataclass, field
from enum import Enum
import hashlib
from typing import Any, Final, Optional

FORWARD_ENGINE_VERSION: Final[str] = "1.0.0"


class HorizonStatus(str, Enum):
    """Maturity state of a forward observation horizon."""

    PENDING = "PENDING"
    MATURED = "MATURED"
    INSUFFICIENT_BARS = "INSUFFICIENT_BARS"


def generate_candidate_id(symbol: str, screening_date: str, reference_close_price: float, engine_version: str = FORWARD_ENGINE_VERSION) -> str:
    """Generate a deterministic SHA-256 candidate ID from provenance attributes."""
    raw = f"{symbol.strip().upper()}_{screening_date.strip()}_{reference_close_price:.4f}_{engine_version.strip()}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]


@dataclass(frozen=True)
class ForwardCandidateRecord:
    """Immutable screening record capturing exact quantitative state at screening date T."""

    # 1. Identity & Provenance
    candidate_id: str
    screening_date: str
    symbol: str
    yfinance_ticker: str
    company_name: str
    reference_close_price: float
    data_bars: int

    # 2. Frozen Triage Categorization
    candidate_category: str
    composite_score: float
    is_mechanically_qualified: bool
    is_disqualified: bool
    disqualifying_flags: str  # Semi-colon separated string

    # 3. Mechanical Filter Sub-Flags
    weekly_uptrend: bool
    dma_50_above_100: bool
    rsi_in_band: bool
    atr_contracting: bool
    vcp_bbw_contracting: bool

    # 4. VSA Observations (Latest Bar at T)
    vsa_volume_ratio: float
    vsa_spread_ratio: float
    vsa_close_position: float
    is_stopping_volume: bool
    is_no_demand: bool
    is_no_supply: bool
    is_effort_vs_result: bool

    # 5. Wyckoff Schematic Events (Detected up to T)
    most_recent_event_type: str
    most_recent_event_date: str
    possible_LPS: bool
    possible_SOS: bool
    possible_Spring: bool
    is_UTAD_warning: bool
    numeric_evidence: str

    # 6. Point & Figure Objectives (Formed up to T)
    pf_target_price: Optional[float]
    pf_upside_pct: Optional[float]
    pf_count_columns: Optional[int]
    pf_is_stale_anchor: bool

    # 7. Explanation & Visual Navigation
    explanation_summary: str
    tradingview_daily_url: str
    tradingview_weekly_url: str
    tradingview_75m_url: str

    # 8. Integrity Metadata
    engine_version: str = FORWARD_ENGINE_VERSION
    created_at_utc: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Convert immutable candidate record to flat dictionary for tabular export."""
        return asdict(self)


@dataclass
class ForwardOutcomeRecord:
    """Prospective forward outcome tracking record for a frozen candidate."""

    # 1. Identification & Anchors
    candidate_id: str
    symbol: str
    screening_date: str
    reference_close_price: float
    candidate_category: str
    composite_score: float

    # 2. Tracking State
    available_forward_bars: int = 0
    status_10d: str = HorizonStatus.PENDING.value
    status_20d: str = HorizonStatus.PENDING.value
    status_60d: str = HorizonStatus.PENDING.value

    # 3. Realized Returns (% close-to-close)
    fwd_ret_10d: Optional[float] = None
    fwd_ret_20d: Optional[float] = None
    fwd_ret_60d: Optional[float] = None

    # 4. Maximum Favorable Excursion (% from reference close)
    mfe_10d: Optional[float] = None
    mfe_20d: Optional[float] = None
    mfe_60d: Optional[float] = None

    # 5. Maximum Adverse Excursion (% from reference close)
    mae_10d: Optional[float] = None
    mae_20d: Optional[float] = None
    mae_60d: Optional[float] = None

    # 6. Metadata
    last_updated_date: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Convert outcome record to flat dictionary for CSV persistence."""
        return asdict(self)


@dataclass
class ForwardSnapshotManifest:
    """Manifest describing an immutable daily screening snapshot."""

    snapshot_id: str
    screening_date: str
    created_at_utc: str
    engine_version: str
    total_candidates: int
    category_counts: dict[str, int]
    source_dataset_or_live: str
    candidate_records: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert manifest to serializable dictionary."""
        return asdict(self)
