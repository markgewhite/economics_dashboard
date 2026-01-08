"""Transformer for HM Land Registry housing data."""

from typing import Optional

import pandas as pd

from data.transformers.base import BaseTransformer
from data.models.housing import (
    Region,
    HousingDataPoint,
    HousingMetrics,
    HousingTimeSeries,
    RegionalHousingData,
)
from data.clients.base import FetchResult


class HousingTransformer(BaseTransformer[RegionalHousingData]):
    """
    Transform Land Registry data into housing time series.

    Handles:
    - Multiple regions
    - Missing sales volume (recent months suppressed)
    - Metric calculations
    - Heat map data preparation
    """

    # Expected value ranges
    VALIDATION_RANGES = {
        "average_price": (30000, 2000000),
        "house_price_index": (50, 300),
        "annual_change_pct": (-30, 50),
    }

    def transform(
        self,
        raw_data: dict[Region, FetchResult[pd.DataFrame]],
    ) -> RegionalHousingData:
        """
        Transform raw Land Registry data for all regions.

        Args:
            raw_data: Dict mapping Region to FetchResult from
                     LandRegistryClient.fetch_all_regions()

        Returns:
            RegionalHousingData with all regions
        """
        self._clear_warnings()

        regions = {}

        for region, result in raw_data.items():
            if not result.success or result.data is None:
                self._add_warning(
                    f"No data for {region.display_name}: {result.error_message}"
                )
                continue

            ts = self._transform_region(region, result.data)
            if ts:
                regions[region] = ts

        return RegionalHousingData(regions=regions)

    def transform_single(
        self,
        region: Region,
        raw_data: pd.DataFrame,
    ) -> Optional[HousingTimeSeries]:
        """
        Transform data for a single region.

        Convenience method for transforming individual region data.

        Args:
            region: Region enum value
            raw_data: DataFrame from LandRegistryClient.fetch()

        Returns:
            HousingTimeSeries for the region
        """
        self._clear_warnings()
        return self._transform_region(region, raw_data)

    def _transform_region(
        self,
        region: Region,
        df: pd.DataFrame,
    ) -> Optional[HousingTimeSeries]:
        """Transform data for a single region."""
        if df.empty:
            return None

        df = df.copy()

        # Ensure date column is datetime
        df["ref_month"] = pd.to_datetime(df["ref_month"])

        # Validate ranges
        for col, (min_val, max_val) in self.VALIDATION_RANGES.items():
            if col in df.columns:
                self._validate_range(df, col, min_val, max_val)

        # Sort by date
        df = df.sort_values("ref_month").reset_index(drop=True)

        # Create data points
        data_points = []
        for _, row in df.iterrows():
            data_points.append(
                HousingDataPoint(
                    ref_month=row["ref_month"].date(),
                    region=region,
                    average_price=float(row["average_price"]),
                    house_price_index=float(row["house_price_index"]),
                    monthly_change_pct=self._safe_float(row.get("monthly_change_pct")) or 0,
                    annual_change_pct=self._safe_float(row.get("annual_change_pct")) or 0,
                    sales_volume=self._safe_int(row.get("sales_volume")),
                    price_detached=self._safe_float(row.get("price_detached")),
                    price_semi_detached=self._safe_float(row.get("price_semi_detached")),
                    price_terraced=self._safe_float(row.get("price_terraced")),
                    price_flat=self._safe_float(row.get("price_flat")),
                )
            )

        # Calculate metrics
        metrics = self._calculate_metrics(region, df)

        return HousingTimeSeries(
            region=region,
            data_points=data_points,
            metrics=metrics,
        )

    def _safe_float(self, value) -> Optional[float]:
        """Convert value to float, returning None for NaN."""
        if pd.isna(value):
            return None
        return float(value)

    def _safe_int(self, value) -> Optional[int]:
        """Convert value to int, returning None for NaN."""
        if pd.isna(value):
            return None
        return int(value)

    def _calculate_metrics(
        self,
        region: Region,
        df: pd.DataFrame,
    ) -> Optional[HousingMetrics]:
        """Calculate metrics for a region."""
        if df.empty:
            return None

        df = df.sort_values("ref_month")
        latest = df.iloc[-1]

        return HousingMetrics(
            region=region,
            current_average_price=float(latest["average_price"]),
            current_index=float(latest["house_price_index"]),
            price_change_yoy=self._safe_float(latest.get("annual_change_pct")) or 0,
            price_change_mom=self._safe_float(latest.get("monthly_change_pct")) or 0,
            latest_month=latest["ref_month"].date(),
        )
