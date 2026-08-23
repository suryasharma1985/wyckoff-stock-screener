"""Batch data downloader, caching package, and canonical research dataset builders."""

from wyckoff_screener.data.batch_downloader import (
    BatchDownloadResult,
    BatchMarketDataDownloader,
    DataQualityReport,
    DownloadFailure,
    download_and_cache_universe,
)
from wyckoff_screener.data.dataset_builder import (
    ResearchDatasetManifest,
    ResearchDatasetResult,
    build_research_dataset,
)

__all__ = [
    "BatchDownloadResult",
    "BatchMarketDataDownloader",
    "DataQualityReport",
    "DownloadFailure",
    "download_and_cache_universe",
    "ResearchDatasetManifest",
    "ResearchDatasetResult",
    "build_research_dataset",
]
