"""Universe source abstractions for ingesting NSE equity constituent records."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timezone
import io
import os
from pathlib import Path
from typing import Any, Optional, Sequence, Union
import urllib.error
import urllib.request
import pandas as pd


@dataclass
class RawUniverseData:
    """Container for raw universe records and provenance metadata."""

    source_name: str
    source_date: str
    source_identifier: str
    dataframe: pd.DataFrame
    fetch_success: bool = True
    error_message: Optional[str] = None


class UniverseSource(ABC):
    """Abstract interface for universe data sources."""

    @property
    @abstractmethod
    def source_name(self) -> str:
        """Human-readable identifier for this universe source."""
        pass

    @abstractmethod
    def fetch_raw_records(self) -> RawUniverseData:
        """Fetch raw universe constituent records.

        Returns:
            RawUniverseData container with raw DataFrame and provenance.
        """
        pass


class LocalCsvUniverseSource(UniverseSource):
    """Loads universe records from a local CSV file (e.g. sample or custom universe)."""

    def __init__(self, csv_path: Union[str, Path], source_name: Optional[str] = None):
        self.csv_path = Path(csv_path)
        self._source_name = source_name or f"local_csv:{self.csv_path.name}"

    @property
    def source_name(self) -> str:
        return self._source_name

    def fetch_raw_records(self) -> RawUniverseData:
        retrieval_date = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        if not self.csv_path.exists():
            return RawUniverseData(
                source_name=self.source_name,
                source_date=retrieval_date,
                source_identifier=str(self.csv_path),
                dataframe=pd.DataFrame(),
                fetch_success=False,
                error_message=f"Local universe file not found: {self.csv_path}",
            )

        try:
            df = pd.read_csv(self.csv_path)
            return RawUniverseData(
                source_name=self.source_name,
                source_date=retrieval_date,
                source_identifier=str(self.csv_path),
                dataframe=df,
                fetch_success=True,
            )
        except Exception as exc:
            return RawUniverseData(
                source_name=self.source_name,
                source_date=retrieval_date,
                source_identifier=str(self.csv_path),
                dataframe=pd.DataFrame(),
                fetch_success=False,
                error_message=f"Failed to read CSV at {self.csv_path}: {exc}",
            )


class NseOfficialEquitySource(UniverseSource):
    """Fetches currently listed equity securities from official NSE archives.

    URL: https://archives.nseindia.com/content/equities/EQUITY_L.csv
    Expected headers: SYMBOL, NAME OF COMPANY, SERIES, DATE OF LISTING, etc.
    """

    OFFICIAL_NSE_EQUITY_URL: str = "https://archives.nseindia.com/content/equities/EQUITY_L.csv"
    DEFAULT_TIMEOUT_SEC: int = 15
    DEFAULT_USER_AGENT: str = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )

    def __init__(
        self,
        url: Optional[str] = None,
        timeout_sec: int = DEFAULT_TIMEOUT_SEC,
        user_agent: Optional[str] = None,
    ):
        self.url = url or self.OFFICIAL_NSE_EQUITY_URL
        self.timeout_sec = timeout_sec
        self.user_agent = user_agent or self.DEFAULT_USER_AGENT

    @property
    def source_name(self) -> str:
        return "nse_official_equity_archive"

    def fetch_raw_records(self) -> RawUniverseData:
        retrieval_date = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        req = urllib.request.Request(
            self.url,
            headers={"User-Agent": self.user_agent, "Accept": "text/csv, text/plain, */*"},
        )

        try:
            with urllib.request.urlopen(req, timeout=self.timeout_sec) as response:
                if response.status != 200:
                    return RawUniverseData(
                        source_name=self.source_name,
                        source_date=retrieval_date,
                        source_identifier=self.url,
                        dataframe=pd.DataFrame(),
                        fetch_success=False,
                        error_message=f"HTTP status {response.status} from {self.url}",
                    )
                raw_bytes = response.read()
                csv_text = raw_bytes.decode("utf-8", errors="replace")
                df = pd.read_csv(io.StringIO(csv_text))
                return RawUniverseData(
                    source_name=self.source_name,
                    source_date=retrieval_date,
                    source_identifier=self.url,
                    dataframe=df,
                    fetch_success=True,
                )
        except Exception as exc:
            return RawUniverseData(
                source_name=self.source_name,
                source_date=retrieval_date,
                source_identifier=self.url,
                dataframe=pd.DataFrame(),
                fetch_success=False,
                error_message=f"Failed to fetch from {self.url}: {type(exc).__name__} - {exc}",
            )


def get_universe_source(source_type: str = "sample", **kwargs: Any) -> UniverseSource:
    """Factory for obtaining universe source instances.

    Supported source types:
      - 'sample': Local CSV at data/sample_nse_symbols.csv
      - 'nse_eq' / 'official': NseOfficialEquitySource (live from archives.nseindia.com)
      - 'custom_csv' / 'local': LocalCsvUniverseSource (requires csv_path kwarg)
    """
    clean_type = source_type.strip().lower()
    if clean_type == "sample":
        default_sample = Path("data/sample_nse_symbols.csv")
        csv_path = kwargs.get("csv_path", default_sample)
        return LocalCsvUniverseSource(csv_path=csv_path, source_name="sample_nse_symbols")
    elif clean_type in ("nse_eq", "official", "nse_official"):
        url = kwargs.get("url")
        timeout = kwargs.get("timeout_sec", NseOfficialEquitySource.DEFAULT_TIMEOUT_SEC)
        return NseOfficialEquitySource(url=url, timeout_sec=timeout)
    elif clean_type in ("custom_csv", "local", "csv"):
        csv_path = kwargs.get("csv_path")
        if not csv_path:
            raise ValueError("custom_csv source requires 'csv_path' argument.")
        source_name = kwargs.get("source_name")
        return LocalCsvUniverseSource(csv_path=csv_path, source_name=source_name)
    else:
        raise ValueError(
            f"Unknown universe source type '{source_type}'. Supported: 'sample', 'nse_eq', 'custom_csv'."
        )
