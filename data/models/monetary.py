"""Data models for Bank of England monetary data."""

from dataclasses import dataclass, field
from datetime import date
from typing import Optional

import pandas as pd


@dataclass(frozen=True)
class MonetaryDataPoint:
    """Single observation of monetary data for a specific date."""

    observation_date: date
    bank_rate: Optional[float] = None
    sonia: Optional[float] = None
    mortgage_2yr: Optional[float] = None
    mortgage_5yr: Optional[float] = None
    gbp_usd: Optional[float] = None
    gbp_eur: Optional[float] = None


@dataclass
class MonetaryMetrics:
    """Calculated metrics for hero cards and summaries."""

    current_bank_rate: float
    current_mortgage_2yr: float
    current_mortgage_5yr: float
    bank_rate_change_yoy: float  # Year-over-year percentage point change
    mortgage_2yr_change_yoy: float
    mortgage_5yr_change_yoy: float
    latest_date: date


@dataclass
class MonetaryTimeSeries:
    """Complete monetary time series with calculated metrics."""

    data_points: list[MonetaryDataPoint] = field(default_factory=list)
    metrics: Optional[MonetaryMetrics] = None
    earliest_date: Optional[date] = None
    latest_date: Optional[date] = None

    def __len__(self) -> int:
        """Return number of data points."""
        return len(self.data_points)

    def filter_by_range(self, start: date, end: date) -> "MonetaryTimeSeries":
        """Return new instance filtered to date range."""
        filtered = [
            dp for dp in self.data_points
            if start <= dp.observation_date <= end
        ]
        return MonetaryTimeSeries(
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
                "date": dp.observation_date,
                "bank_rate": dp.bank_rate,
                "sonia": dp.sonia,
                "mortgage_2yr": dp.mortgage_2yr,
                "mortgage_5yr": dp.mortgage_5yr,
                "gbp_usd": dp.gbp_usd,
                "gbp_eur": dp.gbp_eur,
            }
            for dp in self.data_points
        ])

    @property
    def dates(self) -> list[date]:
        """Return list of observation dates."""
        return [dp.observation_date for dp in self.data_points]

    @property
    def bank_rates(self) -> list[Optional[float]]:
        """Return list of bank rate values."""
        return [dp.bank_rate for dp in self.data_points]

    @property
    def mortgage_2yr_rates(self) -> list[Optional[float]]:
        """Return list of 2-year mortgage rate values."""
        return [dp.mortgage_2yr for dp in self.data_points]
