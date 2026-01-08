"""Data service layer orchestrating API clients, transformers, and cache."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Callable, Any
import logging

import pandas as pd

from data.clients.bank_of_england import BankOfEnglandClient
from data.clients.land_registry import LandRegistryClient
from data.clients.ons import ONSClient
from data.clients.base import FetchResult
from data.transformers.monetary import MonetaryTransformer
from data.transformers.housing import HousingTransformer
from data.transformers.economic import EconomicTransformer
from data.cache.manager import CacheManager
from data.cache.scheduler import RefreshScheduler
from data.models.monetary import MonetaryTimeSeries
from data.models.housing import RegionalHousingData, Region
from data.models.economic import EconomicTimeSeries
from data.models.cache import CacheMetadata, RefreshReason


@dataclass
class DashboardData:
    """Complete dataset for dashboard rendering."""

    monetary: Optional[MonetaryTimeSeries] = None
    housing: Optional[RegionalHousingData] = None
    economic: Optional[EconomicTimeSeries] = None
    metadata: dict[str, Optional[CacheMetadata]] = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def is_complete(self) -> bool:
        """Check if all data sources loaded successfully."""
        return all([
            self.monetary is not None,
            self.housing is not None,
            self.economic is not None,
        ])

    @property
    def has_errors(self) -> bool:
        """Check if any errors occurred."""
        return len(self.errors) > 0

    @property
    def has_warnings(self) -> bool:
        """Check if any warnings were generated."""
        return len(self.warnings) > 0

    @property
    def has_any_data(self) -> bool:
        """Check if at least some data is available."""
        return any([
            self.monetary is not None,
            self.housing is not None,
            self.economic is not None,
        ])


class DataService:
    """
    High-level service orchestrating data fetching and caching.

    This is the main interface for the presentation layer.
    Implements graceful degradation - continues with partial data
    when some sources fail.
    """

    def __init__(self, cache_dir: Path):
        self.logger = logging.getLogger(__name__)
        self.cache_dir = Path(cache_dir)

        # Initialize scheduler first (shared)
        self.scheduler = RefreshScheduler()

        # Initialize cache with scheduler
        self.cache = CacheManager(self.cache_dir, scheduler=self.scheduler)

        # Initialize clients (lazy - only created when needed)
        self._boe_client: Optional[BankOfEnglandClient] = None
        self._lr_client: Optional[LandRegistryClient] = None
        self._ons_client: Optional[ONSClient] = None

        # Initialize transformers
        self.monetary_transformer = MonetaryTransformer()
        self.housing_transformer = HousingTransformer()
        self.economic_transformer = EconomicTransformer()

    @property
    def boe_client(self) -> BankOfEnglandClient:
        """Lazy-initialized Bank of England client."""
        if self._boe_client is None:
            self._boe_client = BankOfEnglandClient()
        return self._boe_client

    @property
    def lr_client(self) -> LandRegistryClient:
        """Lazy-initialized Land Registry client."""
        if self._lr_client is None:
            self._lr_client = LandRegistryClient()
        return self._lr_client

    @property
    def ons_client(self) -> ONSClient:
        """Lazy-initialized ONS client."""
        if self._ons_client is None:
            self._ons_client = ONSClient()
        return self._ons_client

    def get_dashboard_data(
        self,
        force_refresh: bool = False,
    ) -> DashboardData:
        """
        Get all data for dashboard, using cache when appropriate.

        Args:
            force_refresh: If True, bypass cache and fetch fresh data

        Returns:
            DashboardData with all datasets and metadata
        """
        errors = []
        warnings = []
        metadata = {}

        # Fetch each dataset with error handling
        monetary, meta, transformer_warnings = self._get_monetary_data(force_refresh)
        metadata["monetary"] = meta
        warnings.extend(transformer_warnings)
        if monetary is None:
            errors.append("Failed to load monetary data")

        housing, meta, transformer_warnings = self._get_housing_data(force_refresh)
        metadata["housing"] = meta
        warnings.extend(transformer_warnings)
        if housing is None:
            errors.append("Failed to load housing data")

        economic, meta, transformer_warnings = self._get_economic_data(force_refresh)
        metadata["economic"] = meta
        warnings.extend(transformer_warnings)
        if economic is None:
            errors.append("Failed to load economic data")

        return DashboardData(
            monetary=monetary,
            housing=housing,
            economic=economic,
            metadata=metadata,
            errors=errors,
            warnings=warnings,
        )

    def _get_monetary_data(
        self,
        force_refresh: bool,
    ) -> tuple[Optional[MonetaryTimeSeries], Optional[CacheMetadata], list[str]]:
        """Fetch or retrieve monetary data."""
        dataset = "monetary"
        warnings = []

        # Check cache state
        cached_df, cached_meta = self.cache.get(dataset)
        should_refresh, refresh_reason = self._should_refresh(
            dataset, cached_meta, force_refresh
        )

        # Use cache if fresh
        if not should_refresh and cached_df is not None:
            self.logger.info(f"Using cached {dataset} data")
            result = self.monetary_transformer.transform(cached_df)
            warnings.extend(self.monetary_transformer.warnings)
            return result, cached_meta, warnings

        # Fetch fresh data
        self.logger.info(f"Fetching fresh {dataset} data")
        fetch_result = self.boe_client.fetch()

        if fetch_result.success and fetch_result.data is not None:
            # Transform
            result = self.monetary_transformer.transform(fetch_result.data)
            warnings.extend(self.monetary_transformer.warnings)

            # Cache raw data
            meta = self.cache.put(dataset, fetch_result.data, refresh_reason)

            return result, meta, warnings

        # Fetch failed - fall back to stale cache
        if cached_df is not None and cached_meta is not None:
            self.logger.warning(f"Fetch failed for {dataset}, using stale cache")
            self.cache.mark_stale(dataset)
            result = self.monetary_transformer.transform(cached_df)
            warnings.extend(self.monetary_transformer.warnings)
            warnings.append(f"Using stale {dataset} data (fetch failed)")
            return result, cached_meta, warnings

        # No data available
        self.logger.error(f"No data available for {dataset}")
        return None, None, warnings

    def _get_housing_data(
        self,
        force_refresh: bool,
    ) -> tuple[Optional[RegionalHousingData], Optional[CacheMetadata], list[str]]:
        """Fetch or retrieve housing data."""
        dataset = "housing"
        warnings = []

        # Check cache state
        cached_df, cached_meta = self.cache.get(dataset)
        should_refresh, refresh_reason = self._should_refresh(
            dataset, cached_meta, force_refresh
        )

        # Use cache if fresh
        if not should_refresh and cached_df is not None:
            self.logger.info(f"Using cached {dataset} data")
            result = self._transform_cached_housing(cached_df)
            return result, cached_meta, warnings

        # Fetch fresh data from all regions
        self.logger.info(f"Fetching fresh {dataset} data")
        fetch_results = self.lr_client.fetch_all_regions()

        # Check if any succeeded
        successful = {r: res for r, res in fetch_results.items() if res.success}

        if successful:
            # Transform
            result = self.housing_transformer.transform(fetch_results)
            warnings.extend(self.housing_transformer.warnings)

            # Cache as combined DataFrame
            cache_df = self._housing_to_dataframe(fetch_results)
            meta = self.cache.put(dataset, cache_df, refresh_reason)

            return result, meta, warnings

        # All fetches failed - fall back to stale cache
        if cached_df is not None and cached_meta is not None:
            self.logger.warning(f"Fetch failed for {dataset}, using stale cache")
            self.cache.mark_stale(dataset)
            result = self._transform_cached_housing(cached_df)
            warnings.append(f"Using stale {dataset} data (fetch failed)")
            return result, cached_meta, warnings

        # No data available
        self.logger.error(f"No data available for {dataset}")
        return None, None, warnings

    def _get_economic_data(
        self,
        force_refresh: bool,
    ) -> tuple[Optional[EconomicTimeSeries], Optional[CacheMetadata], list[str]]:
        """Fetch or retrieve economic data."""
        dataset = "economic"
        warnings = []

        # Check cache state
        cached_df, cached_meta = self.cache.get(dataset)
        should_refresh, refresh_reason = self._should_refresh(
            dataset, cached_meta, force_refresh
        )

        # Use cache if fresh
        if not should_refresh and cached_df is not None:
            self.logger.info(f"Using cached {dataset} data")
            result = self._transform_cached_economic(cached_df)
            return result, cached_meta, warnings

        # Fetch fresh data
        self.logger.info(f"Fetching fresh {dataset} data")
        fetch_results = self.ons_client.fetch_all()

        # Check if any succeeded
        successful = {n: res for n, res in fetch_results.items() if res.success}

        if successful:
            # Transform
            result = self.economic_transformer.transform(fetch_results)
            warnings.extend(self.economic_transformer.warnings)

            # Cache as combined DataFrame
            cache_df = self._economic_to_dataframe(fetch_results)
            meta = self.cache.put(dataset, cache_df, refresh_reason)

            return result, meta, warnings

        # All fetches failed - fall back to stale cache
        if cached_df is not None and cached_meta is not None:
            self.logger.warning(f"Fetch failed for {dataset}, using stale cache")
            self.cache.mark_stale(dataset)
            result = self._transform_cached_economic(cached_df)
            warnings.append(f"Using stale {dataset} data (fetch failed)")
            return result, cached_meta, warnings

        # No data available
        self.logger.error(f"No data available for {dataset}")
        return None, None, warnings

    def _should_refresh(
        self,
        dataset: str,
        cached_meta: Optional[CacheMetadata],
        force_refresh: bool,
    ) -> tuple[bool, RefreshReason]:
        """Determine if dataset needs refresh."""
        if force_refresh:
            return True, RefreshReason.FORCED_REFRESH

        if cached_meta is None:
            return True, RefreshReason.INITIAL_FETCH

        decision = self.scheduler.should_refresh(dataset, cached_meta.last_fetch)
        return decision.should_refresh, decision.reason

    def _housing_to_dataframe(
        self,
        results: dict[Region, FetchResult[pd.DataFrame]],
    ) -> pd.DataFrame:
        """Convert housing fetch results to cacheable DataFrame."""
        dfs = []
        for region, result in results.items():
            if result.success and result.data is not None:
                df = result.data.copy()
                df["region"] = region.value
                dfs.append(df)

        if not dfs:
            return pd.DataFrame()

        return pd.concat(dfs, ignore_index=True)

    def _transform_cached_housing(
        self,
        cached_df: pd.DataFrame,
    ) -> Optional[RegionalHousingData]:
        """Transform cached housing DataFrame back to domain model."""
        if cached_df.empty:
            return None

        # Reconstruct per-region DataFrames and wrap in FetchResults
        results = {}
        for region in Region:
            region_df = cached_df[cached_df["region"] == region.value].copy()
            if not region_df.empty:
                results[region] = FetchResult.ok(region_df)
            else:
                results[region] = FetchResult.error("No cached data for region")

        return self.housing_transformer.transform(results)

    def _economic_to_dataframe(
        self,
        results: dict[str, FetchResult[pd.DataFrame]],
    ) -> pd.DataFrame:
        """Convert economic fetch results to cacheable DataFrame."""
        merged = None

        for name, result in results.items():
            if not result.success or result.data is None:
                continue

            df = result.data.copy()
            df["date"] = pd.to_datetime(df["date"])
            df = df.rename(columns={"value": name})
            df = df[["date", name]]

            if merged is None:
                merged = df
            else:
                merged = pd.merge(merged, df, on="date", how="outer")

        if merged is not None:
            merged = merged.sort_values("date").reset_index(drop=True)
            return merged

        return pd.DataFrame()

    def _transform_cached_economic(
        self,
        cached_df: pd.DataFrame,
    ) -> Optional[EconomicTimeSeries]:
        """Transform cached economic DataFrame back to domain model."""
        if cached_df.empty:
            return None

        # Reconstruct per-dataset DataFrames and wrap in FetchResults
        results = {}
        for dataset in ["cpi", "employment", "retail_sales"]:
            if dataset in cached_df.columns:
                df = cached_df[["date", dataset]].copy()
                df = df.rename(columns={dataset: "value"})
                df["dataset"] = dataset
                df = df.dropna(subset=["value"])
                results[dataset] = FetchResult.ok(df)
            else:
                results[dataset] = FetchResult.error("No cached data for dataset")

        return self.economic_transformer.transform(results)

    def get_refresh_status(self) -> dict[str, dict]:
        """
        Get refresh status for all datasets.

        Returns:
            Dict with status info for each dataset
        """
        return self.cache.get_cache_status()

    def invalidate_cache(self, dataset: Optional[str] = None) -> None:
        """
        Invalidate cached data.

        Args:
            dataset: Specific dataset to invalidate, or None for all
        """
        if dataset:
            self.cache.invalidate(dataset)
        else:
            self.cache.invalidate_all()

    def close(self) -> None:
        """Clean up resources."""
        if self._boe_client:
            self._boe_client.close()
        if self._lr_client:
            self._lr_client.close()
        if self._ons_client:
            self._ons_client.close()

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
        return False
