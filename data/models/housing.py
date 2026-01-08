"""Data models for HM Land Registry housing data."""

from dataclasses import dataclass, field
from datetime import date
from enum import Enum
from typing import Optional

import pandas as pd


class Region(Enum):
    """UK regions for housing data."""

    # Nations
    UNITED_KINGDOM = "united-kingdom"
    ENGLAND = "england"
    SCOTLAND = "scotland"
    WALES = "wales"
    NORTHERN_IRELAND = "northern-ireland"

    # English regions
    LONDON = "london"
    SOUTH_EAST = "south-east"
    SOUTH_WEST = "south-west"
    EAST_OF_ENGLAND = "east-anglia"
    EAST_MIDLANDS = "east-midlands"
    WEST_MIDLANDS = "west-midlands"
    YORKSHIRE_AND_HUMBER = "yorkshire-and-the-humber"
    NORTH_WEST = "north-west"
    NORTH_EAST = "north-east"

    @property
    def display_name(self) -> str:
        """Human-readable name for UI display."""
        names = {
            "united-kingdom": "United Kingdom",
            "england": "England",
            "scotland": "Scotland",
            "wales": "Wales",
            "northern-ireland": "Northern Ireland",
            "london": "London",
            "south-east": "South East",
            "south-west": "South West",
            "east-anglia": "East of England",
            "east-midlands": "East Midlands",
            "west-midlands": "West Midlands",
            "yorkshire-and-the-humber": "Yorkshire and The Humber",
            "north-west": "North West",
            "north-east": "North East",
        }
        return names.get(self.value, self.value.replace("-", " ").title())

    @classmethod
    def from_string(cls, value: str) -> "Region":
        """Create Region from string value."""
        for region in cls:
            if region.value == value:
                return region
        raise ValueError(f"Unknown region: {value}")

    @classmethod
    def nations(cls) -> list["Region"]:
        """Return list of nation-level regions."""
        return [
            cls.UNITED_KINGDOM,
            cls.ENGLAND,
            cls.SCOTLAND,
            cls.WALES,
            cls.NORTHERN_IRELAND,
        ]

    @classmethod
    def english_regions(cls) -> list["Region"]:
        """Return list of English regional regions."""
        return [
            cls.LONDON,
            cls.SOUTH_EAST,
            cls.SOUTH_WEST,
            cls.EAST_OF_ENGLAND,
            cls.EAST_MIDLANDS,
            cls.WEST_MIDLANDS,
            cls.YORKSHIRE_AND_HUMBER,
            cls.NORTH_WEST,
            cls.NORTH_EAST,
        ]


@dataclass(frozen=True)
class HousingDataPoint:
    """Single observation of housing data for a region and month."""

    ref_month: date  # First day of month
    region: Region
    average_price: float
    house_price_index: float
    monthly_change_pct: float
    annual_change_pct: float
    sales_volume: Optional[int] = None  # None for suppressed recent months

    # Price by property type
    price_detached: Optional[float] = None
    price_semi_detached: Optional[float] = None
    price_terraced: Optional[float] = None
    price_flat: Optional[float] = None


@dataclass
class HousingMetrics:
    """Calculated metrics for a region."""

    region: Region
    current_average_price: float
    current_index: float
    price_change_yoy: float  # Year-over-year percentage change
    price_change_mom: float  # Month-over-month percentage change
    latest_month: date


@dataclass
class HousingTimeSeries:
    """Housing time series for a single region."""

    region: Region
    data_points: list[HousingDataPoint] = field(default_factory=list)
    metrics: Optional[HousingMetrics] = None

    def __len__(self) -> int:
        """Return number of data points."""
        return len(self.data_points)

    def filter_by_range(self, start: date, end: date) -> "HousingTimeSeries":
        """Return new instance filtered to date range."""
        filtered = [
            dp for dp in self.data_points
            if start <= dp.ref_month <= end
        ]
        return HousingTimeSeries(
            region=self.region,
            data_points=filtered,
            metrics=self.metrics,
        )

    def to_dataframe(self) -> pd.DataFrame:
        """Convert to pandas DataFrame for charting."""
        if not self.data_points:
            return pd.DataFrame()

        return pd.DataFrame([
            {
                "date": dp.ref_month,
                "region": dp.region.value,
                "region_name": dp.region.display_name,
                "average_price": dp.average_price,
                "house_price_index": dp.house_price_index,
                "monthly_change_pct": dp.monthly_change_pct,
                "annual_change_pct": dp.annual_change_pct,
                "sales_volume": dp.sales_volume,
                "price_detached": dp.price_detached,
                "price_semi_detached": dp.price_semi_detached,
                "price_terraced": dp.price_terraced,
                "price_flat": dp.price_flat,
            }
            for dp in self.data_points
        ])

    @property
    def dates(self) -> list[date]:
        """Return list of reference months."""
        return [dp.ref_month for dp in self.data_points]

    @property
    def average_prices(self) -> list[float]:
        """Return list of average prices."""
        return [dp.average_price for dp in self.data_points]


@dataclass
class RegionalHousingData:
    """Housing data for all regions."""

    regions: dict[Region, HousingTimeSeries] = field(default_factory=dict)

    def __len__(self) -> int:
        """Return number of regions."""
        return len(self.regions)

    def get(self, region: Region) -> Optional[HousingTimeSeries]:
        """Get time series for a region."""
        return self.regions.get(region)

    def get_heat_map_data(self) -> list[dict]:
        """
        Prepare data for regional heat map.

        Returns list of dicts with:
        - region: Region enum
        - region_name: Display name
        - annual_change: YoY percentage change
        - average_price: Current average price
        """
        result = []
        for region, ts in self.regions.items():
            if ts.metrics:
                result.append({
                    "region": region,
                    "region_name": region.display_name,
                    "annual_change": ts.metrics.price_change_yoy,
                    "average_price": ts.metrics.current_average_price,
                })
        return result

    def to_dataframe(self) -> pd.DataFrame:
        """Combine all regions into single DataFrame."""
        dfs = [ts.to_dataframe() for ts in self.regions.values()]
        if not dfs:
            return pd.DataFrame()
        return pd.concat(dfs, ignore_index=True)
