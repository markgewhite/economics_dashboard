"""Data models for ONS economic indicators."""

from dataclasses import dataclass, field
from datetime import date
from typing import Optional

import pandas as pd


@dataclass(frozen=True)
class EconomicDataPoint:
    """Single observation of economic indicators for a month."""

    ref_month: date  # First day of month
    cpi_annual_rate: Optional[float] = None  # Percentage (e.g., 2.5 for 2.5%)
    employment_rate: Optional[float] = None  # Percentage (e.g., 75.5 for 75.5%)
    retail_sales_index: Optional[float] = None  # Index value


@dataclass
class EconomicMetrics:
    """Calculated metrics for hero cards and summaries."""

    current_cpi: float
    cpi_change_yoy: float  # Change in the rate itself
    current_employment: float
    employment_change_yoy: float  # Percentage point change
    current_retail_index: float
    retail_change_yoy: float  # Percentage change in index
    latest_month: date


@dataclass
class EconomicTimeSeries:
    """Economic indicators time series."""

    data_points: list[EconomicDataPoint] = field(default_factory=list)
    metrics: Optional[EconomicMetrics] = None
    earliest_date: Optional[date] = None
    latest_date: Optional[date] = None

    def __len__(self) -> int:
        """Return number of data points."""
        return len(self.data_points)

    def filter_by_range(self, start: date, end: date) -> "EconomicTimeSeries":
        """Return new instance filtered to date range."""
        filtered = [
            dp for dp in self.data_points
            if start <= dp.ref_month <= end
        ]
        return EconomicTimeSeries(
            data_points=filtered,
            metrics=self.metrics,
            earliest_date=start if filtered else None,
            latest_date=end if filtered else None,
        )

    def to_dataframe(self) -> pd.DataFrame:
        """Convert to pandas DataFrame for charting."""
        if not self.data_points:
            return pd.DataFrame()

        return pd.DataFrame([
            {
                "date": dp.ref_month,
                "cpi_annual_rate": dp.cpi_annual_rate,
                "employment_rate": dp.employment_rate,
                "retail_sales_index": dp.retail_sales_index,
            }
            for dp in self.data_points
        ])

    @property
    def dates(self) -> list[date]:
        """Return list of reference months."""
        return [dp.ref_month for dp in self.data_points]

    @property
    def cpi_values(self) -> list[Optional[float]]:
        """Return list of CPI annual rate values."""
        return [dp.cpi_annual_rate for dp in self.data_points]

    @property
    def employment_values(self) -> list[Optional[float]]:
        """Return list of employment rate values."""
        return [dp.employment_rate for dp in self.data_points]

    @property
    def retail_values(self) -> list[Optional[float]]:
        """Return list of retail sales index values."""
        return [dp.retail_sales_index for dp in self.data_points]
