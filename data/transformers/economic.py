"""Transformer for ONS economic data."""

from typing import Optional

import pandas as pd

from data.transformers.base import BaseTransformer
from data.models.economic import (
    EconomicDataPoint,
    EconomicMetrics,
    EconomicTimeSeries,
)
from data.clients.base import FetchResult


class EconomicTransformer(BaseTransformer[EconomicTimeSeries]):
    """
    Transform ONS data into economic time series.

    Handles:
    - Merging multiple datasets (CPI, employment, retail)
    - Aligning to monthly frequency
    - Metric calculations
    """

    # Expected value ranges
    VALIDATION_RANGES = {
        "cpi": (-5, 20),
        "employment": (50, 90),
        "retail_sales": (50, 200),
    }

    def transform(
        self,
        raw_data: dict[str, FetchResult[pd.DataFrame]],
    ) -> EconomicTimeSeries:
        """
        Transform raw ONS data to EconomicTimeSeries.

        Args:
            raw_data: Dict mapping dataset name to FetchResult from
                     ONSClient.fetch_all()

        Returns:
            EconomicTimeSeries with merged data
        """
        self._clear_warnings()

        # Extract successful fetches
        datasets = {}
        for name, result in raw_data.items():
            if result.success and result.data is not None:
                datasets[name] = result.data
            else:
                self._add_warning(
                    f"No data for {name}: {result.error_message}"
                )

        if not datasets:
            return EconomicTimeSeries()

        # Merge datasets on date
        merged = self._merge_datasets(datasets)

        if merged.empty:
            return EconomicTimeSeries()

        # Create data points
        data_points = [
            EconomicDataPoint(
                ref_month=row["date"].date(),
                cpi_annual_rate=self._safe_float(row.get("cpi")),
                employment_rate=self._safe_float(row.get("employment")),
                retail_sales_index=self._safe_float(row.get("retail_sales")),
            )
            for _, row in merged.iterrows()
        ]

        # Calculate metrics
        metrics = self._calculate_metrics(merged)

        return EconomicTimeSeries(
            data_points=data_points,
            metrics=metrics,
            earliest_date=merged["date"].min().date() if len(merged) > 0 else None,
            latest_date=merged["date"].max().date() if len(merged) > 0 else None,
        )

    def transform_single(
        self,
        dataset_name: str,
        raw_data: pd.DataFrame,
    ) -> EconomicTimeSeries:
        """
        Transform a single ONS dataset.

        Convenience method for transforming individual datasets.

        Args:
            dataset_name: Name of dataset ("cpi", "employment", "retail_sales")
            raw_data: DataFrame from ONSClient.fetch()

        Returns:
            EconomicTimeSeries with single dataset
        """
        self._clear_warnings()

        fake_result = FetchResult.ok(raw_data)
        return self.transform({dataset_name: fake_result})

    def _safe_float(self, value) -> Optional[float]:
        """Convert value to float, returning None for NaN."""
        if pd.isna(value):
            return None
        return float(value)

    def _merge_datasets(
        self,
        datasets: dict[str, pd.DataFrame],
    ) -> pd.DataFrame:
        """Merge individual datasets on date."""
        merged = None

        for name, df in datasets.items():
            df = df.copy()
            df["date"] = pd.to_datetime(df["date"])
            df = df.rename(columns={"value": name})
            df = df[["date", name]]

            # Validate range
            min_val, max_val = self.VALIDATION_RANGES.get(
                name, (-float("inf"), float("inf"))
            )
            self._validate_range(df, name, min_val, max_val)

            if merged is None:
                merged = df
            else:
                merged = pd.merge(merged, df, on="date", how="outer")

        if merged is not None:
            merged = merged.sort_values("date").reset_index(drop=True)

        return merged if merged is not None else pd.DataFrame()

    def _calculate_metrics(
        self,
        df: pd.DataFrame,
    ) -> Optional[EconomicMetrics]:
        """Calculate hero card metrics."""
        if df.empty:
            return None

        df = df.sort_values("date")

        # Get latest non-null value for each metric
        latest_cpi = None
        latest_employment = None
        latest_retail = None

        if "cpi" in df.columns and not df["cpi"].dropna().empty:
            latest_cpi = df["cpi"].dropna().iloc[-1]

        if "employment" in df.columns and not df["employment"].dropna().empty:
            latest_employment = df["employment"].dropna().iloc[-1]

        if "retail_sales" in df.columns and not df["retail_sales"].dropna().empty:
            latest_retail = df["retail_sales"].dropna().iloc[-1]

        if latest_cpi is None:
            return None

        # Calculate YoY changes
        cpi_yoy = (
            self._calculate_yoy_point_change(df, "date", "cpi")
            if "cpi" in df.columns
            else 0
        )
        employment_yoy = (
            self._calculate_yoy_point_change(df, "date", "employment")
            if "employment" in df.columns
            else 0
        )
        retail_yoy = (
            self._calculate_yoy_change(df, "date", "retail_sales")
            if "retail_sales" in df.columns
            else 0
        )

        latest_date = df["date"].max().date()

        return EconomicMetrics(
            current_cpi=float(latest_cpi),
            cpi_change_yoy=cpi_yoy or 0,
            current_employment=float(latest_employment) if latest_employment else 0,
            employment_change_yoy=employment_yoy or 0,
            current_retail_index=float(latest_retail) if latest_retail else 0,
            retail_change_yoy=retail_yoy or 0,
            latest_month=latest_date,
        )
