"""Unit tests for Land Registry API client."""

from unittest.mock import Mock, patch

import pandas as pd
import pytest

from data.clients.land_registry import LandRegistryClient
from data.models.housing import Region


class TestLandRegistryClient:
    """Tests for LandRegistryClient."""

    def test_base_url_is_correct(self):
        """Verify base URL is set correctly."""
        client = LandRegistryClient()
        assert "landregistry.data.gov.uk" in client.base_url

    def test_build_url_for_region(self):
        """Verify URL is constructed correctly for a region."""
        client = LandRegistryClient()
        url = client._build_url(
            region=Region.ENGLAND,
            start_month=None,
            end_month=None,
        )
        assert "/region/england.csv" in url

    def test_build_url_with_date_range(self):
        """Verify URL includes date range parameters."""
        client = LandRegistryClient()
        url = client._build_url(
            region=Region.LONDON,
            start_month="2020-01",
            end_month="2024-12",
        )
        assert "min-refMonth=2020-01" in url
        assert "max-refMonth=2024-12" in url

    def test_parse_response_renames_columns(self, sample_land_registry_response):
        """Verify column names are converted to snake_case."""
        client = LandRegistryClient()
        df = client._parse_response(sample_land_registry_response, Region.ENGLAND)

        expected_columns = [
            "ref_month",
            "average_price",
            "house_price_index",
            "monthly_change_pct",
            "annual_change_pct",
            "sales_volume",
            "price_detached",
            "price_semi_detached",
            "price_terraced",
            "price_flat",
            "region",
        ]
        for col in expected_columns:
            assert col in df.columns

    def test_parse_response_adds_region_column(self, sample_land_registry_response):
        """Verify region column is added to DataFrame."""
        client = LandRegistryClient()
        df = client._parse_response(sample_land_registry_response, Region.ENGLAND)

        assert "region" in df.columns
        assert df["region"].iloc[0] == "england"

    def test_parse_response_parses_dates(self, sample_land_registry_response):
        """Verify ref_month is parsed as datetime."""
        client = LandRegistryClient()
        df = client._parse_response(sample_land_registry_response, Region.ENGLAND)

        assert df["ref_month"].dtype == "datetime64[ns]"
        # Should be first of month
        assert df["ref_month"].iloc[0].day == 1

    def test_parse_response_sorts_by_date(self, sample_land_registry_response):
        """Verify results are sorted by date ascending."""
        client = LandRegistryClient()
        df = client._parse_response(sample_land_registry_response, Region.ENGLAND)

        dates = df["ref_month"].tolist()
        assert dates == sorted(dates)

    def test_parse_response_handles_missing_sales_volume(
        self, sample_land_registry_response
    ):
        """Verify missing sales volume (suppressed months) is handled."""
        client = LandRegistryClient()
        df = client._parse_response(sample_land_registry_response, Region.ENGLAND)

        # Recent months should have NaN for sales_volume
        # In our sample, 2024-06 and 2024-05 have empty sales_volume
        june_row = df[df["ref_month"] == pd.Timestamp("2024-06-01")]
        assert pd.isna(june_row["sales_volume"].values[0])

    @patch.object(LandRegistryClient, "_timed_request")
    def test_fetch_returns_success_on_200(
        self, mock_request, sample_land_registry_response
    ):
        """Verify successful fetch returns data."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = sample_land_registry_response
        mock_request.return_value = (mock_response, 200.0)

        client = LandRegistryClient()
        result = client.fetch(region=Region.ENGLAND)

        assert result.success is True
        assert result.data is not None
        assert isinstance(result.data, pd.DataFrame)

    @patch.object(LandRegistryClient, "_timed_request")
    def test_fetch_returns_error_on_non_200(self, mock_request):
        """Verify error handling for non-200 responses."""
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.reason = "Not Found"
        mock_request.return_value = (mock_response, 100.0)

        client = LandRegistryClient()
        result = client.fetch(region=Region.ENGLAND)

        assert result.success is False
        assert "404" in result.error_message

    @patch.object(LandRegistryClient, "fetch")
    def test_fetch_all_regions_calls_fetch_for_each_region(self, mock_fetch):
        """Verify fetch_all_regions fetches all Region enum values."""
        mock_fetch.return_value = Mock(success=True, data=pd.DataFrame())

        client = LandRegistryClient()
        results = client.fetch_all_regions()

        # Should have result for each region
        assert len(results) == len(Region)
        for region in Region:
            assert region in results

    @patch.object(LandRegistryClient, "fetch")
    def test_fetch_all_regions_handles_partial_failures(self, mock_fetch):
        """Verify fetch_all_regions handles some regions failing."""
        def mock_fetch_impl(region, start_month=None, end_month=None):
            if region == Region.LONDON:
                return Mock(success=False, error_message="Failed")
            return Mock(success=True, data=pd.DataFrame())

        mock_fetch.side_effect = mock_fetch_impl

        client = LandRegistryClient()
        results = client.fetch_all_regions()

        assert results[Region.LONDON].success is False
        assert results[Region.ENGLAND].success is True

    def test_all_regions_have_valid_slugs(self):
        """Verify all Region enum values produce valid URL slugs."""
        client = LandRegistryClient()
        for region in Region:
            url = client._build_url(region, None, None)
            # URL should be well-formed
            assert f"/region/{region.value}.csv" in url
            # Slug should be lowercase with hyphens
            assert region.value.islower() or "-" in region.value
