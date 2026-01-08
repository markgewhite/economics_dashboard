"""Unit tests for Bank of England API client."""

from datetime import date
from unittest.mock import Mock, patch

import pandas as pd
import pytest

from data.clients.bank_of_england import BankOfEnglandClient


class TestBankOfEnglandClient:
    """Tests for BankOfEnglandClient."""

    def test_client_has_user_agent_header(self):
        """Verify User-Agent header is set (required by BoE API)."""
        client = BankOfEnglandClient()
        assert "User-Agent" in client.session.headers
        assert "UK-Economic-Dashboard" in client.session.headers["User-Agent"]

    def test_series_codes_defined(self):
        """Verify all required series codes are defined."""
        expected_series = [
            "bank_rate",
            "sonia",
            "mortgage_2yr",
            "mortgage_5yr",
            "gbp_usd",
            "gbp_eur",
        ]
        client = BankOfEnglandClient()
        for series in expected_series:
            assert series in client.SERIES_CODES

    def test_build_url_formats_dates_correctly(self):
        """Verify URL date format is DD/Mon/YYYY."""
        client = BankOfEnglandClient()
        url = client._build_url(
            series=["bank_rate"],
            start_date=date(2024, 1, 15),
            end_date=date(2024, 6, 30),
        )
        assert "Datefrom=15/Jan/2024" in url
        assert "Dateto=30/Jun/2024" in url

    def test_build_url_includes_series_codes(self):
        """Verify series codes are included in URL."""
        client = BankOfEnglandClient()
        url = client._build_url(
            series=["bank_rate", "sonia"],
            start_date=date(2024, 1, 1),
            end_date=date(2024, 12, 31),
        )
        assert "SeriesCodes=IUDBEDR,IUDSOIA" in url

    def test_parse_response_handles_missing_values(self, sample_boe_response):
        """Verify '..' values are parsed as NaN."""
        client = BankOfEnglandClient()
        df = client._parse_response(
            sample_boe_response,
            series=["bank_rate", "sonia", "mortgage_2yr", "mortgage_5yr", "gbp_usd", "gbp_eur"],
        )

        # SONIA should have NaN for weekends (03 Jan was a Wednesday but marked missing)
        assert pd.isna(df.loc[df["date"] == pd.Timestamp("2024-01-03"), "sonia"].values[0])

    def test_parse_response_renames_columns(self, sample_boe_response):
        """Verify series code columns are renamed to friendly names."""
        client = BankOfEnglandClient()
        df = client._parse_response(
            sample_boe_response,
            series=["bank_rate", "sonia"],
        )

        assert "bank_rate" in df.columns
        assert "sonia" in df.columns
        # Original codes should not be present
        assert "IUDBEDR" not in df.columns
        assert "IUDSOIA" not in df.columns

    def test_parse_response_parses_dates(self, sample_boe_response):
        """Verify date column is parsed correctly."""
        client = BankOfEnglandClient()
        df = client._parse_response(
            sample_boe_response,
            series=["bank_rate"],
        )

        assert df["date"].dtype == "datetime64[ns]"
        assert df["date"].iloc[0] == pd.Timestamp("2024-01-01")

    def test_parse_response_sorts_by_date(self, sample_boe_response):
        """Verify results are sorted by date ascending."""
        client = BankOfEnglandClient()
        df = client._parse_response(
            sample_boe_response,
            series=["bank_rate"],
        )

        dates = df["date"].tolist()
        assert dates == sorted(dates)

    def test_fetch_validates_series_keys(self):
        """Verify invalid series keys return error."""
        client = BankOfEnglandClient()
        result = client.fetch(series=["invalid_series"])

        assert result.success is False
        assert "Unknown series" in result.error_message

    @patch.object(BankOfEnglandClient, "_timed_request")
    def test_fetch_returns_success_on_200(self, mock_request, sample_boe_response):
        """Verify successful fetch returns data."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = sample_boe_response
        mock_request.return_value = (mock_response, 150.0)

        client = BankOfEnglandClient()
        result = client.fetch(
            series=["bank_rate"],
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 10),
        )

        assert result.success is True
        assert result.data is not None
        assert isinstance(result.data, pd.DataFrame)
        assert result.response_time_ms == 150.0

    @patch.object(BankOfEnglandClient, "_timed_request")
    def test_fetch_returns_error_on_non_200(self, mock_request):
        """Verify error handling for non-200 responses."""
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.reason = "Internal Server Error"
        mock_request.return_value = (mock_response, 100.0)

        client = BankOfEnglandClient()
        result = client.fetch(series=["bank_rate"])

        assert result.success is False
        assert "500" in result.error_message

    def test_default_date_range_is_five_years(self):
        """Verify default date range spans 5 years."""
        client = BankOfEnglandClient()

        with patch.object(client, "_timed_request") as mock_request:
            mock_response = Mock()
            mock_response.status_code = 500
            mock_response.reason = "Test"
            mock_request.return_value = (mock_response, 0)

            client.fetch(series=["bank_rate"])

            called_url = mock_request.call_args[0][0]
            today = date.today()
            five_years_ago = date(today.year - 5, today.month, today.day)

            # Check that the date range is roughly correct
            assert five_years_ago.strftime("%d/%b/%Y") in called_url

    def test_context_manager_closes_session(self):
        """Verify context manager properly closes session."""
        with BankOfEnglandClient() as client:
            # Access session to initialize it
            _ = client.session
            assert client._session is not None

        assert client._session is None
