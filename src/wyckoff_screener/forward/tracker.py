"""Prospective forward price-path outcome tracking engine."""

from datetime import datetime, timezone
import logging
from pathlib import Path
from typing import Optional, Sequence, Union
import numpy as np
import pandas as pd

from wyckoff_screener.data_loader import validate_ohlcv_dataframe
from wyckoff_screener.forward.ledger import ForwardLedger
from wyckoff_screener.forward.models import ForwardOutcomeRecord, HorizonStatus
from wyckoff_screener.validation.metrics import calculate_forward_metrics_for_bar

logger = logging.getLogger(__name__)

DEFAULT_HORIZONS: Sequence[int] = (10, 20, 60)


def update_candidate_outcome(
    outcome: ForwardOutcomeRecord,
    ohlcv_df: pd.DataFrame,
    horizons: Sequence[int] = DEFAULT_HORIZONS,
) -> ForwardOutcomeRecord:
    """Update prospective forward return and excursion metrics for a single candidate.

    Args:
        outcome: ForwardOutcomeRecord to be updated.
        ohlcv_df: Full/latest OHLCV DataFrame for the security.
        horizons: Forward horizon trading bar counts (default 10, 20, 60).

    Returns:
        ForwardOutcomeRecord with updated forward outcomes and maturity statuses.
    """
    valid_df = validate_ohlcv_dataframe(ohlcv_df)

    # Normalize Date column to YYYY-MM-DD string
    dates_series = pd.to_datetime(valid_df["Date"]).dt.strftime("%Y-%m-%d")
    screening_date_str = str(outcome.screening_date).strip()

    # Locate the screening bar index T
    date_matches = np.where(dates_series.values == screening_date_str)[0]
    if len(date_matches) == 0:
        # Date not found in the provided OHLCV dataset
        logger.warning(
            f"Screening date {screening_date_str} for {outcome.symbol} not found in OHLCV dataset."
        )
        return outcome

    bar_idx = int(date_matches[0])
    total_bars = len(valid_df)
    available_forward_bars = total_bars - 1 - bar_idx

    outcome.available_forward_bars = max(0, available_forward_bars)

    prices_close = valid_df["Close"].to_numpy(dtype=float)
    prices_high = valid_df["High"].to_numpy(dtype=float)
    prices_low = valid_df["Low"].to_numpy(dtype=float)

    # Calculate audited forward metrics
    metrics = calculate_forward_metrics_for_bar(
        prices_close=prices_close,
        prices_high=prices_high,
        prices_low=prices_low,
        bar_idx=bar_idx,
        horizons=horizons,
    )

    # Update 10-day horizon
    if 10 in horizons:
        if available_forward_bars >= 10:
            outcome.status_10d = HorizonStatus.MATURED.value
            outcome.fwd_ret_10d = metrics.get("fwd_ret_10d")
            outcome.mfe_10d = metrics.get("mfe_10d")
            outcome.mae_10d = metrics.get("mae_10d")
        else:
            outcome.status_10d = HorizonStatus.PENDING.value
            outcome.fwd_ret_10d = None
            outcome.mfe_10d = None
            outcome.mae_10d = None

    # Update 20-day horizon
    if 20 in horizons:
        if available_forward_bars >= 20:
            outcome.status_20d = HorizonStatus.MATURED.value
            outcome.fwd_ret_20d = metrics.get("fwd_ret_20d")
            outcome.mfe_20d = metrics.get("mfe_20d")
            outcome.mae_20d = metrics.get("mae_20d")
        else:
            outcome.status_20d = HorizonStatus.PENDING.value
            outcome.fwd_ret_20d = None
            outcome.mfe_20d = None
            outcome.mae_20d = None

    # Update 60-day horizon
    if 60 in horizons:
        if available_forward_bars >= 60:
            outcome.status_60d = HorizonStatus.MATURED.value
            outcome.fwd_ret_60d = metrics.get("fwd_ret_60d")
            outcome.mfe_60d = metrics.get("mfe_60d")
            outcome.mae_60d = metrics.get("mae_60d")
        else:
            outcome.status_60d = HorizonStatus.PENDING.value
            outcome.fwd_ret_60d = None
            outcome.mfe_60d = None
            outcome.mae_60d = None

    outcome.last_updated_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    return outcome


def update_all_forward_outcomes(
    ledger: ForwardLedger,
    data_dir: Union[str, Path],
    horizons: Sequence[int] = DEFAULT_HORIZONS,
) -> tuple[int, int]:
    """Scan all registered candidates in the ledger and update matured outcomes from market data.

    Args:
        ledger: ForwardLedger instance.
        data_dir: Path to directory containing security CSV files (e.g. data/research_datasets/.../data).
        horizons: Horizons to evaluate.

    Returns:
        tuple[int, int]: (total_candidates_processed, total_matured_horizons_count)
    """
    data_path = Path(data_dir)
    if not data_path.exists():
        raise FileNotFoundError(f"Market data directory not found at: {data_path}")

    outcomes_df = ledger.load_outcomes_dataframe()
    if outcomes_df.empty:
        logger.info("Forward outcomes ledger is empty; no records to update.")
        return 0, 0

    updated_records: list[dict] = []
    matured_count = 0

    for _, row in outcomes_df.iterrows():
        rec = ForwardOutcomeRecord(
            candidate_id=str(row["candidate_id"]),
            symbol=str(row["symbol"]),
            screening_date=str(row["screening_date"]),
            reference_close_price=float(row["reference_close_price"]),
            candidate_category=str(row["candidate_category"]),
            composite_score=float(row["composite_score"]),
            available_forward_bars=int(row.get("available_forward_bars", 0)),
            status_10d=str(row.get("status_10d", HorizonStatus.PENDING.value)),
            status_20d=str(row.get("status_20d", HorizonStatus.PENDING.value)),
            status_60d=str(row.get("status_60d", HorizonStatus.PENDING.value)),
            fwd_ret_10d=float(row["fwd_ret_10d"]) if pd.notna(row.get("fwd_ret_10d")) else None,
            fwd_ret_20d=float(row["fwd_ret_20d"]) if pd.notna(row.get("fwd_ret_20d")) else None,
            fwd_ret_60d=float(row["fwd_ret_60d"]) if pd.notna(row.get("fwd_ret_60d")) else None,
            mfe_10d=float(row["mfe_10d"]) if pd.notna(row.get("mfe_10d")) else None,
            mae_10d=float(row["mae_10d"]) if pd.notna(row.get("mae_10d")) else None,
            mfe_20d=float(row["mfe_20d"]) if pd.notna(row.get("mfe_20d")) else None,
            mae_20d=float(row["mae_20d"]) if pd.notna(row.get("mae_20d")) else None,
            mfe_60d=float(row["mfe_60d"]) if pd.notna(row.get("mfe_60d")) else None,
            mae_60d=float(row["mae_60d"]) if pd.notna(row.get("mae_60d")) else None,
            last_updated_date=str(row.get("last_updated_date", "")),
        )

        sym = rec.symbol
        # Try both SYMBOL.NS.csv and SYMBOL.csv
        csv_path = data_path / f"{sym}.NS.csv"
        if not csv_path.exists():
            csv_path = data_path / f"{sym}.csv"

        if csv_path.exists():
            try:
                df = pd.read_csv(csv_path)
                rec = update_candidate_outcome(rec, df, horizons=horizons)
            except Exception as exc:
                logger.warning(f"Failed to update outcome for {sym}: {exc}")
        else:
            logger.debug(f"No OHLCV file found for {sym} at {data_path}")

        updated_records.append(rec.to_dict())
        if rec.status_10d == HorizonStatus.MATURED.value:
            matured_count += 1
        if rec.status_20d == HorizonStatus.MATURED.value:
            matured_count += 1
        if rec.status_60d == HorizonStatus.MATURED.value:
            matured_count += 1

    new_outcomes_df = pd.DataFrame(updated_records)
    ledger.save_outcomes_dataframe(new_outcomes_df)

    return len(updated_records), matured_count
