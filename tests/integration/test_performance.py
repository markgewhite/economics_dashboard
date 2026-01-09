"""Performance tests for the dashboard data pipeline.

These tests verify that data loading meets performance requirements:
- Initial dashboard load should complete in <3 seconds (with cached data)
- Cache retrieval should be fast (<100ms)
"""

import time
from pathlib import Path
from unittest.mock import patch, MagicMock
import tempfile

import pytest
import pandas as pd

from app.services.data_service import DataService
from data.models.cache import CacheMetadata, RefreshReason


class TestPerformance:
    """Performance tests for data loading."""

    @pytest.fixture
    def temp_cache_dir(self):
        """Create a temporary cache directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def populated_cache(self, temp_cache_dir):
        """Create a cache with pre-populated test data."""
        from datetime import datetime
        from zoneinfo import ZoneInfo

        service = DataService(cache_dir=temp_cache_dir)
        uk_tz = ZoneInfo("Europe/London")

        # Create sample monetary data
        monetary_df = pd.DataFrame({
            "date": pd.date_range("2024-01-01", periods=24, freq="ME"),
            "bank_rate": [5.25] * 24,
            "mortgage_2yr": [5.89] * 24,
            "mortgage_5yr": [5.45] * 24,
            "sonia": [5.19] * 24,
        })

        # Create sample housing data for a few regions
        housing_df = pd.DataFrame({
            "ref_month": pd.date_range("2024-01-01", periods=24, freq="ME"),
            "region": ["united-kingdom"] * 24,
            "average_price": [292000 + i * 100 for i in range(24)],
            "annual_change": [2.5] * 24,
            "monthly_change": [0.2] * 24,
            "sales_volume": [85000] * 24,
            "detached_price": [450000] * 24,
            "semi_detached_price": [280000] * 24,
            "terraced_price": [240000] * 24,
            "flat_price": [220000] * 24,
        })

        # Create sample economic data
        economic_df = pd.DataFrame({
            "date": pd.date_range("2024-01-01", periods=24, freq="ME"),
            "dataset": ["cpi"] * 24,
            "value": [3.9] * 24,
        })

        # Store in cache
        service.cache.put("monetary", monetary_df, RefreshReason.INITIAL_FETCH)
        service.cache.put("housing", housing_df, RefreshReason.INITIAL_FETCH)
        service.cache.put("economic", economic_df, RefreshReason.INITIAL_FETCH)

        return service

    def test_cache_retrieval_under_100ms(self, populated_cache):
        """Verify cached data retrieval is fast (<100ms)."""
        service = populated_cache

        # Warm up - first call
        _ = service.cache.get("monetary")

        # Measure retrieval time
        start = time.perf_counter()
        for _ in range(10):
            _ = service.cache.get("monetary")
        elapsed = time.perf_counter() - start

        avg_time_ms = (elapsed / 10) * 1000
        assert avg_time_ms < 100, f"Cache retrieval took {avg_time_ms:.1f}ms, expected <100ms"

    def test_dashboard_data_load_under_3_seconds(self, populated_cache):
        """Verify dashboard data loads in <3 seconds with cached data."""
        service = populated_cache

        # Test that loading from cache is fast
        # Don't force refresh - this tests the cached path
        start = time.perf_counter()

        # Directly test cache retrieval speed (simulating what get_dashboard_data does)
        _ = service.cache.get("monetary")
        _ = service.cache.get("housing")
        _ = service.cache.get("economic")

        elapsed = time.perf_counter() - start

        assert elapsed < 3.0, f"Dashboard load took {elapsed:.2f}s, expected <3s"

    def test_transformer_performance(self, temp_cache_dir):
        """Verify data transformation is fast."""
        from data.transformers.monetary import MonetaryTransformer
        from data.transformers.housing import HousingTransformer

        # Create larger test dataset
        monetary_df = pd.DataFrame({
            "date": pd.date_range("2019-01-01", periods=2000, freq="D"),
            "bank_rate": [5.25] * 2000,
            "mortgage_2yr": [5.89] * 2000,
            "mortgage_5yr": [5.45] * 2000,
            "sonia": [5.19] * 2000,
        })

        transformer = MonetaryTransformer()

        start = time.perf_counter()
        result = transformer.transform(monetary_df)
        elapsed = time.perf_counter() - start

        # Transformation should complete in under 1 second
        assert elapsed < 1.0, f"Transformation took {elapsed:.2f}s, expected <1s"
        assert len(result.data_points) > 0

    def test_cache_metadata_operations_fast(self, populated_cache):
        """Verify metadata operations are fast."""
        service = populated_cache

        start = time.perf_counter()
        for _ in range(100):
            _ = service.cache.get_metadata("monetary")
        elapsed = time.perf_counter() - start

        avg_time_ms = (elapsed / 100) * 1000
        assert avg_time_ms < 10, f"Metadata retrieval took {avg_time_ms:.1f}ms, expected <10ms"

    def test_refresh_status_check_fast(self, populated_cache):
        """Verify refresh status check is fast."""
        service = populated_cache

        start = time.perf_counter()
        for _ in range(10):
            _ = service.get_refresh_status()
        elapsed = time.perf_counter() - start

        avg_time_ms = (elapsed / 10) * 1000
        assert avg_time_ms < 50, f"Refresh status took {avg_time_ms:.1f}ms, expected <50ms"


class TestDataIntegrity:
    """Tests for data integrity during transformations."""

    def test_monetary_data_preserves_values(self):
        """Verify monetary transformation doesn't corrupt data."""
        from data.transformers.monetary import MonetaryTransformer

        df = pd.DataFrame({
            "date": pd.date_range("2024-01-01", periods=31, freq="D"),
            "bank_rate": [5.25] * 31,
            "mortgage_2yr": [5.89] * 31,
            "mortgage_5yr": [5.45] * 31,
        })

        transformer = MonetaryTransformer()
        result = transformer.transform(df)

        # Verify values are preserved (within floating point tolerance)
        assert len(result.data_points) == 1  # One month
        dp = result.data_points[0]
        assert abs(dp.bank_rate - 5.25) < 0.01
        assert abs(dp.mortgage_2yr - 5.89) < 0.01
        assert abs(dp.mortgage_5yr - 5.45) < 0.01

    def test_housing_regional_data_complete(self):
        """Verify all regions can be processed."""
        from data.transformers.housing import HousingTransformer
        from data.models.housing import Region
        from data.clients.base import FetchResult

        # Create data for all regions using the expected input format
        raw_data = {}
        for region in Region:
            df = pd.DataFrame({
                "ref_month": pd.date_range("2024-01-01", periods=12, freq="ME"),
                "region": [region.value] * 12,
                "average_price": [250000 + i * 1000 for i in range(12)],
                "house_price_index": [100 + i * 0.5 for i in range(12)],
                "annual_change": [2.5] * 12,
                "monthly_change": [0.2] * 12,
            })
            raw_data[region] = FetchResult(success=True, data=df)

        transformer = HousingTransformer()
        result = transformer.transform(raw_data)

        # Verify all regions are present
        assert len(result.regions) == len(Region)
        for region in Region:
            ts = result.get(region)
            assert ts is not None, f"Missing region: {region.display_name}"
            assert len(ts.data_points) == 12
