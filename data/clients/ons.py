"""Client for Office for National Statistics API."""

from typing import Optional
from datetime import datetime
import io
import time

import pandas as pd

from data.clients.base import BaseAPIClient, FetchResult
from data.exceptions import RateLimitError


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
        dataset: str,
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
                raise RateLimitError("ONS", int(retry_after))

            if response.status_code != 200:
                return FetchResult.error(
                    f"HTTP {response.status_code}: {response.reason}"
                )

            df = self._parse_csv_response(response.text, dataset)

            self.logger.info(
                f"Fetched {len(df)} rows for {dataset} in {elapsed_ms:.0f}ms"
            )

            return FetchResult.ok(df, response_time_ms=elapsed_ms)

        except RateLimitError:
            raise
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
        dataset: str,
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
            first_field = line.split(",")[0].strip() if line else ""
            if first_field and len(first_field) >= 4 and first_field[:4].isdigit():
                data_start = i
                break

        # Parse from data start
        df = pd.read_csv(
            io.StringIO("\n".join(lines[data_start:])),
            header=None,
            names=["period", "value"],
        )

        # Parse period to date
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
