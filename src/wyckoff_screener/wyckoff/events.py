"""Wyckoff event definitions and structured data models.

Adheres strictly to AGENTS.md Guiding Principle — No Fabricated Confidence:
Every flagged event must cite the specific numbers behind it (volume ratio,
spread ratio, close position, price level) in its supporting_note.
"""

from dataclasses import dataclass
from typing import Any, Optional
import pandas as pd


@dataclass(frozen=True)
class WyckoffEvent:
    """Represents a quantified Wyckoff schematic event candidate.

    Attributes:
        event_type: Name/Code of the schematic event (e.g., 'SC', 'AR', 'ST', 'Spring', 'LPS', 'SOS', 'UTAD').
        date: Date or timestamp of the bar where the event was detected.
        price: Price level at the event bar (typically the Close price).
        volume_ratio: Ratio of bar volume to the 20-period rolling average volume.
        spread_ratio: Ratio of bar spread (H-L) to the 20-period rolling average true range.
        close_position: Close position within the bar's range [0.0, 1.0].
        supporting_note: Explicit, quantified string showing the numeric evidence behind the candidate.
    """

    event_type: str
    date: Any
    price: float
    volume_ratio: float
    spread_ratio: float
    close_position: float
    supporting_note: str
    support_level: Optional[float] = None
    anchor_low: Optional[float] = None

    def to_dict(self) -> dict[str, Any]:
        """Convert event to dictionary."""
        d = {
            "event_type": self.event_type,
            "date": pd.to_datetime(self.date).strftime("%Y-%m-%d") if hasattr(self.date, "strftime") else str(self.date),
            "price": self.price,
            "volume_ratio": round(self.volume_ratio, 2),
            "spread_ratio": round(self.spread_ratio, 2),
            "close_position": round(self.close_position, 2),
            "supporting_note": self.supporting_note,
        }
        if self.support_level is not None:
            d["support_level"] = self.support_level
        if self.anchor_low is not None:
            d["anchor_low"] = self.anchor_low
        return d
