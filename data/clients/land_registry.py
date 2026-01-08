"""Client for HM Land Registry UK House Price Index API."""

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
            Land Registry schema (ref_month, average_price, etc.)
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
        region: Region,
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
