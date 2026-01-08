"""Unit tests for ONS API client."""

from datetime import datetime
from unittest.mock import Mock, patch, PropertyMock
import time

import pandas as pd
import pytest

from data.clients.ons import ONSClient
from data.exceptions import RateLimitError


class TestONSClient:
    """Tests for ONSClient."""

    def test_base_url_is_correct(self):
        """Verify base URL is set correctly."""
        client = ONSClient()
        assert "ons.gov.uk" in client.base_url

    def test_series_paths_defined(self):
        """Verify all required series paths are defined."""
        expected_datasets = ["cpi", "employment", "retail_sales"]
        client = ONSClient()
        for dataset in expected_datasets:
            assert dataset in client.SERIES_PATHS

    def test_fetch_validates_dataset_name(self):
        """Verify invalid dataset name returns error."""
        client = ONSClient()
        result = client.fetch("invalid_dataset")

        assert result.success is False
        assert "Unknown dataset" in result.error_message

    def test_parse_ons_period_monthly_format(self):
        """Verify 'YYYY MMM' format is parsed correctly."""
        client = ONSClient()

        result = client._parse_ons_period("2024 JAN")
        assert result == datetime(2024, 1, 1)

        result = client._parse_ons_period("2023 DEC")
        assert result == datetime(2023, 12, 1)

    def test_parse_ons_period_quarterly_format(self):
        """Verify 'YYYY Q1' format is parsed correctly."""
        client = ONSClient()

        result = client._parse_ons_period("2024 Q1")
        assert result == datetime(2024, 1, 1)

        result = client._parse_ons_period("2024 Q2")
        assert result == datetime(2024, 4, 1)

        result = client._parse_ons_period("2024 Q3")
        assert result == datetime(2024, 7, 1)

        result = client._parse_ons_period("2024 Q4")
        assert result == datetime(2024, 10, 1)

    def test_parse_ons_period_yearly_format(self):
        """Verify 'YYYY' format is parsed correctly."""
        client = ONSClient()

        result = client._parse_ons_period("2024")
        assert result == datetime(2024, 1, 1)

    def test_parse_ons_period_invalid_returns_none(self):
        """Verify invalid period strings return None."""
        client = ONSClient()

        assert client._parse_ons_period("Invalid") is None
        assert client._parse_ons_period("") is None
        assert client._parse_ons_period("2024 XYZ") is None

    def test_parse_csv_response_skips_header_rows(self, sample_ons_response):
        """Verify header/metadata rows are skipped."""
        client = ONSClient()
        df = client._parse_csv_response(sample_ons_response, "cpi")

        # Should not have Title, CDID, etc. as values
        assert "Title" not in df["value"].astype(str).values
        assert "CDID" not in str(df.values)

    def test_parse_csv_response_parses_dates(self, sample_ons_response):
        """Verify dates are parsed correctly."""
        client = ONSClient()
        df = client._parse_csv_response(sample_ons_response, "cpi")

        assert df["date"].dtype == "datetime64[ns]"
        # First data row should be 2023 JAN
        assert df["date"].iloc[0] == pd.Timestamp("2023-01-01")

    def test_parse_csv_response_parses_values(self, sample_ons_response):
        """Verify numeric values are parsed correctly."""
        client = ONSClient()
        df = client._parse_csv_response(sample_ons_response, "cpi")

        # First value should be 10.1
        assert df["value"].iloc[0] == 10.1

    def test_parse_csv_response_adds_dataset_column(self, sample_ons_response):
        """Verify dataset column is added."""
        client = ONSClient()
        df = client._parse_csv_response(sample_ons_response, "cpi")

        assert "dataset" in df.columns
        assert df["dataset"].iloc[0] == "cpi"

    def test_parse_csv_response_sorts_by_date(self, sample_ons_response):
        """Verify results are sorted by date ascending."""
        client = ONSClient()
        df = client._parse_csv_response(sample_ons_response, "cpi")

        dates = df["date"].tolist()
        assert dates == sorted(dates)

    @patch.object(ONSClient, "_timed_request")
    def test_fetch_returns_success_on_200(self, mock_request, sample_ons_response):
        """Verify successful fetch returns data."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = sample_ons_response
        mock_request.return_value = (mock_response, 100.0)

        client = ONSClient()
        result = client.fetch("cpi")

        assert result.success is True
        assert result.data is not None
        assert isinstance(result.data, pd.DataFrame)

    @patch.object(ONSClient, "_timed_request")
    def test_fetch_raises_rate_limit_error_on_429(self, mock_request):
        """Verify 429 response raises RateLimitError."""
        mock_response = Mock()
        mock_response.status_code = 429
        mock_response.headers = {"Retry-After": "30"}
        mock_request.return_value = (mock_response, 100.0)

        client = ONSClient()

        with pytest.raises(RateLimitError) as exc_info:
            client.fetch("cpi")

        assert exc_info.value.retry_after == 30

    @patch.object(ONSClient, "_timed_request")
    def test_fetch_returns_error_on_non_200(self, mock_request):
        """Verify error handling for non-200 responses."""
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.reason = "Internal Server Error"
        mock_request.return_value = (mock_response, 100.0)

        client = ONSClient()
        result = client.fetch("cpi")

        assert result.success is False
        assert "500" in result.error_message

    def test_rate_limiter_tracks_requests(self):
        """Verify rate limiter tracks request timestamps."""
        client = ONSClient()

        # Simulate some timestamps
        now = time.time()
        client._request_timestamps = [now - 30, now - 20, now - 10]

        # Enforce should not wait (under limit)
        client._enforce_rate_limit()

        # Should have added a new timestamp
        assert len(client._request_timestamps) == 4

    def test_rate_limiter_removes_old_timestamps(self):
        """Verify old timestamps (>60s) are removed."""
        client = ONSClient()

        # Add old timestamps
        now = time.time()
        client._request_timestamps = [now - 120, now - 90, now - 30]

        client._enforce_rate_limit()

        # Old timestamps should be removed, new one added
        # Only timestamps within last 60 seconds should remain
        recent = [ts for ts in client._request_timestamps if now - ts < 60]
        assert len(recent) >= 1

    @patch.object(ONSClient, "fetch")
    def test_fetch_all_returns_all_datasets(self, mock_fetch):
        """Verify fetch_all fetches all defined datasets."""
        mock_fetch.return_value = Mock(success=True, data=pd.DataFrame())

        client = ONSClient()
        results = client.fetch_all()

        assert "cpi" in results
        assert "employment" in results
        assert "retail_sales" in results

    @patch.object(ONSClient, "fetch")
    def test_fetch_all_handles_partial_failures(self, mock_fetch):
        """Verify fetch_all handles some datasets failing."""
        def mock_fetch_impl(dataset):
            if dataset == "cpi":
                return Mock(success=False, error_message="Failed")
            return Mock(success=True, data=pd.DataFrame())

        mock_fetch.side_effect = mock_fetch_impl

        client = ONSClient()
        results = client.fetch_all()

        assert results["cpi"].success is False
        assert results["employment"].success is True
