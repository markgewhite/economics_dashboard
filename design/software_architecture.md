# UK Housing & Economic Dashboard - Software Architecture Design

## Document Information

| Field | Value |
|-------|-------|
| Version | 1.0 |
| Date | January 2026 |
| Status | Draft |
| Python Version | 3.13 |

---

## 1. System Architecture Overview

### 1.1 Architecture Style

The dashboard follows a **layered architecture** with clear boundaries between concerns:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           PRESENTATION LAYER                                 │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────────────┐│
│  │ Hero Metrics │ │ Main Charts  │ │  Heat Map    │ │ Deep Dive Panels     ││
│  └──────────────┘ └──────────────┘ └──────────────┘ └──────────────────────┘│
│  ┌──────────────┐ ┌──────────────┐                                          │
│  │   Filters    │ │   Header     │                                          │
│  └──────────────┘ └──────────────┘                                          │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           APPLICATION LAYER                                  │
│  ┌────────────────────┐ ┌─────────────────────┐ ┌─────────────────────────┐ │
│  │   State Manager    │ │  Filter Controller  │ │   Refresh Manager       │ │
│  └────────────────────┘ └─────────────────────┘ └─────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         DATA SERVICE LAYER                                   │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │                         DataService                                      ││
│  │  - Orchestrates data fetching, caching, transformation                  ││
│  │  - Implements graceful degradation                                       ││
│  │  - Provides unified interface for presentation layer                    ││
│  └─────────────────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                       DATA TRANSFORMATION LAYER                              │
│  ┌───────────────────┐ ┌───────────────────┐ ┌───────────────────┐         │
│  │ MonetaryTransform │ │ HousingTransform  │ │ EconomicTransform │         │
│  └───────────────────┘ └───────────────────┘ └───────────────────┘         │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                            CACHING LAYER                                     │
│  ┌──────────────────┐ ┌────────────────────┐ ┌────────────────────────────┐│
│  │  Cache Manager   │ │ Refresh Scheduler  │ │  Cache Metadata Store      ││
│  └──────────────────┘ └────────────────────┘ └────────────────────────────┘│
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                        DATA ACQUISITION LAYER                                │
│  ┌───────────────────┐ ┌───────────────────┐ ┌───────────────────┐         │
│  │  BoE Client       │ │ Land Registry     │ │   ONS Client      │         │
│  │                   │ │ Client            │ │                   │         │
│  └───────────────────┘ └───────────────────┘ └───────────────────┘         │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         EXTERNAL DATA SOURCES                                │
│       [ Bank of England ]    [ HM Land Registry ]    [ ONS API ]            │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 1.2 Key Design Principles

1. **Separation of Concerns**: Each layer has a single responsibility
2. **Dependency Inversion**: Higher layers depend on abstractions, not concrete implementations
3. **Graceful Degradation**: System continues operating with partial data when sources fail
4. **Schedule-Aware Caching**: Refresh decisions based on publication schedules, not arbitrary intervals
5. **Testability**: Each component can be tested in isolation with mocked dependencies

### 1.3 Data Flow

```
User Request
     │
     ▼
┌──────────────────┐
│   Streamlit UI   │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐     ┌──────────────────┐
│   DataService    │────▶│ RefreshScheduler │
└────────┬─────────┘     └────────┬─────────┘
         │                        │
         │   ┌────────────────────┘
         │   │  "Should refresh?"
         ▼   ▼
┌──────────────────┐
│  Cache Manager   │
└────────┬─────────┘
         │
         │ Cache miss or refresh needed
         ▼
┌──────────────────┐
│   API Clients    │────▶ External APIs
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  Transformers    │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ Cache (write)    │
└────────┬─────────┘
         │
         ▼
    Dashboard Data
```

---

## 2. Module Structure

### 2.1 Directory Layout

```
uk-economic-dashboard/
│
├── app/                              # Application layer
│   ├── __init__.py
│   ├── main.py                       # Streamlit entry point
│   ├── config.py                     # Configuration management
│   ├── state.py                      # Session state management
│   ├── design_tokens.py              # Figma design specifications
│   │
│   ├── components/                   # UI components
│   │   ├── __init__.py
│   │   ├── header.py                 # Dashboard header with refresh
│   │   ├── hero_metrics.py           # Four key metric cards
│   │   ├── filters.py                # Time range and region selectors
│   │   │
│   │   ├── charts/                   # Chart components
│   │   │   ├── __init__.py
│   │   │   ├── dual_axis.py          # Interest rates vs house prices
│   │   │   ├── heat_map.py           # Regional choropleth
│   │   │   ├── rate_trends.py        # Mortgage rate multi-line
│   │   │   ├── transactions.py       # Transaction volume bars
│   │   │   ├── sparklines.py         # Mini trend indicators
│   │   │   └── composition.py        # Donut chart
│   │   │
│   │   └── panels/                   # Deep dive panels
│   │       ├── __init__.py
│   │       ├── housing_composition.py
│   │       ├── economic_context.py
│   │       ├── regional_spotlight.py
│   │       └── footer.py
│   │
│   └── services/                     # Application services
│       ├── __init__.py
│       ├── data_service.py           # Data orchestration
│       └── refresh_service.py        # Refresh decision logic
│
├── data/                             # Data layer
│   ├── __init__.py
│   │
│   ├── clients/                      # API client modules
│   │   ├── __init__.py
│   │   ├── base.py                   # Abstract base client
│   │   ├── bank_of_england.py        # BoE IADB client
│   │   ├── land_registry.py          # HM Land Registry client
│   │   └── ons.py                    # ONS API client
│   │
│   ├── transformers/                 # Data transformation
│   │   ├── __init__.py
│   │   ├── base.py                   # Common utilities
│   │   ├── monetary.py               # BoE data transforms
│   │   ├── housing.py                # Housing data transforms
│   │   └── economic.py               # Economic data transforms
│   │
│   ├── cache/                        # Caching system
│   │   ├── __init__.py
│   │   ├── manager.py                # Cache read/write
│   │   ├── metadata.py               # Metadata handling
│   │   └── scheduler.py              # Schedule-aware refresh
│   │
│   ├── models/                       # Data models
│   │   ├── __init__.py
│   │   ├── monetary.py               # Monetary data models
│   │   ├── housing.py                # Housing data models
│   │   ├── economic.py               # Economic data models
│   │   └── cache.py                  # Cache metadata models
│   │
│   └── exceptions.py                 # Custom exceptions
│
├── storage/                          # Runtime cache (gitignored)
│   ├── raw/                          # Raw API responses
│   ├── processed/                    # Transformed data
│   └── metadata/                     # Cache metadata JSON
│
├── tests/                            # Test suite
│   ├── __init__.py
│   ├── conftest.py                   # Pytest fixtures
│   │
│   ├── unit/                         # Unit tests
│   │   ├── test_clients/
│   │   ├── test_transformers/
│   │   └── test_cache/
│   │
│   ├── integration/                  # Integration tests
│   │   ├── test_data_pipeline.py
│   │   └── test_api_availability.py
│   │
│   └── fixtures/                     # Test data
│       ├── sample_boe_response.csv
│       ├── sample_land_registry.csv
│       └── sample_ons_response.json
│
├── assets/                           # Static assets
│   └── styles.css                    # Custom Streamlit CSS
│
├── .env.example                      # Environment template
├── .gitignore
├── pyproject.toml                    # Project metadata
├── requirements.txt                  # Dependencies
├── CLAUDE.md                         # AI assistant guidance
└── README.md                         # Project documentation
```

### 2.2 Module Responsibilities

| Module | Responsibility |
|--------|----------------|
| `app/main.py` | Streamlit entry point, page orchestration, layout |
| `app/config.py` | Load and validate configuration from environment |
| `app/state.py` | Manage Streamlit session state |
| `app/services/data_service.py` | Coordinate data fetching, caching, transformation |
| `data/clients/*.py` | Fetch raw data from external APIs |
| `data/transformers/*.py` | Convert raw data to domain models |
| `data/cache/*.py` | Persist and retrieve cached data |
| `data/models/*.py` | Define data structures |

---

## 3. Data Models

All data models use Python dataclasses with type hints for clarity, immutability, and automatic method generation.

### 3.1 Monetary Data Models

```python
# data/models/monetary.py
from dataclasses import dataclass, field
from datetime import date
from typing import Optional


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
    """Calculated metrics for hero cards and charts."""

    current_bank_rate: float
    current_mortgage_2yr: float
    current_mortgage_5yr: float
    bank_rate_change_yoy: float  # Year-over-year percentage change
    mortgage_2yr_change_yoy: float
    mortgage_5yr_change_yoy: float
    latest_date: date


@dataclass
class MonetaryTimeSeries:
    """Complete monetary time series with metadata."""

    data_points: list[MonetaryDataPoint] = field(default_factory=list)
    metrics: Optional[MonetaryMetrics] = None
    earliest_date: Optional[date] = None
    latest_date: Optional[date] = None

    def filter_by_range(self, start: date, end: date) -> "MonetaryTimeSeries":
        """Return new instance filtered to date range."""
        filtered = [
            dp for dp in self.data_points
            if start <= dp.observation_date <= end
        ]
        return MonetaryTimeSeries(
            data_points=filtered,
            metrics=self.metrics,
            earliest_date=start,
            latest_date=end
        )

    def to_dataframe(self) -> "pd.DataFrame":
        """Convert to pandas DataFrame for charting."""
        import pandas as pd
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
```

### 3.2 Housing Data Models

```python
# data/models/housing.py
from dataclasses import dataclass, field
from datetime import date
from enum import Enum
from typing import Optional


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
    price_change_yoy: float
    price_change_mom: float
    latest_month: date


@dataclass
class HousingTimeSeries:
    """Housing time series for a single region."""

    region: Region
    data_points: list[HousingDataPoint] = field(default_factory=list)
    metrics: Optional[HousingMetrics] = None

    def filter_by_range(self, start: date, end: date) -> "HousingTimeSeries":
        """Return new instance filtered to date range."""
        filtered = [
            dp for dp in self.data_points
            if start <= dp.ref_month <= end
        ]
        return HousingTimeSeries(
            region=self.region,
            data_points=filtered,
            metrics=self.metrics
        )


@dataclass
class RegionalHousingData:
    """Housing data for all regions."""

    regions: dict[Region, HousingTimeSeries] = field(default_factory=dict)

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
```

### 3.3 Economic Data Models

```python
# data/models/economic.py
from dataclasses import dataclass, field
from datetime import date
from typing import Optional


@dataclass(frozen=True)
class EconomicDataPoint:
    """Single observation of economic indicators."""

    ref_month: date
    cpi_annual_rate: Optional[float] = None  # Percentage
    employment_rate: Optional[float] = None  # Percentage
    retail_sales_index: Optional[float] = None  # Index value


@dataclass
class EconomicMetrics:
    """Calculated metrics for hero cards."""

    current_cpi: float
    cpi_change_yoy: float
    current_employment: float
    employment_change_yoy: float
    current_retail_index: float
    retail_change_yoy: float
    latest_month: date


@dataclass
class EconomicTimeSeries:
    """Economic indicators time series."""

    data_points: list[EconomicDataPoint] = field(default_factory=list)
    metrics: Optional[EconomicMetrics] = None

    def filter_by_range(self, start: date, end: date) -> "EconomicTimeSeries":
        """Return new instance filtered to date range."""
        filtered = [
            dp for dp in self.data_points
            if start <= dp.ref_month <= end
        ]
        return EconomicTimeSeries(
            data_points=filtered,
            metrics=self.metrics
        )
```

### 3.4 Cache Metadata Models

```python
# data/models/cache.py
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum
from typing import Optional
import json


class RefreshReason(Enum):
    """Reason codes for cache refresh decisions."""

    INITIAL_FETCH = "initial_fetch"
    FORCED_REFRESH = "forced_refresh"
    DAILY_UPDATE_EXPECTED = "daily_update_expected"
    MONTHLY_UPDATE_EXPECTED = "monthly_update_expected"
    ALREADY_CURRENT = "already_current"
    CACHED_WEEKEND = "cached_weekend_no_update"
    CACHED_BEFORE_CHECK_TIME = "cached_before_check_time"
    CACHED_BEFORE_RELEASE_DAY = "cached_before_release_day"
    FETCH_FAILED_USING_STALE = "fetch_failed_using_stale"


@dataclass
class CacheMetadata:
    """Metadata for a cached dataset."""

    dataset: str  # "monetary", "housing", "economic"
    last_fetch: datetime
    next_expected: datetime
    data_date: str  # Latest data point date (ISO format)
    refresh_reason: RefreshReason
    record_count: int
    is_stale: bool = False  # True if fetch failed and using old cache

    def to_json(self) -> str:
        """Serialize to JSON string."""
        data = asdict(self)
        data["last_fetch"] = self.last_fetch.isoformat()
        data["next_expected"] = self.next_expected.isoformat()
        data["refresh_reason"] = self.refresh_reason.value
        return json.dumps(data, indent=2)

    @classmethod
    def from_json(cls, json_str: str) -> "CacheMetadata":
        """Deserialize from JSON string."""
        data = json.loads(json_str)
        data["last_fetch"] = datetime.fromisoformat(data["last_fetch"])
        data["next_expected"] = datetime.fromisoformat(data["next_expected"])
        data["refresh_reason"] = RefreshReason(data["refresh_reason"])
        return cls(**data)

    @property
    def age_description(self) -> str:
        """Human-readable description of data age."""
        age = datetime.now() - self.last_fetch
        if age.days > 0:
            return f"Updated {age.days} day{'s' if age.days != 1 else ''} ago"
        hours = age.seconds // 3600
        if hours > 0:
            return f"Updated {hours} hour{'s' if hours != 1 else ''} ago"
        minutes = age.seconds // 60
        return f"Updated {minutes} minute{'s' if minutes != 1 else ''} ago"
```

---

## 4. API Clients

### 4.1 Base Client

```python
# data/clients/base.py
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import TypeVar, Generic, Optional
import logging
import time

import requests
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)

T = TypeVar("T")


@dataclass
class FetchResult(Generic[T]):
    """Result of an API fetch operation."""

    success: bool
    data: Optional[T]
    error_message: Optional[str] = None
    response_time_ms: float = 0.0

    @classmethod
    def ok(cls, data: T, response_time_ms: float = 0.0) -> "FetchResult[T]":
        """Create successful result."""
        return cls(success=True, data=data, response_time_ms=response_time_ms)

    @classmethod
    def error(cls, message: str) -> "FetchResult[T]":
        """Create error result."""
        return cls(success=False, data=None, error_message=message)


class BaseAPIClient(ABC):
    """
    Abstract base class for all API clients.

    Provides:
    - Lazy-initialized requests session
    - Retry logic with exponential backoff
    - Response timing
    - Logging
    """

    def __init__(self, base_url: str, timeout: int = 30):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.logger = logging.getLogger(self.__class__.__name__)
        self._session: Optional[requests.Session] = None

    @property
    def session(self) -> requests.Session:
        """Lazy-initialized requests session."""
        if self._session is None:
            self._session = self._create_session()
        return self._session

    def _create_session(self) -> requests.Session:
        """
        Create configured session.

        Override in subclasses to add custom headers.
        """
        session = requests.Session()
        session.headers.update({
            "Accept": "text/csv,application/json",
        })
        return session

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=8),
        retry=retry_if_exception_type((requests.ConnectionError, requests.Timeout)),
    )
    def _make_request(
        self,
        url: str,
        method: str = "GET",
        **kwargs
    ) -> requests.Response:
        """
        Make HTTP request with retry logic.

        Retries on:
        - Connection errors
        - Timeouts

        Does not retry on:
        - 4xx/5xx HTTP errors (handled by caller)
        """
        self.logger.debug(f"Requesting: {url}")

        response = self.session.request(
            method=method,
            url=url,
            timeout=self.timeout,
            **kwargs
        )

        self.logger.debug(f"Response status: {response.status_code}")
        return response

    def _timed_request(self, url: str, **kwargs) -> tuple[requests.Response, float]:
        """Make request and return response with timing."""
        start = time.perf_counter()
        response = self._make_request(url, **kwargs)
        elapsed_ms = (time.perf_counter() - start) * 1000
        return response, elapsed_ms

    @abstractmethod
    def fetch(self, **params) -> FetchResult:
        """
        Fetch data from API.

        Override in subclasses with appropriate parameters.
        """
        pass

    def close(self):
        """Close the session."""
        if self._session:
            self._session.close()
            self._session = None
```

### 4.2 Bank of England Client

```python
# data/clients/bank_of_england.py
from datetime import date
from typing import Optional
import io

import pandas as pd

from data.clients.base import BaseAPIClient, FetchResult


class BankOfEnglandClient(BaseAPIClient):
    """
    Client for Bank of England IADB (Interactive Database) API.

    API Documentation: https://www.bankofengland.co.uk/boeapps/database/help.asp

    Important:
    - Requires User-Agent header (server returns 500 without it)
    - Missing values represented as ".." in CSV
    - Date format in responses: "DD Mon YYYY" (e.g., "01 Jan 2024")
    """

    # Series codes for required data
    SERIES_CODES = {
        "bank_rate": "IUDBEDR",
        "sonia": "IUDSOIA",
        "mortgage_2yr": "IUMBV34",
        "mortgage_5yr": "IUMBV42",
        "gbp_usd": "XUDLUSS",
        "gbp_eur": "XUDLERS",
    }

    def __init__(self):
        super().__init__(
            base_url="https://www.bankofengland.co.uk/boeapps/database"
        )

    def _create_session(self) -> "requests.Session":
        """Create session with required User-Agent header."""
        import requests
        session = requests.Session()
        session.headers.update({
            "User-Agent": "UK-Economic-Dashboard/1.0 (Portfolio Project)",
            "Accept": "text/csv",
        })
        return session

    def fetch(
        self,
        series: Optional[list[str]] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> FetchResult[pd.DataFrame]:
        """
        Fetch time series data from BoE IADB.

        Args:
            series: List of series keys (e.g., ["bank_rate", "sonia"]).
                   If None, fetches all available series.
            start_date: Start of date range. Defaults to 5 years ago.
            end_date: End of date range. Defaults to today.

        Returns:
            FetchResult containing DataFrame with columns:
            - date: datetime64
            - One column per series (bank_rate, sonia, etc.)
        """
        # Default date range: 5 years
        if end_date is None:
            end_date = date.today()
        if start_date is None:
            start_date = date(end_date.year - 5, end_date.month, end_date.day)

        # Default to all series
        if series is None:
            series = list(self.SERIES_CODES.keys())

        # Build URL
        url = self._build_url(series, start_date, end_date)

        try:
            response, elapsed_ms = self._timed_request(url)

            if response.status_code != 200:
                return FetchResult.error(
                    f"HTTP {response.status_code}: {response.reason}"
                )

            # Parse CSV response
            df = self._parse_response(response.text, series)

            self.logger.info(
                f"Fetched {len(df)} rows from BoE in {elapsed_ms:.0f}ms"
            )

            return FetchResult.ok(df, response_time_ms=elapsed_ms)

        except Exception as e:
            self.logger.error(f"Failed to fetch from BoE: {e}")
            return FetchResult.error(str(e))

    def _build_url(
        self,
        series: list[str],
        start_date: date,
        end_date: date
    ) -> str:
        """Construct API URL with required parameters."""
        # Convert series keys to codes
        codes = [self.SERIES_CODES[s] for s in series]

        # Format dates as required: DD/Mon/YYYY
        date_format = "%d/%b/%Y"

        params = {
            "Datefrom": start_date.strftime(date_format),
            "Dateto": end_date.strftime(date_format),
            "SeriesCodes": ",".join(codes),
            "CSVF": "TN",  # CSV with series names as headers
            "UsingCodes": "Y",
            "VPD": "Y",
            "VFD": "N",
        }

        query = "&".join(f"{k}={v}" for k, v in params.items())
        return f"{self.base_url}/_iadb-fromshowcolumns.asp?{query}"

    def _parse_response(
        self,
        content: str,
        series: list[str]
    ) -> pd.DataFrame:
        """
        Parse CSV response from BoE.

        Handles:
        - Date format: "DD Mon YYYY"
        - Missing values: ".."
        - Column renaming from codes to friendly names
        """
        # Read CSV
        df = pd.read_csv(
            io.StringIO(content),
            na_values=[".."],  # BoE uses ".." for missing
        )

        # Parse date column
        df["DATE"] = pd.to_datetime(df["DATE"], format="%d %b %Y")
        df = df.rename(columns={"DATE": "date"})

        # Rename series code columns to friendly names
        code_to_name = {v: k for k, v in self.SERIES_CODES.items()}
        df = df.rename(columns=code_to_name)

        # Sort by date
        df = df.sort_values("date").reset_index(drop=True)

        return df
```

### 4.3 Land Registry Client

```python
# data/clients/land_registry.py
from datetime import date
from typing import Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
import io

import pandas as pd

from data.clients.base import BaseAPIClient, FetchResult
from data.models.housing import Region


class LandRegistryClient(BaseAPIClient):
    """
    Client for HM Land Registry UK House Price Index API.

    API Documentation: http://landregistry.data.gov.uk/app/root/doc/ukhpi

    Notes:
    - Each region requires a separate request
    - Sales volume suppressed for most recent 2 months
    - Monthly publication on 20th working day
    """

    def __init__(self):
        super().__init__(
            base_url="http://landregistry.data.gov.uk/data/ukhpi"
        )

    def fetch(
        self,
        region: Region,
        start_month: Optional[str] = None,
        end_month: Optional[str] = None,
    ) -> FetchResult[pd.DataFrame]:
        """
        Fetch housing data for a single region.

        Args:
            region: Region enum value
            start_month: Start month in YYYY-MM format
            end_month: End month in YYYY-MM format

        Returns:
            FetchResult containing DataFrame with columns matching
            Land Registry schema (refMonth, averagePrice, etc.)
        """
        url = self._build_url(region, start_month, end_month)

        try:
            response, elapsed_ms = self._timed_request(url)

            if response.status_code != 200:
                return FetchResult.error(
                    f"HTTP {response.status_code} for {region.value}"
                )

            df = self._parse_response(response.text, region)

            self.logger.debug(
                f"Fetched {len(df)} rows for {region.value} in {elapsed_ms:.0f}ms"
            )

            return FetchResult.ok(df, response_time_ms=elapsed_ms)

        except Exception as e:
            self.logger.error(f"Failed to fetch {region.value}: {e}")
            return FetchResult.error(str(e))

    def fetch_all_regions(
        self,
        start_month: Optional[str] = None,
        end_month: Optional[str] = None,
        max_workers: int = 5,
    ) -> dict[Region, FetchResult[pd.DataFrame]]:
        """
        Fetch housing data for all regions in parallel.

        Args:
            start_month: Start month in YYYY-MM format
            end_month: End month in YYYY-MM format
            max_workers: Maximum concurrent requests

        Returns:
            Dict mapping Region to FetchResult
        """
        results: dict[Region, FetchResult[pd.DataFrame]] = {}

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all region fetches
            future_to_region = {
                executor.submit(
                    self.fetch, region, start_month, end_month
                ): region
                for region in Region
            }

            # Collect results
            for future in as_completed(future_to_region):
                region = future_to_region[future]
                try:
                    results[region] = future.result()
                except Exception as e:
                    results[region] = FetchResult.error(str(e))

        successful = sum(1 for r in results.values() if r.success)
        self.logger.info(
            f"Fetched {successful}/{len(Region)} regions successfully"
        )

        return results

    def _build_url(
        self,
        region: Region,
        start_month: Optional[str],
        end_month: Optional[str],
    ) -> str:
        """Construct API URL for region."""
        url = f"{self.base_url}/region/{region.value}.csv"

        params = []
        if start_month:
            params.append(f"min-refMonth={start_month}")
        if end_month:
            params.append(f"max-refMonth={end_month}")

        if params:
            url += "?" + "&".join(params)

        return url

    def _parse_response(
        self,
        content: str,
        region: Region
    ) -> pd.DataFrame:
        """Parse CSV response from Land Registry."""
        df = pd.read_csv(io.StringIO(content))

        # Select and rename relevant columns
        column_mapping = {
            "refMonth": "ref_month",
            "averagePrice": "average_price",
            "housePriceIndex": "house_price_index",
            "percentageChange": "monthly_change_pct",
            "percentageAnnualChange": "annual_change_pct",
            "salesVolume": "sales_volume",
            "averagePriceDetached": "price_detached",
            "averagePriceSemiDetached": "price_semi_detached",
            "averagePriceTerraced": "price_terraced",
            "averagePriceFlat": "price_flat",
        }

        # Keep only columns we need
        available = [c for c in column_mapping.keys() if c in df.columns]
        df = df[available].rename(columns=column_mapping)

        # Parse month to date (first of month)
        df["ref_month"] = pd.to_datetime(df["ref_month"] + "-01")

        # Add region
        df["region"] = region.value

        # Sort by date
        df = df.sort_values("ref_month").reset_index(drop=True)

        return df
```

### 4.4 ONS Client

```python
# data/clients/ons.py
from typing import Optional
from datetime import datetime
import io
import time

import pandas as pd

from data.clients.base import BaseAPIClient, FetchResult


class ONSClient(BaseAPIClient):
    """
    Client for Office for National Statistics API.

    Uses direct CSV downloads rather than the hierarchical API,
    as this is simpler and more stable.

    Rate Limits:
    - 120 requests per 10 seconds
    - 200 requests per minute

    API Documentation: https://developer.ons.gov.uk/
    """

    # Direct CSV download paths (more stable than API navigation)
    SERIES_PATHS = {
        "cpi": "/economy/inflationandpriceindices/timeseries/l55o/mm23",
        "employment": "/employmentandlabourmarket/peopleinwork/employmentandemployeetypes/timeseries/lf24/lms",
        "retail_sales": "/businessindustryandtrade/retailindustry/timeseries/j5ek/drsi",
    }

    # Rate limiting
    MAX_REQUESTS_PER_MINUTE = 100  # Conservative limit

    def __init__(self):
        super().__init__(base_url="https://www.ons.gov.uk")
        self._request_timestamps: list[float] = []

    def fetch(
        self,
        dataset: str
    ) -> FetchResult[pd.DataFrame]:
        """
        Fetch dataset using direct CSV download.

        Args:
            dataset: One of "cpi", "employment", "retail_sales"

        Returns:
            FetchResult containing DataFrame with columns:
            - date: datetime64 (monthly)
            - value: float
        """
        if dataset not in self.SERIES_PATHS:
            return FetchResult.error(
                f"Unknown dataset: {dataset}. "
                f"Available: {list(self.SERIES_PATHS.keys())}"
            )

        # Rate limiting
        self._enforce_rate_limit()

        url = f"{self.base_url}/generator?format=csv&uri={self.SERIES_PATHS[dataset]}"

        try:
            response, elapsed_ms = self._timed_request(url)

            if response.status_code == 429:
                # Rate limited - extract retry-after if available
                retry_after = response.headers.get("Retry-After", "60")
                return FetchResult.error(
                    f"Rate limited. Retry after {retry_after} seconds."
                )

            if response.status_code != 200:
                return FetchResult.error(
                    f"HTTP {response.status_code}: {response.reason}"
                )

            df = self._parse_csv_response(response.text, dataset)

            self.logger.info(
                f"Fetched {len(df)} rows for {dataset} in {elapsed_ms:.0f}ms"
            )

            return FetchResult.ok(df, response_time_ms=elapsed_ms)

        except Exception as e:
            self.logger.error(f"Failed to fetch {dataset}: {e}")
            return FetchResult.error(str(e))

    def fetch_all(self) -> dict[str, FetchResult[pd.DataFrame]]:
        """
        Fetch all economic datasets.

        Returns:
            Dict mapping dataset name to FetchResult
        """
        results = {}
        for dataset in self.SERIES_PATHS.keys():
            results[dataset] = self.fetch(dataset)
            # Small delay between requests to be respectful
            time.sleep(0.5)
        return results

    def _enforce_rate_limit(self):
        """Enforce client-side rate limiting."""
        now = time.time()

        # Remove timestamps older than 1 minute
        self._request_timestamps = [
            ts for ts in self._request_timestamps
            if now - ts < 60
        ]

        # If at limit, wait
        if len(self._request_timestamps) >= self.MAX_REQUESTS_PER_MINUTE:
            oldest = self._request_timestamps[0]
            wait_time = 60 - (now - oldest)
            if wait_time > 0:
                self.logger.debug(f"Rate limiting: waiting {wait_time:.1f}s")
                time.sleep(wait_time)

        # Record this request
        self._request_timestamps.append(time.time())

    def _parse_csv_response(
        self,
        content: str,
        dataset: str
    ) -> pd.DataFrame:
        """
        Parse ONS CSV response.

        ONS CSV format has header rows before the actual data.
        We need to skip these and find the data rows.
        """
        lines = content.strip().split("\n")

        # Find the header row (contains "Title" or column names)
        data_start = 0
        for i, line in enumerate(lines):
            # Look for rows that start with a date pattern (YYYY or YYYY MMM)
            if line and (line[:4].isdigit() or line.split(",")[0].strip()[:4].isdigit()):
                data_start = i
                break

        # Parse from data start
        df = pd.read_csv(
            io.StringIO("\n".join(lines[data_start:])),
            header=None,
            names=["period", "value"],
        )

        # Parse period to date
        # ONS uses formats like "2024 JAN" or "2024 Q1" or just "2024"
        df["date"] = df["period"].apply(self._parse_ons_period)

        # Drop rows where date couldn't be parsed (usually headers)
        df = df.dropna(subset=["date"])

        # Convert value to numeric
        df["value"] = pd.to_numeric(df["value"], errors="coerce")

        # Keep only date and value, add dataset name
        df = df[["date", "value"]].copy()
        df["dataset"] = dataset

        # Sort by date
        df = df.sort_values("date").reset_index(drop=True)

        return df

    def _parse_ons_period(self, period: str) -> Optional[datetime]:
        """
        Parse ONS period string to datetime.

        Handles formats:
        - "2024 JAN" -> 2024-01-01
        - "2024 Q1" -> 2024-01-01 (first month of quarter)
        - "2024" -> 2024-01-01
        """
        try:
            period = str(period).strip()

            # Try "YYYY MMM" format
            if " " in period:
                parts = period.split()
                year = int(parts[0])

                # Month abbreviation
                month_abbrs = {
                    "JAN": 1, "FEB": 2, "MAR": 3, "APR": 4,
                    "MAY": 5, "JUN": 6, "JUL": 7, "AUG": 8,
                    "SEP": 9, "OCT": 10, "NOV": 11, "DEC": 12,
                }

                month_str = parts[1].upper()
                if month_str in month_abbrs:
                    return datetime(year, month_abbrs[month_str], 1)

                # Quarter
                if month_str.startswith("Q"):
                    quarter = int(month_str[1])
                    month = (quarter - 1) * 3 + 1
                    return datetime(year, month, 1)

            # Try just year
            if period.isdigit() and len(period) == 4:
                return datetime(int(period), 1, 1)

            return None

        except (ValueError, IndexError):
            return None
```

---

## 5. Caching System

### 5.1 Refresh Scheduler

```python
# data/cache/scheduler.py
from dataclasses import dataclass
from datetime import datetime, date, time, timedelta
from typing import Optional
from zoneinfo import ZoneInfo

import holidays

from data.models.cache import RefreshReason


@dataclass
class RefreshSchedule:
    """Configuration for a dataset's refresh schedule."""

    frequency: str  # "daily" or "monthly"
    check_time: time  # Time after which to check for updates (UK time)
    publication_day: Optional[int] = None  # Day of month for monthly
    weekdays_only: bool = True


@dataclass
class RefreshDecision:
    """Result of refresh decision logic."""

    should_refresh: bool
    reason: RefreshReason
    next_expected: datetime


class RefreshScheduler:
    """
    Determines when data refresh is needed based on publication schedules.

    This implements schedule-aware caching rather than arbitrary time intervals,
    minimizing unnecessary API calls while ensuring data freshness.
    """

    # Dataset refresh schedules
    SCHEDULES = {
        "monetary": RefreshSchedule(
            frequency="daily",
            check_time=time(10, 0),  # After 10:00 UK time
            weekdays_only=True,
        ),
        "housing": RefreshSchedule(
            frequency="monthly",
            check_time=time(15, 0),  # After 15:00 UK time
            publication_day=20,  # 20th working day
            weekdays_only=True,
        ),
        "economic": RefreshSchedule(
            frequency="monthly",
            check_time=time(12, 0),  # After 12:00 UK time
            publication_day=15,  # Around 15th
            weekdays_only=True,
        ),
    }

    def __init__(self):
        self.uk_tz = ZoneInfo("Europe/London")
        self.uk_holidays = holidays.UK()

    def should_refresh(
        self,
        dataset: str,
        last_fetch: Optional[datetime],
    ) -> RefreshDecision:
        """
        Determine if dataset needs refresh based on schedule.

        Args:
            dataset: Dataset identifier ("monetary", "housing", "economic")
            last_fetch: Timestamp of last successful fetch (None if never fetched)

        Returns:
            RefreshDecision with should_refresh, reason, and next_expected
        """
        schedule = self.SCHEDULES.get(dataset)
        if not schedule:
            raise ValueError(f"Unknown dataset: {dataset}")

        now = datetime.now(self.uk_tz)

        # Never fetched - refresh needed
        if last_fetch is None:
            return RefreshDecision(
                should_refresh=True,
                reason=RefreshReason.INITIAL_FETCH,
                next_expected=self._calculate_next_expected(schedule, now),
            )

        # Ensure last_fetch is timezone-aware
        if last_fetch.tzinfo is None:
            last_fetch = last_fetch.replace(tzinfo=self.uk_tz)

        if schedule.frequency == "daily":
            return self._check_daily_refresh(schedule, last_fetch, now)
        else:
            return self._check_monthly_refresh(schedule, last_fetch, now)

    def _check_daily_refresh(
        self,
        schedule: RefreshSchedule,
        last_fetch: datetime,
        now: datetime,
    ) -> RefreshDecision:
        """Check if daily-updated dataset needs refresh."""
        today = now.date()
        last_fetch_date = last_fetch.date()

        # Already fetched today
        if last_fetch_date == today:
            return RefreshDecision(
                should_refresh=False,
                reason=RefreshReason.ALREADY_CURRENT,
                next_expected=self._calculate_next_expected(schedule, now),
            )

        # Weekend - no updates published
        if schedule.weekdays_only and today.weekday() >= 5:
            return RefreshDecision(
                should_refresh=False,
                reason=RefreshReason.CACHED_WEEKEND,
                next_expected=self._next_business_day(today, schedule.check_time),
            )

        # Before check time
        check_datetime = datetime.combine(today, schedule.check_time, tzinfo=self.uk_tz)
        if now < check_datetime:
            return RefreshDecision(
                should_refresh=False,
                reason=RefreshReason.CACHED_BEFORE_CHECK_TIME,
                next_expected=check_datetime,
            )

        # After check time on a weekday - refresh needed
        return RefreshDecision(
            should_refresh=True,
            reason=RefreshReason.DAILY_UPDATE_EXPECTED,
            next_expected=self._calculate_next_expected(schedule, now),
        )

    def _check_monthly_refresh(
        self,
        schedule: RefreshSchedule,
        last_fetch: datetime,
        now: datetime,
    ) -> RefreshDecision:
        """Check if monthly-updated dataset needs refresh."""
        today = now.date()
        last_fetch_date = last_fetch.date()

        # Same month - already have this month's data
        if (last_fetch_date.year == today.year and
            last_fetch_date.month == today.month):
            return RefreshDecision(
                should_refresh=False,
                reason=RefreshReason.ALREADY_CURRENT,
                next_expected=self._calculate_next_expected(schedule, now),
            )

        # Before publication day
        pub_day = schedule.publication_day or 15
        if today.day < pub_day:
            return RefreshDecision(
                should_refresh=False,
                reason=RefreshReason.CACHED_BEFORE_RELEASE_DAY,
                next_expected=self._publication_datetime(
                    today.year, today.month, pub_day, schedule.check_time
                ),
            )

        # On or after publication day - check time
        check_datetime = datetime.combine(
            date(today.year, today.month, pub_day),
            schedule.check_time,
            tzinfo=self.uk_tz,
        )

        if now < check_datetime:
            return RefreshDecision(
                should_refresh=False,
                reason=RefreshReason.CACHED_BEFORE_CHECK_TIME,
                next_expected=check_datetime,
            )

        # After publication day and check time - refresh needed
        return RefreshDecision(
            should_refresh=True,
            reason=RefreshReason.MONTHLY_UPDATE_EXPECTED,
            next_expected=self._calculate_next_expected(schedule, now),
        )

    def _calculate_next_expected(
        self,
        schedule: RefreshSchedule,
        from_datetime: datetime,
    ) -> datetime:
        """Calculate next expected update timestamp."""
        if schedule.frequency == "daily":
            # Next business day at check time
            next_day = from_datetime.date() + timedelta(days=1)
            return self._next_business_day(next_day, schedule.check_time)
        else:
            # Next month's publication day
            year = from_datetime.year
            month = from_datetime.month + 1
            if month > 12:
                month = 1
                year += 1

            pub_day = schedule.publication_day or 15
            return self._publication_datetime(year, month, pub_day, schedule.check_time)

    def _next_business_day(self, from_date: date, at_time: time) -> datetime:
        """Find next business day from given date."""
        check_date = from_date
        while check_date.weekday() >= 5 or check_date in self.uk_holidays:
            check_date += timedelta(days=1)
        return datetime.combine(check_date, at_time, tzinfo=self.uk_tz)

    def _publication_datetime(
        self,
        year: int,
        month: int,
        day: int,
        at_time: time,
    ) -> datetime:
        """Create publication datetime, adjusting for month length."""
        from calendar import monthrange
        max_day = monthrange(year, month)[1]
        actual_day = min(day, max_day)
        return datetime.combine(
            date(year, month, actual_day),
            at_time,
            tzinfo=self.uk_tz,
        )

    def _is_business_day(self, check_date: date) -> bool:
        """Check if date is a UK business day."""
        return check_date.weekday() < 5 and check_date not in self.uk_holidays
```

### 5.2 Cache Manager

```python
# data/cache/manager.py
from pathlib import Path
from datetime import datetime
from typing import Optional
import logging

import pandas as pd

from data.models.cache import CacheMetadata, RefreshReason
from data.cache.scheduler import RefreshScheduler


class CacheManager:
    """
    Manages file-based cache for dashboard data.

    Cache structure:
    - storage/processed/{dataset}.parquet - Transformed data
    - storage/metadata/{dataset}.json - Cache metadata
    """

    def __init__(self, cache_dir: Path):
        self.cache_dir = Path(cache_dir)
        self.processed_dir = self.cache_dir / "processed"
        self.metadata_dir = self.cache_dir / "metadata"
        self.logger = logging.getLogger(__name__)

        self._ensure_directories()

    def _ensure_directories(self):
        """Create cache directories if they don't exist."""
        self.processed_dir.mkdir(parents=True, exist_ok=True)
        self.metadata_dir.mkdir(parents=True, exist_ok=True)

    def get(
        self,
        dataset: str
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
        scheduler: RefreshScheduler,
    ) -> CacheMetadata:
        """
        Store data in cache with metadata.

        Args:
            dataset: Dataset identifier
            data: DataFrame to cache
            refresh_reason: Reason for this cache write
            scheduler: RefreshScheduler for calculating next expected

        Returns:
            Generated CacheMetadata
        """
        data_path = self.processed_dir / f"{dataset}.parquet"
        meta_path = self.metadata_dir / f"{dataset}.json"

        now = datetime.now()

        # Calculate next expected update
        decision = scheduler.should_refresh(dataset, now)

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

        # Write data
        data.to_parquet(data_path, index=False)

        # Write metadata
        meta_path.write_text(metadata.to_json())

        self.logger.info(
            f"Cached {dataset}: {len(data)} rows, "
            f"data through {data_date_str}"
        )

        return metadata

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
        for dataset in ["monetary", "housing", "economic"]:
            self.invalidate(dataset)

    def get_all_metadata(self) -> dict[str, Optional[CacheMetadata]]:
        """Get metadata for all datasets."""
        return {
            dataset: self.get_metadata(dataset)
            for dataset in ["monetary", "housing", "economic"]
        }
```

---

## 6. Data Transformers

### 6.1 Base Transformer

```python
# data/transformers/base.py
from abc import ABC, abstractmethod
from typing import TypeVar, Generic, Optional
import logging

import pandas as pd
import numpy as np

T = TypeVar("T")


class BaseTransformer(ABC, Generic[T]):
    """
    Base class for data transformers.

    Transformers convert raw API responses (DataFrames) into
    domain models suitable for the presentation layer.
    """

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self._warnings: list[str] = []

    @abstractmethod
    def transform(self, raw_data: pd.DataFrame) -> T:
        """
        Transform raw data into domain model.

        Override in subclasses.
        """
        pass

    @property
    def warnings(self) -> list[str]:
        """Data quality warnings from last transformation."""
        return self._warnings.copy()

    def _add_warning(self, message: str):
        """Add a data quality warning."""
        self._warnings.append(message)
        self.logger.warning(message)

    def _clear_warnings(self):
        """Clear warnings before new transformation."""
        self._warnings = []

    def _handle_missing_values(
        self,
        df: pd.DataFrame,
        columns: list[str],
        strategy: str = "forward_fill",
    ) -> pd.DataFrame:
        """
        Apply missing value handling strategy.

        Args:
            df: DataFrame to process
            columns: Columns to handle
            strategy: One of "forward_fill", "interpolate", "drop"

        Returns:
            DataFrame with missing values handled
        """
        df = df.copy()

        for col in columns:
            if col not in df.columns:
                continue

            missing_count = df[col].isna().sum()
            if missing_count > 0:
                self._add_warning(
                    f"Column {col}: {missing_count} missing values "
                    f"({missing_count/len(df)*100:.1f}%)"
                )

                if strategy == "forward_fill":
                    df[col] = df[col].ffill()
                elif strategy == "interpolate":
                    df[col] = df[col].interpolate(method="linear")
                elif strategy == "drop":
                    df = df.dropna(subset=[col])

        return df

    def _calculate_change(
        self,
        series: pd.Series,
        periods: int = 1,
    ) -> pd.Series:
        """Calculate percentage change over specified periods."""
        return series.pct_change(periods=periods) * 100

    def _calculate_yoy_change(
        self,
        df: pd.DataFrame,
        date_col: str,
        value_col: str,
    ) -> Optional[float]:
        """
        Calculate year-over-year change for latest value.

        Returns percentage change or None if insufficient data.
        """
        if len(df) < 2:
            return None

        df = df.sort_values(date_col)
        latest_date = df[date_col].max()
        latest_value = df[df[date_col] == latest_date][value_col].iloc[0]

        # Find value from ~1 year ago
        target_date = latest_date - pd.DateOffset(years=1)

        # Find closest date to 1 year ago
        past_df = df[df[date_col] <= target_date]
        if past_df.empty:
            return None

        past_value = past_df[value_col].iloc[-1]

        if past_value == 0 or pd.isna(past_value):
            return None

        return ((latest_value - past_value) / past_value) * 100

    def _validate_range(
        self,
        df: pd.DataFrame,
        column: str,
        min_val: float,
        max_val: float,
    ) -> pd.DataFrame:
        """Flag values outside expected range."""
        if column not in df.columns:
            return df

        outliers = df[(df[column] < min_val) | (df[column] > max_val)]
        if len(outliers) > 0:
            self._add_warning(
                f"Column {column}: {len(outliers)} values outside "
                f"expected range [{min_val}, {max_val}]"
            )

        return df
```

### 6.2 Monetary Transformer

```python
# data/transformers/monetary.py
from datetime import date
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

        # Create data points
        data_points = [
            MonetaryDataPoint(
                observation_date=row["date"].date(),
                bank_rate=row.get("bank_rate"),
                sonia=row.get("sonia"),
                mortgage_2yr=row.get("mortgage_2yr"),
                mortgage_5yr=row.get("mortgage_5yr"),
                gbp_usd=row.get("gbp_usd"),
                gbp_eur=row.get("gbp_eur"),
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
        current_bank_rate = latest.get("bank_rate")
        current_mortgage_2yr = latest.get("mortgage_2yr")
        current_mortgage_5yr = latest.get("mortgage_5yr")

        # YoY changes
        bank_rate_yoy = self._calculate_yoy_change(df, "date", "bank_rate")
        mortgage_2yr_yoy = self._calculate_yoy_change(df, "date", "mortgage_2yr")
        mortgage_5yr_yoy = self._calculate_yoy_change(df, "date", "mortgage_5yr")

        # Handle None values
        if any(v is None for v in [current_bank_rate, current_mortgage_2yr]):
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
```

### 6.3 Housing Transformer

```python
# data/transformers/housing.py
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
        raw_data: dict[Region, FetchResult[pd.DataFrame]]
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

    def _transform_region(
        self,
        region: Region,
        df: pd.DataFrame
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

        # Create data points
        data_points = []
        for _, row in df.iterrows():
            data_points.append(HousingDataPoint(
                ref_month=row["ref_month"].date(),
                region=region,
                average_price=row["average_price"],
                house_price_index=row["house_price_index"],
                monthly_change_pct=row.get("monthly_change_pct", 0),
                annual_change_pct=row.get("annual_change_pct", 0),
                sales_volume=row.get("sales_volume"),
                price_detached=row.get("price_detached"),
                price_semi_detached=row.get("price_semi_detached"),
                price_terraced=row.get("price_terraced"),
                price_flat=row.get("price_flat"),
            ))

        # Calculate metrics
        metrics = self._calculate_metrics(region, df)

        return HousingTimeSeries(
            region=region,
            data_points=data_points,
            metrics=metrics,
        )

    def _calculate_metrics(
        self,
        region: Region,
        df: pd.DataFrame
    ) -> Optional[HousingMetrics]:
        """Calculate metrics for a region."""
        if df.empty:
            return None

        df = df.sort_values("ref_month")
        latest = df.iloc[-1]

        return HousingMetrics(
            region=region,
            current_average_price=latest["average_price"],
            current_index=latest["house_price_index"],
            price_change_yoy=latest.get("annual_change_pct", 0),
            price_change_mom=latest.get("monthly_change_pct", 0),
            latest_month=latest["ref_month"].date(),
        )
```

### 6.4 Economic Transformer

```python
# data/transformers/economic.py
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
        raw_data: dict[str, FetchResult[pd.DataFrame]]
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
                cpi_annual_rate=row.get("cpi"),
                employment_rate=row.get("employment"),
                retail_sales_index=row.get("retail_sales"),
            )
            for _, row in merged.iterrows()
        ]

        # Calculate metrics
        metrics = self._calculate_metrics(merged)

        return EconomicTimeSeries(
            data_points=data_points,
            metrics=metrics,
        )

    def _merge_datasets(
        self,
        datasets: dict[str, pd.DataFrame]
    ) -> pd.DataFrame:
        """Merge individual datasets on date."""
        merged = None

        for name, df in datasets.items():
            df = df.copy()
            df["date"] = pd.to_datetime(df["date"])
            df = df.rename(columns={"value": name})
            df = df[["date", name]]

            # Validate range
            min_val, max_val = self.VALIDATION_RANGES.get(name, (-float("inf"), float("inf")))
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
        df: pd.DataFrame
    ) -> Optional[EconomicMetrics]:
        """Calculate hero card metrics."""
        if df.empty:
            return None

        df = df.sort_values("date")

        # Get latest non-null value for each metric
        latest_cpi = df["cpi"].dropna().iloc[-1] if "cpi" in df.columns and not df["cpi"].dropna().empty else None
        latest_employment = df["employment"].dropna().iloc[-1] if "employment" in df.columns and not df["employment"].dropna().empty else None
        latest_retail = df["retail_sales"].dropna().iloc[-1] if "retail_sales" in df.columns and not df["retail_sales"].dropna().empty else None

        if latest_cpi is None:
            return None

        # Calculate YoY changes
        cpi_yoy = self._calculate_yoy_change(df, "date", "cpi") if "cpi" in df.columns else 0
        employment_yoy = self._calculate_yoy_change(df, "date", "employment") if "employment" in df.columns else 0
        retail_yoy = self._calculate_yoy_change(df, "date", "retail_sales") if "retail_sales" in df.columns else 0

        latest_date = df["date"].max().date()

        return EconomicMetrics(
            current_cpi=latest_cpi,
            cpi_change_yoy=cpi_yoy or 0,
            current_employment=latest_employment or 0,
            employment_change_yoy=employment_yoy or 0,
            current_retail_index=latest_retail or 0,
            retail_change_yoy=retail_yoy or 0,
            latest_month=latest_date,
        )
```

---

## 7. Data Service Layer

```python
# app/services/data_service.py
from dataclasses import dataclass
from pathlib import Path
from typing import Optional
from concurrent.futures import ThreadPoolExecutor
import logging

import pandas as pd

from data.clients.bank_of_england import BankOfEnglandClient
from data.clients.land_registry import LandRegistryClient
from data.clients.ons import ONSClient
from data.transformers.monetary import MonetaryTransformer
from data.transformers.housing import HousingTransformer
from data.transformers.economic import EconomicTransformer
from data.cache.manager import CacheManager
from data.cache.scheduler import RefreshScheduler
from data.models.monetary import MonetaryTimeSeries
from data.models.housing import RegionalHousingData
from data.models.economic import EconomicTimeSeries
from data.models.cache import CacheMetadata, RefreshReason


@dataclass
class DashboardData:
    """Complete dataset for dashboard rendering."""

    monetary: Optional[MonetaryTimeSeries]
    housing: Optional[RegionalHousingData]
    economic: Optional[EconomicTimeSeries]
    metadata: dict[str, Optional[CacheMetadata]]
    errors: list[str]

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


class DataService:
    """
    High-level service orchestrating data fetching and caching.

    This is the main interface for the presentation layer.
    Implements graceful degradation - continues with partial data
    when some sources fail.
    """

    def __init__(self, cache_dir: Path):
        self.logger = logging.getLogger(__name__)

        # Initialize cache and scheduler
        self.cache = CacheManager(cache_dir)
        self.scheduler = RefreshScheduler()

        # Initialize clients
        self.boe_client = BankOfEnglandClient()
        self.lr_client = LandRegistryClient()
        self.ons_client = ONSClient()

        # Initialize transformers
        self.monetary_transformer = MonetaryTransformer()
        self.housing_transformer = HousingTransformer()
        self.economic_transformer = EconomicTransformer()

    def get_dashboard_data(
        self,
        force_refresh: bool = False
    ) -> DashboardData:
        """
        Get all data for dashboard, using cache when appropriate.

        Args:
            force_refresh: If True, bypass cache and fetch fresh data

        Returns:
            DashboardData with all datasets and metadata
        """
        errors = []
        metadata = {}

        # Fetch each dataset with error handling
        monetary, meta = self._get_monetary_data(force_refresh)
        metadata["monetary"] = meta
        if monetary is None:
            errors.append("Failed to load monetary data")

        housing, meta = self._get_housing_data(force_refresh)
        metadata["housing"] = meta
        if housing is None:
            errors.append("Failed to load housing data")

        economic, meta = self._get_economic_data(force_refresh)
        metadata["economic"] = meta
        if economic is None:
            errors.append("Failed to load economic data")

        return DashboardData(
            monetary=monetary,
            housing=housing,
            economic=economic,
            metadata=metadata,
            errors=errors,
        )

    def _get_monetary_data(
        self,
        force_refresh: bool
    ) -> tuple[Optional[MonetaryTimeSeries], Optional[CacheMetadata]]:
        """Fetch or retrieve monetary data."""
        return self._get_dataset(
            dataset="monetary",
            force_refresh=force_refresh,
            fetch_fn=lambda: self.boe_client.fetch(),
            transform_fn=lambda df: self.monetary_transformer.transform(df),
        )

    def _get_housing_data(
        self,
        force_refresh: bool
    ) -> tuple[Optional[RegionalHousingData], Optional[CacheMetadata]]:
        """Fetch or retrieve housing data."""
        return self._get_dataset(
            dataset="housing",
            force_refresh=force_refresh,
            fetch_fn=lambda: self._fetch_housing_raw(),
            transform_fn=lambda data: self.housing_transformer.transform(data),
            raw_is_dict=True,
        )

    def _fetch_housing_raw(self):
        """Wrapper to fetch all regions and return in expected format."""
        results = self.lr_client.fetch_all_regions()
        # Check if any succeeded
        if any(r.success for r in results.values()):
            from data.clients.base import FetchResult
            return FetchResult.ok(results)
        return FetchResult.error("All region fetches failed")

    def _get_economic_data(
        self,
        force_refresh: bool
    ) -> tuple[Optional[EconomicTimeSeries], Optional[CacheMetadata]]:
        """Fetch or retrieve economic data."""
        return self._get_dataset(
            dataset="economic",
            force_refresh=force_refresh,
            fetch_fn=lambda: self._fetch_economic_raw(),
            transform_fn=lambda data: self.economic_transformer.transform(data),
            raw_is_dict=True,
        )

    def _fetch_economic_raw(self):
        """Wrapper to fetch all ONS datasets."""
        results = self.ons_client.fetch_all()
        if any(r.success for r in results.values()):
            from data.clients.base import FetchResult
            return FetchResult.ok(results)
        return FetchResult.error("All ONS fetches failed")

    def _get_dataset(
        self,
        dataset: str,
        force_refresh: bool,
        fetch_fn,
        transform_fn,
        raw_is_dict: bool = False,
    ) -> tuple:
        """
        Generic dataset retrieval with caching logic.

        Implements:
        1. Check if refresh needed (or forced)
        2. Try fetch if needed
        3. Fall back to stale cache if fetch fails
        4. Transform and cache result
        """
        # Check cache
        cached_df, cached_meta = self.cache.get(dataset)

        # Determine if refresh needed
        should_refresh = force_refresh
        refresh_reason = RefreshReason.FORCED_REFRESH if force_refresh else None

        if not force_refresh and cached_meta:
            decision = self.scheduler.should_refresh(
                dataset,
                cached_meta.last_fetch
            )
            should_refresh = decision.should_refresh
            refresh_reason = decision.reason
        elif cached_meta is None:
            should_refresh = True
            refresh_reason = RefreshReason.INITIAL_FETCH

        # If cache is current, use it
        if not should_refresh and cached_df is not None:
            self.logger.info(f"Using cached {dataset} data")
            # Transform cached data
            if raw_is_dict:
                # For housing/economic, we cache the raw dict results
                # Need to reconstruct and transform
                # Actually, let's cache the transformed data instead
                pass
            # For simplicity, we'll cache transformed data as parquet
            # and reconstruct models
            return self._reconstruct_from_cache(dataset, cached_df, cached_meta)

        # Try to fetch fresh data
        self.logger.info(f"Fetching fresh {dataset} data")
        result = fetch_fn()

        if result.success and result.data is not None:
            # Transform
            transformed = transform_fn(result.data)

            # Cache (as DataFrame)
            if raw_is_dict:
                # For dict results, cache a merged DataFrame
                cache_df = self._to_cacheable_df(dataset, result.data)
            else:
                cache_df = result.data

            meta = self.cache.put(
                dataset,
                cache_df,
                refresh_reason or RefreshReason.INITIAL_FETCH,
                self.scheduler,
            )

            return transformed, meta

        # Fetch failed - fall back to stale cache
        if cached_df is not None and cached_meta is not None:
            self.logger.warning(
                f"Fetch failed for {dataset}, using stale cache"
            )
            cached_meta.is_stale = True
            return self._reconstruct_from_cache(dataset, cached_df, cached_meta)

        # No cache available
        self.logger.error(f"No data available for {dataset}")
        return None, None

    def _reconstruct_from_cache(self, dataset, df, meta):
        """Reconstruct domain model from cached DataFrame."""
        # This is a simplified approach - in production you might
        # cache the serialized model directly
        if dataset == "monetary":
            return self.monetary_transformer.transform(df), meta
        elif dataset == "housing":
            # Would need to reconstruct dict format
            # For now, return the cached transformed data
            return None, meta  # Placeholder
        elif dataset == "economic":
            return None, meta  # Placeholder
        return None, meta

    def _to_cacheable_df(self, dataset, data) -> pd.DataFrame:
        """Convert dict results to cacheable DataFrame."""
        # Implementation depends on data structure
        return pd.DataFrame()  # Placeholder

    def get_refresh_status(self) -> dict[str, dict]:
        """
        Get refresh status for all datasets.

        Returns:
            Dict with status info for each dataset
        """
        status = {}

        for dataset in ["monetary", "housing", "economic"]:
            meta = self.cache.get_metadata(dataset)

            if meta is None:
                status[dataset] = {
                    "status": "not_cached",
                    "message": "No data cached",
                }
            else:
                decision = self.scheduler.should_refresh(
                    dataset,
                    meta.last_fetch
                )
                status[dataset] = {
                    "status": "stale" if meta.is_stale else "current",
                    "last_fetch": meta.last_fetch.isoformat(),
                    "next_expected": meta.next_expected.isoformat(),
                    "data_date": meta.data_date,
                    "age": meta.age_description,
                    "needs_refresh": decision.should_refresh,
                    "refresh_reason": decision.reason.value,
                }

        return status

    def close(self):
        """Clean up resources."""
        self.boe_client.close()
        self.lr_client.close()
        self.ons_client.close()
```

---

## 8. Streamlit Application Structure

### 8.1 Main Entry Point

```python
# app/main.py
from pathlib import Path

import streamlit as st

from app.config import Config
from app.state import StateManager
from app.services.data_service import DataService
from app.components.header import render_header
from app.components.hero_metrics import render_hero_metrics
from app.components.filters import render_filters
from app.components.charts.dual_axis import render_rates_vs_prices
from app.components.charts.heat_map import render_regional_heat_map
from app.components.charts.rate_trends import render_rate_trends
from app.components.charts.transactions import render_transactions
from app.components.panels.housing_composition import render_housing_panel
from app.components.panels.economic_context import render_economic_panel
from app.components.panels.regional_spotlight import render_regional_panel
from app.components.panels.footer import render_footer


def main():
    """Main dashboard entry point."""

    # Page configuration
    st.set_page_config(
        page_title="UK Housing & Economic Dashboard",
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="collapsed",
    )

    # Load custom CSS
    _load_styles()

    # Initialize configuration and state
    config = Config.from_env()
    state = StateManager(st.session_state)

    # Initialize data service
    data_service = DataService(cache_dir=config.cache_dir)

    # Check for refresh trigger
    force_refresh = state.should_force_refresh()

    # Load data
    with st.spinner("Loading dashboard data..."):
        data = data_service.get_dashboard_data(force_refresh=force_refresh)

    # Clear refresh flag
    state.clear_refresh_flag()

    # Show errors if any
    if data.has_errors:
        for error in data.errors:
            st.warning(error)

    # Render dashboard sections
    render_header(data.metadata, on_refresh=state.trigger_refresh)

    if data.monetary:
        render_hero_metrics(data)

    # Filters
    time_range, region = render_filters(state)

    # Main content area
    left_col, right_col = st.columns([3, 2])

    with left_col:
        if data.monetary and data.housing:
            render_rates_vs_prices(data, time_range)

        if data.housing:
            render_regional_heat_map(data.housing)

    with right_col:
        if data.monetary:
            render_rate_trends(data.monetary, time_range)

        if data.housing:
            render_transactions(data.housing, region, time_range)

    # Deep dive panels
    st.markdown("---")
    panel_cols = st.columns(3)

    with panel_cols[0]:
        if data.housing:
            render_housing_panel(data.housing, region)

    with panel_cols[1]:
        if data.economic:
            render_economic_panel(data.economic)

    with panel_cols[2]:
        if data.housing:
            render_regional_panel(data.housing)

    # Footer
    render_footer()


def _load_styles():
    """Load custom CSS from assets."""
    css_path = Path(__file__).parent.parent / "assets" / "styles.css"
    if css_path.exists():
        st.markdown(
            f"<style>{css_path.read_text()}</style>",
            unsafe_allow_html=True,
        )


if __name__ == "__main__":
    main()
```

### 8.2 Configuration

```python
# app/config.py
from dataclasses import dataclass
from pathlib import Path
from datetime import time
import os

from dotenv import load_dotenv


@dataclass
class Config:
    """Application configuration loaded from environment."""

    # API base URLs
    boe_base_url: str
    land_registry_base_url: str
    ons_base_url: str

    # Cache settings
    cache_dir: Path

    # Refresh schedule overrides
    monetary_check_time: time
    housing_check_time: time
    economic_check_time: time

    # Application settings
    timezone: str
    log_level: str
    debug: bool

    @classmethod
    def from_env(cls) -> "Config":
        """Load configuration from environment variables."""
        load_dotenv()

        return cls(
            boe_base_url=os.getenv(
                "BOE_API_BASE_URL",
                "https://www.bankofengland.co.uk/boeapps/database",
            ),
            land_registry_base_url=os.getenv(
                "LAND_REGISTRY_API_BASE_URL",
                "http://landregistry.data.gov.uk",
            ),
            ons_base_url=os.getenv(
                "ONS_API_BASE_URL",
                "https://api.beta.ons.gov.uk/v1",
            ),
            cache_dir=Path(os.getenv("CACHE_DIR", "./storage")),
            monetary_check_time=cls._parse_time(
                os.getenv("MONETARY_CHECK_TIME", "10:00")
            ),
            housing_check_time=cls._parse_time(
                os.getenv("HOUSING_CHECK_TIME", "15:00")
            ),
            economic_check_time=cls._parse_time(
                os.getenv("ECONOMIC_CHECK_TIME", "12:00")
            ),
            timezone=os.getenv("TIMEZONE", "Europe/London"),
            log_level=os.getenv("LOG_LEVEL", "INFO"),
            debug=os.getenv("DEBUG", "false").lower() == "true",
        )

    @staticmethod
    def _parse_time(time_str: str) -> time:
        """Parse HH:MM string to time object."""
        hours, minutes = map(int, time_str.split(":"))
        return time(hours, minutes)
```

### 8.3 State Manager

```python
# app/state.py
from typing import Optional
from streamlit.runtime.state import SessionStateProxy


class StateManager:
    """
    Manages Streamlit session state for dashboard.

    Provides a clean interface over st.session_state with
    type hints and default values.
    """

    DEFAULT_TIME_RANGE = "1Y"
    DEFAULT_REGION = "united-kingdom"

    def __init__(self, session_state: SessionStateProxy):
        self._state = session_state
        self._initialize_defaults()

    def _initialize_defaults(self):
        """Set default values if not already in session state."""
        defaults = {
            "time_range": self.DEFAULT_TIME_RANGE,
            "region": self.DEFAULT_REGION,
            "force_refresh": False,
        }

        for key, value in defaults.items():
            if key not in self._state:
                self._state[key] = value

    @property
    def time_range(self) -> str:
        """Current time range selection."""
        return self._state.time_range

    @time_range.setter
    def time_range(self, value: str):
        self._state.time_range = value

    @property
    def region(self) -> str:
        """Current region selection."""
        return self._state.region

    @region.setter
    def region(self, value: str):
        self._state.region = value

    def trigger_refresh(self):
        """Flag that manual refresh was requested."""
        self._state.force_refresh = True

    def should_force_refresh(self) -> bool:
        """Check if manual refresh was requested."""
        return self._state.get("force_refresh", False)

    def clear_refresh_flag(self):
        """Clear the refresh flag after processing."""
        self._state.force_refresh = False
```

### 8.4 Design Tokens

```python
# app/design_tokens.py
"""
Design tokens extracted from Figma design.

These are placeholder values. Update after extracting actual values
from the Figma design file via MCP.
"""


class Colors:
    """Color palette from Figma."""

    # Primary palette
    PRIMARY = "#1E3A8A"
    SECONDARY = "#3B82F6"
    ACCENT = "#10B981"

    # Background colors
    BG_PRIMARY = "#FFFFFF"
    BG_SECONDARY = "#F8FAFC"
    BG_CARD = "#FFFFFF"

    # Text colors
    TEXT_PRIMARY = "#1E293B"
    TEXT_SECONDARY = "#64748B"
    TEXT_MUTED = "#94A3B8"

    # Status colors
    POSITIVE = "#10B981"
    NEGATIVE = "#EF4444"
    NEUTRAL = "#6B7280"

    # Chart colors
    CHART_1 = "#3B82F6"
    CHART_2 = "#10B981"
    CHART_3 = "#F59E0B"
    CHART_4 = "#8B5CF6"
    CHART_5 = "#EC4899"


class Typography:
    """Typography specifications from Figma."""

    FONT_FAMILY = "Inter, -apple-system, BlinkMacSystemFont, sans-serif"

    # Font sizes
    SIZE_H1 = "32px"
    SIZE_H2 = "24px"
    SIZE_H3 = "18px"
    SIZE_BODY = "14px"
    SIZE_CAPTION = "12px"
    SIZE_METRIC_VALUE = "36px"

    # Font weights
    WEIGHT_REGULAR = 400
    WEIGHT_MEDIUM = 500
    WEIGHT_SEMIBOLD = 600
    WEIGHT_BOLD = 700

    # Line heights
    LINE_HEIGHT_TIGHT = 1.2
    LINE_HEIGHT_NORMAL = 1.5
    LINE_HEIGHT_RELAXED = 1.75


class Spacing:
    """Spacing system from Figma."""

    # Base unit: 4px
    XS = "4px"
    SM = "8px"
    MD = "16px"
    LG = "24px"
    XL = "32px"
    XXL = "48px"

    # Component-specific
    CARD_PADDING = "24px"
    SECTION_GAP = "24px"
    GRID_GUTTER = "16px"


class Effects:
    """Visual effects from Figma."""

    SHADOW_SM = "0 1px 2px rgba(0, 0, 0, 0.05)"
    SHADOW_MD = "0 4px 6px rgba(0, 0, 0, 0.1)"
    SHADOW_LG = "0 10px 15px rgba(0, 0, 0, 0.1)"

    BORDER_RADIUS_SM = "4px"
    BORDER_RADIUS_MD = "8px"
    BORDER_RADIUS_LG = "12px"

    BORDER_COLOR = "#E2E8F0"
    BORDER_WIDTH = "1px"


class ChartConfig:
    """Plotly chart configuration derived from design tokens."""

    # Color sequences for multi-series charts
    COLOR_SEQUENCE = [
        Colors.CHART_1,
        Colors.CHART_2,
        Colors.CHART_3,
        Colors.CHART_4,
        Colors.CHART_5,
    ]

    # Heat map color scale (negative -> neutral -> positive)
    HEAT_MAP_SCALE = [
        [0.0, Colors.NEGATIVE],
        [0.5, "#FFFFFF"],
        [1.0, Colors.POSITIVE],
    ]

    # Layout defaults
    LAYOUT_DEFAULTS = {
        "font_family": Typography.FONT_FAMILY,
        "font_color": Colors.TEXT_PRIMARY,
        "paper_bgcolor": Colors.BG_CARD,
        "plot_bgcolor": Colors.BG_CARD,
        "margin": {"l": 60, "r": 20, "t": 40, "b": 40},
    }
```

---

## 9. Error Handling

### 9.1 Exception Hierarchy

```python
# data/exceptions.py
"""Custom exceptions for the dashboard application."""


class DashboardError(Exception):
    """Base exception for all dashboard errors."""
    pass


class DataFetchError(DashboardError):
    """Error fetching data from external API."""

    def __init__(
        self,
        source: str,
        message: str,
        original_error: Exception = None
    ):
        self.source = source
        self.original_error = original_error
        super().__init__(f"Failed to fetch from {source}: {message}")


class DataTransformError(DashboardError):
    """Error transforming raw data."""

    def __init__(self, transformer: str, message: str):
        self.transformer = transformer
        super().__init__(f"Transform error in {transformer}: {message}")


class CacheError(DashboardError):
    """Error with cache operations."""
    pass


class ConfigurationError(DashboardError):
    """Error with application configuration."""
    pass


class ValidationError(DashboardError):
    """Data validation failed."""

    def __init__(self, field: str, message: str):
        self.field = field
        super().__init__(f"Validation error for {field}: {message}")
```

### 9.2 Error Handling Patterns

The application implements graceful degradation:

1. **API Failures**: Fall back to stale cached data with warning
2. **Partial Data**: Continue with available data, hide broken components
3. **Transform Errors**: Log warning, return partial results
4. **Cache Errors**: Proceed without caching, fetch fresh data

---

## 10. Dependencies

### 10.1 Required Packages

```
# requirements.txt
# Core framework
streamlit

# Data processing
pandas
numpy

# Visualization
plotly

# HTTP client
requests
tenacity

# Configuration
python-dotenv

# Date/time handling
holidays

# Data storage
pyarrow  # For parquet support

# Type checking (development)
mypy

# Testing
pytest
pytest-cov
responses

# Code quality (development)
black
isort
flake8
```

### 10.2 Python Version

- **Required**: Python 3.13+
- **Recommended**: Python 3.13.11 (current stable)

---

## 11. Document Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | January 2026 | Architecture | Initial document |

---

## Appendix A: Quick Reference

### A.1 Key File Locations

| Purpose | Path |
|---------|------|
| Entry point | `app/main.py` |
| Configuration | `app/config.py` |
| Design tokens | `app/design_tokens.py` |
| Data service | `app/services/data_service.py` |
| API clients | `data/clients/` |
| Cache system | `data/cache/` |
| Data models | `data/models/` |

### A.2 Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `CACHE_DIR` | `./storage` | Cache directory path |
| `TIMEZONE` | `Europe/London` | Application timezone |
| `LOG_LEVEL` | `INFO` | Logging level |
| `DEBUG` | `false` | Enable debug mode |

### A.3 API Endpoints

| Source | Endpoint |
|--------|----------|
| Bank of England | `bankofengland.co.uk/boeapps/database/_iadb-fromshowcolumns.asp` |
| Land Registry | `landregistry.data.gov.uk/data/ukhpi/region/{region}.csv` |
| ONS | `ons.gov.uk/generator?format=csv&uri={path}` |
