"""Cache manager for file-based data persistence."""

from pathlib import Path
from datetime import datetime
from typing import Optional
import logging

import pandas as pd

from data.models.cache import CacheMetadata, RefreshReason
from data.cache.scheduler import RefreshScheduler, RefreshDecision
from data.exceptions import CacheReadError, CacheWriteError


class CacheManager:
    """
    Manages file-based cache for dashboard data.

    Cache structure:
    - storage/processed/{dataset}.parquet - Transformed data
    - storage/metadata/{dataset}.json - Cache metadata
    """

    DATASETS = ["monetary", "housing", "economic"]

    def __init__(self, cache_dir: Path, scheduler: Optional[RefreshScheduler] = None):
        self.cache_dir = Path(cache_dir)
        self.processed_dir = self.cache_dir / "processed"
        self.metadata_dir = self.cache_dir / "metadata"
        self.logger = logging.getLogger(__name__)
        self._scheduler = scheduler

        self._ensure_directories()

    @property
    def scheduler(self) -> RefreshScheduler:
        """Lazy-initialized scheduler."""
        if self._scheduler is None:
            self._scheduler = RefreshScheduler()
        return self._scheduler

    def _ensure_directories(self):
        """Create cache directories if they don't exist."""
        self.processed_dir.mkdir(parents=True, exist_ok=True)
        self.metadata_dir.mkdir(parents=True, exist_ok=True)

    def get(
        self,
        dataset: str,
    ) -> tuple[Optional[pd.DataFrame], Optional[CacheMetadata]]:
        """
        Retrieve cached data and metadata.

        Args:
            dataset: Dataset identifier ("monetary", "housing", "economic")

        Returns:
            Tuple of (data, metadata) - both None if not cached
        """
        data_path = self.processed_dir / f"{dataset}.parquet"
        meta_path = self.metadata_dir / f"{dataset}.json"

        if not data_path.exists() or not meta_path.exists():
            self.logger.debug(f"Cache miss for {dataset}")
            return None, None

        try:
            # Load data
            df = pd.read_parquet(data_path)

            # Load metadata
            metadata = CacheMetadata.from_json(meta_path.read_text())

            self.logger.debug(f"Cache hit for {dataset}: {len(df)} rows")
            return df, metadata

        except Exception as e:
            self.logger.warning(f"Failed to read cache for {dataset}: {e}")
            return None, None

    def put(
        self,
        dataset: str,
        data: pd.DataFrame,
        refresh_reason: RefreshReason,
    ) -> CacheMetadata:
        """
        Store data in cache with metadata.

        Args:
            dataset: Dataset identifier
            data: DataFrame to cache
            refresh_reason: Reason for this cache write

        Returns:
            Generated CacheMetadata

        Raises:
            CacheWriteError: If unable to write to cache
        """
        data_path = self.processed_dir / f"{dataset}.parquet"
        meta_path = self.metadata_dir / f"{dataset}.json"

        now = datetime.now()

        # Calculate next expected update
        decision = self.scheduler.should_refresh(dataset, now)

        # Determine latest data date
        date_columns = ["date", "ref_month", "observation_date"]
        data_date = None
        for col in date_columns:
            if col in data.columns:
                data_date = pd.to_datetime(data[col]).max()
                break

        data_date_str = data_date.strftime("%Y-%m-%d") if data_date else "unknown"

        # Create metadata
        metadata = CacheMetadata(
            dataset=dataset,
            last_fetch=now,
            next_expected=decision.next_expected,
            data_date=data_date_str,
            refresh_reason=refresh_reason,
            record_count=len(data),
        )

        try:
            # Write data
            data.to_parquet(data_path, index=False)

            # Write metadata
            meta_path.write_text(metadata.to_json())

            self.logger.info(
                f"Cached {dataset}: {len(data)} rows, "
                f"data through {data_date_str}"
            )

            return metadata

        except Exception as e:
            self.logger.error(f"Failed to write cache for {dataset}: {e}")
            raise CacheWriteError(dataset, str(e)) from e

    def get_metadata(self, dataset: str) -> Optional[CacheMetadata]:
        """Load metadata without loading full dataset."""
        meta_path = self.metadata_dir / f"{dataset}.json"

        if not meta_path.exists():
            return None

        try:
            return CacheMetadata.from_json(meta_path.read_text())
        except Exception as e:
            self.logger.warning(f"Failed to read metadata for {dataset}: {e}")
            return None

    def needs_refresh(self, dataset: str) -> RefreshDecision:
        """
        Check if dataset needs refresh based on cache state.

        Args:
            dataset: Dataset identifier

        Returns:
            RefreshDecision indicating whether refresh is needed
        """
        metadata = self.get_metadata(dataset)

        if metadata is None:
            return self.scheduler.should_refresh(dataset, None)

        return self.scheduler.should_refresh(dataset, metadata.last_fetch)

    def mark_stale(self, dataset: str) -> None:
        """
        Mark cached data as stale (fetch failed, using old data).

        Args:
            dataset: Dataset identifier
        """
        meta_path = self.metadata_dir / f"{dataset}.json"

        if not meta_path.exists():
            return

        try:
            metadata = CacheMetadata.from_json(meta_path.read_text())
            metadata = CacheMetadata(
                dataset=metadata.dataset,
                last_fetch=metadata.last_fetch,
                next_expected=metadata.next_expected,
                data_date=metadata.data_date,
                refresh_reason=RefreshReason.FETCH_FAILED_USING_STALE,
                record_count=metadata.record_count,
                is_stale=True,
            )
            meta_path.write_text(metadata.to_json())
            self.logger.info(f"Marked {dataset} cache as stale")

        except Exception as e:
            self.logger.warning(f"Failed to mark {dataset} as stale: {e}")

    def invalidate(self, dataset: str) -> None:
        """Remove cached data for dataset."""
        data_path = self.processed_dir / f"{dataset}.parquet"
        meta_path = self.metadata_dir / f"{dataset}.json"

        for path in [data_path, meta_path]:
            if path.exists():
                path.unlink()

        self.logger.info(f"Invalidated cache for {dataset}")

    def invalidate_all(self) -> None:
        """Clear entire cache."""
        for dataset in self.DATASETS:
            self.invalidate(dataset)

    def get_all_metadata(self) -> dict[str, Optional[CacheMetadata]]:
        """Get metadata for all datasets."""
        return {dataset: self.get_metadata(dataset) for dataset in self.DATASETS}

    def get_cache_status(self) -> dict[str, dict]:
        """
        Get comprehensive status of all cached datasets.

        Returns:
            Dict with dataset status including:
            - cached: bool
            - stale: bool
            - record_count: int
            - data_date: str
            - age_description: str
            - needs_refresh: bool
        """
        status = {}

        for dataset in self.DATASETS:
            metadata = self.get_metadata(dataset)

            if metadata is None:
                status[dataset] = {
                    "cached": False,
                    "stale": False,
                    "record_count": 0,
                    "data_date": None,
                    "age_description": "Not cached",
                    "needs_refresh": True,
                }
            else:
                decision = self.scheduler.should_refresh(dataset, metadata.last_fetch)
                status[dataset] = {
                    "cached": True,
                    "stale": metadata.is_stale,
                    "record_count": metadata.record_count,
                    "data_date": metadata.data_date,
                    "age_description": metadata.age_description,
                    "needs_refresh": decision.should_refresh,
                    "next_update": metadata.next_update_description,
                }

        return status

    def exists(self, dataset: str) -> bool:
        """Check if dataset is cached."""
        data_path = self.processed_dir / f"{dataset}.parquet"
        meta_path = self.metadata_dir / f"{dataset}.json"
        return data_path.exists() and meta_path.exists()
