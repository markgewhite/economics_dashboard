"""Client for Bank of England IADB (Interactive Database) API."""

from datetime import date
from typing import Optional
import io

import pandas as pd
import requests

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

    def _create_session(self) -> requests.Session:
        """Create session with required User-Agent header."""
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

        # Validate series keys
        invalid_series = [s for s in series if s not in self.SERIES_CODES]
        if invalid_series:
            return FetchResult.error(
                f"Unknown series: {invalid_series}. "
                f"Available: {list(self.SERIES_CODES.keys())}"
            )

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
        end_date: date,
    ) -> str:
        """Construct API URL with required parameters."""
        # Convert series keys to codes
        codes = [self.SERIES_CODES[s] for s in series]

        # Format dates as required: DD/Mon/YYYY
        date_format = "%d/%b/%Y"

        params = {
            "csv.x": "yes",  # Required to get CSV response
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
        series: list[str],
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
