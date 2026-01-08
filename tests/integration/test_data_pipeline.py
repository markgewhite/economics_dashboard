"""Integration tests for the data service pipeline."""

from datetime import datetime, date
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from zoneinfo import ZoneInfo

import pandas as pd
import pytest

from app.services.data_service import DataService, DashboardData
from data.clients.base import FetchResult
from data.models.housing import Region
from data.models.cache import RefreshReason


class TestDashboardData:
    """Tests for DashboardData dataclass."""

    def test_is_complete_all_present(self):
        """Verify is_complete returns True when all data present."""
        data = DashboardData(
            monetary=Mock(),
            housing=Mock(),
            economic=Mock(),
        )
        assert data.is_complete is True

    def test_is_complete_missing_data(self):
        """Verify is_complete returns False when data missing."""
        data = DashboardData(
            monetary=Mock(),
            housing=None,
            economic=Mock(),
        )
        assert data.is_complete is False

    def test_has_errors_with_errors(self):
        """Verify has_errors returns True when errors present."""
        data = DashboardData(errors=["Error 1", "Error 2"])
        assert data.has_errors is True

    def test_has_errors_no_errors(self):
        """Verify has_errors returns False when no errors."""
        data = DashboardData()
        assert data.has_errors is False

    def test_has_any_data_partial(self):
        """Verify has_any_data returns True with partial data."""
        data = DashboardData(monetary=Mock())
        assert data.has_any_data is True

    def test_has_any_data_none(self):
        """Verify has_any_data returns False with no data."""
        data = DashboardData()
        assert data.has_any_data is False


class TestDataServiceInit:
    """Tests for DataService initialization."""

    def test_creates_cache_directory(self, tmp_path):
        """Verify cache directories are created."""
        cache_dir = tmp_path / "cache"
        service = DataService(cache_dir)

        assert service.cache.processed_dir.exists()
        assert service.cache.metadata_dir.exists()

    def test_lazy_client_initialization(self, tmp_path):
        """Verify clients are not initialized until needed."""
        service = DataService(tmp_path)

        assert service._boe_client is None
        assert service._lr_client is None
        assert service._ons_client is None

    def test_client_property_initializes(self, tmp_path):
        """Verify client properties initialize on access."""
        service = DataService(tmp_path)

        _ = service.boe_client
        assert service._boe_client is not None

    def test_context_manager(self, tmp_path):
        """Verify context manager closes clients."""
        with DataService(tmp_path) as service:
            _ = service.boe_client
            assert service._boe_client is not None

        # After exit, client should be closed
        # (we can't easily verify this without mocking)


class TestDataServiceMonetary:
    """Tests for monetary data fetching."""

    @pytest.fixture
    def service(self, tmp_path):
        """Create service instance."""
        return DataService(tmp_path)

    @pytest.fixture
    def sample_monetary_df(self):
        """Sample monetary DataFrame."""
        return pd.DataFrame({
            "date": pd.date_range("2024-01-31", periods=12, freq="ME"),
            "bank_rate": [5.0 + i * 0.05 for i in range(12)],
            "mortgage_2yr": [5.5 + i * 0.03 for i in range(12)],
            "mortgage_5yr": [5.0 + i * 0.02 for i in range(12)],
        })

    def test_fetch_monetary_success(self, service, sample_monetary_df):
        """Verify successful monetary fetch."""
        mock_client = Mock()
        mock_client.fetch.return_value = FetchResult.ok(sample_monetary_df)
        service._boe_client = mock_client

        data = service.get_dashboard_data()

        assert data.monetary is not None
        assert data.metadata["monetary"] is not None

    def test_fetch_monetary_cached(self, service, sample_monetary_df):
        """Verify cached monetary data is used."""
        # First fetch
        mock_client = Mock()
        mock_client.fetch.return_value = FetchResult.ok(sample_monetary_df)
        service._boe_client = mock_client
        service.get_dashboard_data()

        # Reset mock call count
        mock_client.reset_mock()

        # Force cache to be considered fresh by mocking scheduler
        with patch.object(service.scheduler, "should_refresh") as mock_refresh:
            mock_refresh.return_value = Mock(
                should_refresh=False,
                reason=RefreshReason.ALREADY_CURRENT,
            )

            data = service.get_dashboard_data()

            assert data.monetary is not None
            mock_client.fetch.assert_not_called()

    def test_fetch_monetary_fallback_to_stale(self, service, sample_monetary_df):
        """Verify fallback to stale cache when fetch fails."""
        # First successful fetch
        mock_client = Mock()
        mock_client.fetch.return_value = FetchResult.ok(sample_monetary_df)
        service._boe_client = mock_client
        service.get_dashboard_data(force_refresh=True)

        # Second fetch fails but stale cache is available
        mock_client.fetch.return_value = FetchResult.error("API error")

        data = service.get_dashboard_data(force_refresh=True)

        # Should still have data from stale cache
        assert data.monetary is not None
        assert "stale" in data.warnings[0].lower()


class TestDataServiceHousing:
    """Tests for housing data fetching."""

    @pytest.fixture
    def service(self, tmp_path):
        """Create service instance."""
        return DataService(tmp_path)

    @pytest.fixture
    def sample_housing_results(self):
        """Sample housing FetchResults."""
        def make_region_df(region_value):
            return pd.DataFrame({
                "ref_month": pd.date_range("2024-01-01", periods=6, freq="MS"),
                "region": [region_value] * 6,
                "average_price": [300000 + i * 1000 for i in range(6)],
                "house_price_index": [150 + i * 0.5 for i in range(6)],
                "monthly_change_pct": [0.3] * 6,
                "annual_change_pct": [3.0] * 6,
            })

        return {
            Region.ENGLAND: FetchResult.ok(make_region_df("england")),
            Region.LONDON: FetchResult.ok(make_region_df("london")),
            Region.SCOTLAND: FetchResult.error("API error"),
        }

    def test_fetch_housing_partial_success(self, service, sample_housing_results):
        """Verify housing data with partial region success."""
        mock_client = Mock()
        mock_client.fetch_all_regions.return_value = sample_housing_results
        service._lr_client = mock_client

        data = service.get_dashboard_data()

        assert data.housing is not None
        # Should have England and London, not Scotland
        assert Region.ENGLAND in data.housing.regions
        assert Region.LONDON in data.housing.regions

    def test_housing_cached_roundtrip(self, service, sample_housing_results):
        """Verify housing data survives cache roundtrip."""
        # First fetch
        mock_client = Mock()
        mock_client.fetch_all_regions.return_value = sample_housing_results
        service._lr_client = mock_client
        data1 = service.get_dashboard_data()

        # Second fetch from cache
        with patch.object(service.scheduler, "should_refresh") as mock_refresh:
            mock_refresh.return_value = Mock(
                should_refresh=False,
                reason=RefreshReason.ALREADY_CURRENT,
            )

            data2 = service.get_dashboard_data()

            assert data2.housing is not None
            # Verify regions survived
            assert Region.ENGLAND in data2.housing.regions


class TestDataServiceEconomic:
    """Tests for economic data fetching."""

    @pytest.fixture
    def service(self, tmp_path):
        """Create service instance."""
        return DataService(tmp_path)

    @pytest.fixture
    def sample_economic_results(self):
        """Sample economic FetchResults."""
        dates = pd.date_range("2024-01-01", periods=12, freq="MS")

        return {
            "cpi": FetchResult.ok(pd.DataFrame({
                "date": dates,
                "value": [3.0 + i * 0.1 for i in range(12)],
                "dataset": ["cpi"] * 12,
            })),
            "employment": FetchResult.ok(pd.DataFrame({
                "date": dates,
                "value": [75.0 + i * 0.1 for i in range(12)],
                "dataset": ["employment"] * 12,
            })),
            "retail_sales": FetchResult.error("API error"),
        }

    def test_fetch_economic_partial_success(self, service, sample_economic_results):
        """Verify economic data with partial dataset success."""
        mock_client = Mock()
        mock_client.fetch_all.return_value = sample_economic_results
        service._ons_client = mock_client

        data = service.get_dashboard_data()

        assert data.economic is not None
        # Should have CPI and employment data
        assert any(dp.cpi_annual_rate is not None for dp in data.economic.data_points)

    def test_economic_cached_roundtrip(self, service, sample_economic_results):
        """Verify economic data survives cache roundtrip."""
        # First fetch
        mock_client = Mock()
        mock_client.fetch_all.return_value = sample_economic_results
        service._ons_client = mock_client
        data1 = service.get_dashboard_data()

        # Second fetch from cache
        with patch.object(service.scheduler, "should_refresh") as mock_refresh:
            mock_refresh.return_value = Mock(
                should_refresh=False,
                reason=RefreshReason.ALREADY_CURRENT,
            )

            data2 = service.get_dashboard_data()

            assert data2.economic is not None


class TestDataServiceRefreshStatus:
    """Tests for refresh status API."""

    @pytest.fixture
    def service(self, tmp_path):
        """Create service instance."""
        return DataService(tmp_path)

    def test_refresh_status_empty_cache(self, service):
        """Verify refresh status with empty cache."""
        status = service.get_refresh_status()

        assert "monetary" in status
        assert "housing" in status
        assert "economic" in status
        assert status["monetary"]["cached"] is False

    def test_refresh_status_with_data(self, service):
        """Verify refresh status after data fetch."""
        sample_df = pd.DataFrame({
            "date": pd.date_range("2024-01-31", periods=3, freq="ME"),
            "bank_rate": [5.0, 5.1, 5.2],
        })

        mock_client = Mock()
        mock_client.fetch.return_value = FetchResult.ok(sample_df)
        service._boe_client = mock_client
        service.get_dashboard_data()

        status = service.get_refresh_status()

        assert status["monetary"]["cached"] is True
        assert "age_description" in status["monetary"]


class TestDataServiceInvalidation:
    """Tests for cache invalidation."""

    @pytest.fixture
    def service(self, tmp_path):
        """Create service instance."""
        return DataService(tmp_path)

    def test_invalidate_specific_dataset(self, service):
        """Verify specific dataset invalidation."""
        sample_df = pd.DataFrame({
            "date": pd.date_range("2024-01-31", periods=3, freq="ME"),
            "bank_rate": [5.0, 5.1, 5.2],
        })

        mock_client = Mock()
        mock_client.fetch.return_value = FetchResult.ok(sample_df)
        service._boe_client = mock_client
        service.get_dashboard_data()

        assert service.cache.exists("monetary")

        service.invalidate_cache("monetary")

        assert not service.cache.exists("monetary")

    def test_invalidate_all_datasets(self, service):
        """Verify all datasets invalidation."""
        sample_df = pd.DataFrame({
            "date": pd.date_range("2024-01-31", periods=3, freq="ME"),
            "bank_rate": [5.0, 5.1, 5.2],
        })

        mock_client = Mock()
        mock_client.fetch.return_value = FetchResult.ok(sample_df)
        service._boe_client = mock_client
        service.get_dashboard_data()

        service.invalidate_cache()

        assert not service.cache.exists("monetary")


class TestDataServiceForceRefresh:
    """Tests for force refresh functionality."""

    @pytest.fixture
    def service(self, tmp_path):
        """Create service instance."""
        return DataService(tmp_path)

    def test_force_refresh_bypasses_cache(self, service):
        """Verify force_refresh fetches even with valid cache."""
        sample_df = pd.DataFrame({
            "date": pd.date_range("2024-01-31", periods=3, freq="ME"),
            "bank_rate": [5.0, 5.1, 5.2],
        })

        # First fetch
        mock_client = Mock()
        mock_client.fetch.return_value = FetchResult.ok(sample_df)
        service._boe_client = mock_client
        service.get_dashboard_data()
        first_call_count = mock_client.fetch.call_count

        # Reset mock for second fetch
        mock_client.reset_mock()

        # Second fetch with force_refresh
        service.get_dashboard_data(force_refresh=True)

        # Should have been called despite valid cache
        assert mock_client.fetch.call_count == 1
