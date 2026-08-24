"""Persistent forward validation ledger and immutable snapshot manager."""

from datetime import datetime, timezone
import json
import logging
from pathlib import Path
from typing import Any, Final, Optional, Sequence, Union
import pandas as pd

from wyckoff_screener.forward.models import (
    FORWARD_ENGINE_VERSION,
    ForwardCandidateRecord,
    ForwardOutcomeRecord,
    ForwardSnapshotManifest,
    HorizonStatus,
    generate_candidate_id,
)
from wyckoff_screener.research.models import ResearchCandidateResult

logger = logging.getLogger(__name__)

DEFAULT_FORWARD_BASE_DIR: Final[str] = "data/forward_validation"


class DuplicateScreeningDateError(Exception):
    """Raised when attempting to save a snapshot for an existing date without overwrite=True."""


class ForwardLedger:
    """Manager for immutable screening snapshots and forward outcome tracking ledgers."""

    def __init__(self, base_dir: Union[str, Path] = DEFAULT_FORWARD_BASE_DIR):
        self.base_dir = Path(base_dir)
        self.snapshots_dir = self.base_dir / "snapshots"
        self.ledger_dir = self.base_dir / "ledger"

        # Ensure directory structure exists
        self.snapshots_dir.mkdir(parents=True, exist_ok=True)
        self.ledger_dir.mkdir(parents=True, exist_ok=True)

        self.ledger_csv_path = self.ledger_dir / "forward_ledger.csv"
        self.outcomes_csv_path = self.ledger_dir / "forward_outcomes.csv"

    def get_snapshot_path(self, screening_date: str) -> Path:
        """Return the canonical file path for a dated snapshot."""
        clean_date = str(screening_date).strip().replace("-", "")
        return self.snapshots_dir / f"snapshot_{clean_date}.json"

    def snapshot_exists(self, screening_date: str) -> bool:
        """Check if an immutable snapshot already exists for a date."""
        return self.get_snapshot_path(screening_date).exists()

    def candidate_result_to_forward_record(
        self,
        cand: ResearchCandidateResult,
        reference_close_price: Optional[float] = None,
    ) -> ForwardCandidateRecord:
        """Convert a ResearchCandidateResult from Phase 9C into an immutable ForwardCandidateRecord."""
        # Determine reference close price at screening date T
        ref_price = reference_close_price
        if ref_price is None:
            ref_price = float(cand.filter_values.get("close", 0.0))

        scr_date = str(cand.as_of_date).strip()
        cand_id = generate_candidate_id(cand.symbol, scr_date, ref_price, FORWARD_ENGINE_VERSION)
        created_at = datetime.now(timezone.utc).isoformat()

        return ForwardCandidateRecord(
            candidate_id=cand_id,
            screening_date=scr_date,
            symbol=cand.symbol,
            yfinance_ticker=cand.yfinance_ticker,
            company_name=cand.company_name,
            reference_close_price=ref_price,
            data_bars=cand.data_bars,
            candidate_category=cand.candidate_category,
            composite_score=round(float(cand.composite_score), 2),
            is_mechanically_qualified=bool(cand.is_mechanically_qualified),
            is_disqualified=bool(cand.is_disqualified),
            disqualifying_flags="; ".join(cand.disqualifying_flags) if cand.disqualifying_flags else "None",
            weekly_uptrend=bool(cand.filter_flags.get("weekly_uptrend", False)),
            dma_50_above_100=bool(cand.filter_flags.get("dma_50_above_100", False)),
            rsi_in_band=bool(cand.filter_flags.get("rsi_in_band", False)),
            atr_contracting=bool(cand.filter_flags.get("atr_contracting", False)),
            vcp_bbw_contracting=bool(cand.filter_flags.get("vcp_bbw_contracting", False)),
            vsa_volume_ratio=round(float(cand.vsa_volume_ratio), 2),
            vsa_spread_ratio=round(float(cand.vsa_spread_ratio), 2),
            vsa_close_position=round(float(cand.vsa_close_position), 2),
            is_stopping_volume=bool(cand.is_stopping_volume),
            is_no_demand=bool(cand.is_no_demand),
            is_no_supply=bool(cand.is_no_supply),
            is_effort_vs_result=bool(cand.is_effort_vs_result),
            most_recent_event_type=str(cand.most_recent_event_type or "None"),
            most_recent_event_date=str(cand.most_recent_event_date or "None"),
            possible_LPS=bool(cand.possible_LPS),
            possible_SOS=bool(cand.possible_SOS),
            possible_Spring=bool(cand.possible_Spring),
            is_UTAD_warning=bool(cand.is_UTAD_warning),
            numeric_evidence=str(cand.numeric_evidence or "None"),
            pf_target_price=round(float(cand.pf_target_price), 2) if cand.pf_target_price is not None else None,
            pf_upside_pct=round(float(cand.pf_upside_pct), 2) if cand.pf_upside_pct is not None else None,
            pf_count_columns=cand.pf_count_columns,
            pf_is_stale_anchor=bool(cand.pf_is_stale_anchor),
            explanation_summary=str(cand.explanation_summary or ""),
            tradingview_daily_url=str(cand.tradingview_daily_url or ""),
            tradingview_weekly_url=str(cand.tradingview_weekly_url or ""),
            tradingview_75m_url=str(cand.tradingview_75m_url or ""),
            engine_version=FORWARD_ENGINE_VERSION,
            created_at_utc=created_at,
        )

    def save_screening_snapshot(
        self,
        screening_date: str,
        candidate_records: Sequence[ForwardCandidateRecord],
        source_description: str = "Broad NSE EQ Screening",
        overwrite: bool = False,
    ) -> ForwardSnapshotManifest:
        """Write an immutable dated JSON snapshot and update the persistent ledger tables.

        Args:
            screening_date: YYYY-MM-DD string.
            candidate_records: Sequence of frozen ForwardCandidateRecord items.
            source_description: Provenance note.
            overwrite: If False, raises DuplicateScreeningDateError if snapshot exists.

        Returns:
            ForwardSnapshotManifest written to disk.
        """
        snap_path = self.get_snapshot_path(screening_date)
        clean_date = str(screening_date).strip().replace("-", "")

        if snap_path.exists() and not overwrite:
            raise DuplicateScreeningDateError(
                f"Immutable snapshot already exists for screening date {screening_date} at {snap_path}. "
                f"To replace deliberately, set overwrite=True."
            )

        now_utc = datetime.now(timezone.utc).isoformat()
        records_dict = [rec.to_dict() for rec in candidate_records]

        # Compute category distribution
        category_counts: dict[str, int] = {}
        for rec in candidate_records:
            cat = rec.candidate_category
            category_counts[cat] = category_counts.get(cat, 0) + 1

        manifest = ForwardSnapshotManifest(
            snapshot_id=f"snap_{clean_date}",
            screening_date=str(screening_date),
            created_at_utc=now_utc,
            engine_version=FORWARD_ENGINE_VERSION,
            total_candidates=len(candidate_records),
            category_counts=category_counts,
            source_dataset_or_live=source_description,
            candidate_records=records_dict,
        )

        # Write immutable JSON snapshot
        with open(snap_path, "w", encoding="utf-8") as f:
            json.dump(manifest.to_dict(), f, indent=2)
        logger.info(f"Saved immutable forward snapshot ({len(candidate_records)} records) to {snap_path}")

        # Update persistent CSV ledger tables
        self._sync_ledger_tables(candidate_records, screening_date, overwrite=overwrite)

        return manifest

    def load_snapshot(self, screening_date: str) -> ForwardSnapshotManifest:
        """Load an immutable snapshot from disk."""
        snap_path = self.get_snapshot_path(screening_date)
        if not snap_path.exists():
            raise FileNotFoundError(f"No forward snapshot found for screening date: {screening_date} at {snap_path}")

        with open(snap_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        return ForwardSnapshotManifest(
            snapshot_id=data["snapshot_id"],
            screening_date=data["screening_date"],
            created_at_utc=data["created_at_utc"],
            engine_version=data["engine_version"],
            total_candidates=data["total_candidates"],
            category_counts=data["category_counts"],
            source_dataset_or_live=data.get("source_dataset_or_live", "N/A"),
            candidate_records=data.get("candidate_records", []),
        )

    def list_snapshots(self) -> list[dict[str, Any]]:
        """List all available forward screening snapshots sorted chronologically."""
        results = []
        for p in sorted(self.snapshots_dir.glob("snapshot_*.json")):
            try:
                with open(p, "r", encoding="utf-8") as f:
                    d = json.load(f)
                    results.append({
                        "snapshot_id": d.get("snapshot_id"),
                        "screening_date": d.get("screening_date"),
                        "created_at_utc": d.get("created_at_utc"),
                        "total_candidates": d.get("total_candidates"),
                        "category_counts": d.get("category_counts", {}),
                        "file_path": str(p),
                    })
            except Exception as exc:
                logger.warning(f"Error reading snapshot file {p}: {exc}")
        return results

    def load_ledger_dataframe(self) -> pd.DataFrame:
        """Load the master candidate ledger DataFrame."""
        if not self.ledger_csv_path.exists():
            return pd.DataFrame()
        return pd.read_csv(self.ledger_csv_path)

    def load_outcomes_dataframe(self) -> pd.DataFrame:
        """Load the forward outcomes tracking DataFrame."""
        if not self.outcomes_csv_path.exists():
            return pd.DataFrame()
        return pd.read_csv(self.outcomes_csv_path)

    def save_outcomes_dataframe(self, outcomes_df: pd.DataFrame) -> None:
        """Save updated forward outcomes DataFrame to disk."""
        outcomes_df.to_csv(self.outcomes_csv_path, index=False)
        logger.info(f"Updated forward outcomes ledger ({len(outcomes_df)} rows) at {self.outcomes_csv_path}")

    def _sync_ledger_tables(
        self,
        new_records: Sequence[ForwardCandidateRecord],
        screening_date: str,
        overwrite: bool,
    ) -> None:
        """Append or upsert candidate records into the master ledger and initialize pending outcome rows."""
        # 1. Update forward_ledger.csv
        new_ledger_df = pd.DataFrame([rec.to_dict() for rec in new_records])
        if self.ledger_csv_path.exists():
            existing_ledger_df = pd.read_csv(self.ledger_csv_path)
            if overwrite:
                # Remove prior records for this screening date
                existing_ledger_df = existing_ledger_df[existing_ledger_df["screening_date"] != str(screening_date)]
            combined_ledger_df = pd.concat([existing_ledger_df, new_ledger_df], ignore_index=True)
        else:
            combined_ledger_df = new_ledger_df

        # Deduplicate deterministically by candidate_id
        combined_ledger_df = combined_ledger_df.drop_duplicates(subset=["candidate_id"], keep="last")
        combined_ledger_df.sort_values(by=["screening_date", "composite_score"], ascending=[True, False], inplace=True)
        combined_ledger_df.to_csv(self.ledger_csv_path, index=False)

        # 2. Update forward_outcomes.csv (initialize pending records if not already tracked)
        existing_outcomes_df = self.load_outcomes_dataframe()
        existing_ids = set(existing_outcomes_df["candidate_id"].tolist()) if not existing_outcomes_df.empty else set()

        new_outcomes: list[dict[str, Any]] = []
        for rec in new_records:
            if rec.candidate_id in existing_ids and not overwrite:
                continue
            out_rec = ForwardOutcomeRecord(
                candidate_id=rec.candidate_id,
                symbol=rec.symbol,
                screening_date=rec.screening_date,
                reference_close_price=rec.reference_close_price,
                candidate_category=rec.candidate_category,
                composite_score=rec.composite_score,
                available_forward_bars=0,
                status_10d=HorizonStatus.PENDING.value,
                status_20d=HorizonStatus.PENDING.value,
                status_60d=HorizonStatus.PENDING.value,
                last_updated_date=rec.screening_date,
            )
            new_outcomes.append(out_rec.to_dict())

        if new_outcomes:
            new_outcomes_df = pd.DataFrame(new_outcomes)
            if not existing_outcomes_df.empty:
                if overwrite:
                    existing_outcomes_df = existing_outcomes_df[existing_outcomes_df["screening_date"] != str(screening_date)]
                combined_outcomes_df = pd.concat([existing_outcomes_df, new_outcomes_df], ignore_index=True)
            else:
                combined_outcomes_df = new_outcomes_df

            combined_outcomes_df = combined_outcomes_df.drop_duplicates(subset=["candidate_id"], keep="last")
            combined_outcomes_df.sort_values(by=["screening_date", "composite_score"], ascending=[True, False], inplace=True)
            combined_outcomes_df.to_csv(self.outcomes_csv_path, index=False)
