"""Transformer for Bank of England monetary data."""

from typing import Optional

import pandas as pd

from data.transformers.base import BaseTransformer
from data.models.monetary import (
    MonetaryDataPoint,
    MonetaryMetrics,
    MonetaryTimeSeries,
)


class MonetaryTransformer(BaseTransformer[MonetaryTimeSeries]):
    """
    Transform Bank of England data into monetary time series.

    Handles:
    - Date parsing
    - Missing value handling (forward fill)
    - Monthly aggregation for consistency
    - Metric calculations
    """

    # Expected value ranges for validation
    VALIDATION_RANGES = {
        "bank_rate": (0, 20),
        "sonia": (0, 20),
        "mortgage_2yr": (0, 25),
        "mortgage_5yr": (0, 25),
        "gbp_usd": (0.8, 2.0),
        "gbp_eur": (0.8, 1.8),
    }

    def transform(self, raw_data: pd.DataFrame) -> MonetaryTimeSeries:
        """
        Transform raw BoE data to MonetaryTimeSeries.

        Args:
            raw_data: DataFrame from BankOfEnglandClient.fetch()

        Returns:
            MonetaryTimeSeries with data points and metrics
        """
        self._clear_warnings()

        if raw_data.empty:
            return MonetaryTimeSeries()

        df = raw_data.copy()

        # Ensure date column is datetime
        df["date"] = pd.to_datetime(df["date"])

        # Validate ranges
        for col, (min_val, max_val) in self.VALIDATION_RANGES.items():
            if col in df.columns:
                self._validate_range(df, col, min_val, max_val)

        # Handle missing values
        value_columns = [c for c in df.columns if c != "date"]
        df = self._handle_missing_values(df, value_columns, strategy="forward_fill")

        # Convert to monthly if daily data
        if len(df) > 0:
            date_diff = df["date"].diff().median()
            if date_diff and date_diff.days < 7:  # Daily data
                df = self._to_monthly(df)

        # Sort by date
        df = df.sort_values("date").reset_index(drop=True)

        # Create data points
        data_points = [
            MonetaryDataPoint(
                observation_date=row["date"].date(),
                bank_rate=self._safe_float(row.get("bank_rate")),
                sonia=self._safe_float(row.get("sonia")),
                mortgage_2yr=self._safe_float(row.get("mortgage_2yr")),
                mortgage_5yr=self._safe_float(row.get("mortgage_5yr")),
                gbp_usd=self._safe_float(row.get("gbp_usd")),
                gbp_eur=self._safe_float(row.get("gbp_eur")),
            )
            for _, row in df.iterrows()
        ]

        # Calculate metrics
        metrics = self._calculate_metrics(df)

        return MonetaryTimeSeries(
            data_points=data_points,
            metrics=metrics,
            earliest_date=df["date"].min().date() if len(df) > 0 else None,
            latest_date=df["date"].max().date() if len(df) > 0 else None,
        )

    def _safe_float(self, value) -> Optional[float]:
        """Convert value to float, returning None for NaN."""
        if pd.isna(value):
            return None
        return float(value)

    def _to_monthly(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Aggregate daily data to monthly frequency.

        - bank_rate: Last value of month
        - sonia: Monthly average
        - Exchange rates: Monthly average
        - Mortgage rates: Already monthly, take last available
        """
        df = df.set_index("date")

        aggregations = {}

        # Bank rate: last value of month
        if "bank_rate" in df.columns:
            aggregations["bank_rate"] = "last"

        # SONIA and exchange rates: average
        for col in ["sonia", "gbp_usd", "gbp_eur"]:
            if col in df.columns:
                aggregations[col] = "mean"

        # Mortgage rates: last (they're already monthly)
        for col in ["mortgage_2yr", "mortgage_5yr"]:
            if col in df.columns:
                aggregations[col] = "last"

        if not aggregations:
            return df.reset_index()

        monthly = df.resample("ME").agg(aggregations)
        monthly = monthly.reset_index()

        return monthly

    def _calculate_metrics(self, df: pd.DataFrame) -> Optional[MonetaryMetrics]:
        """Calculate hero card metrics."""
        if df.empty:
            return None

        df = df.sort_values("date")
        latest = df.iloc[-1]
        latest_date = latest["date"].date()

        # Current values
        current_bank_rate = self._safe_float(latest.get("bank_rate"))
        current_mortgage_2yr = self._safe_float(latest.get("mortgage_2yr"))
        current_mortgage_5yr = self._safe_float(latest.get("mortgage_5yr"))

        # YoY changes (point change, not percentage, since these are rates)
        bank_rate_yoy = self._calculate_yoy_point_change(df, "date", "bank_rate")
        mortgage_2yr_yoy = self._calculate_yoy_point_change(df, "date", "mortgage_2yr")
        mortgage_5yr_yoy = self._calculate_yoy_point_change(df, "date", "mortgage_5yr")

        # Handle None values
        if current_bank_rate is None or current_mortgage_2yr is None:
            return None

        return MonetaryMetrics(
            current_bank_rate=current_bank_rate,
            current_mortgage_2yr=current_mortgage_2yr,
            current_mortgage_5yr=current_mortgage_5yr or 0,
            bank_rate_change_yoy=bank_rate_yoy or 0,
            mortgage_2yr_change_yoy=mortgage_2yr_yoy or 0,
            mortgage_5yr_change_yoy=mortgage_5yr_yoy or 0,
            latest_date=latest_date,
        )
