"""Unit tests for HousingTransformer."""

from datetime import date
from unittest.mock import Mock

import pandas as pd
import pytest

from data.transformers.housing import HousingTransformer
from data.models.housing import (
    Region,
    HousingTimeSeries,
    HousingDataPoint,
    RegionalHousingData,
)
from data.clients.base import FetchResult


class TestHousingTransformer:
    """Tests for HousingTransformer."""

    @pytest.fixture
    def transformer(self):
        """Create transformer instance."""
        return HousingTransformer()

    @pytest.fixture
    def sample_region_data(self):
        """Sample housing data for a single region."""
        return pd.DataFrame({
            "ref_month": pd.date_range("2024-01-01", periods=12, freq="MS"),
            "region": ["england"] * 12,
            "average_price": [300000 + i * 1000 for i in range(12)],
            "house_price_index": [150 + i * 0.5 for i in range(12)],
            "monthly_change_pct": [0.3] * 12,
            "annual_change_pct": [3.0 + i * 0.1 for i in range(12)],
            "sales_volume": [60000 + i * 500 for i in range(10)] + [None, None],
            "price_detached": [500000 + i * 2000 for i in range(12)],
            "price_semi_detached": [300000 + i * 1000 for i in range(12)],
            "price_terraced": [250000 + i * 800 for i in range(12)],
            "price_flat": [200000 + i * 500 for i in range(12)],
        })

    @pytest.fixture
    def sample_multi_region_data(self, sample_region_data):
        """Sample data for multiple regions."""
        england_result = FetchResult.ok(sample_region_data)

        london_data = sample_region_data.copy()
        london_data["region"] = "london"
        london_data["average_price"] = london_data["average_price"] * 2
        london_result = FetchResult.ok(london_data)

        return {
            Region.ENGLAND: england_result,
            Region.LONDON: london_result,
            Region.SCOTLAND: FetchResult.error("API unavailable"),
        }

    def test_transform_empty_results(self, transformer):
        """Verify empty results dict returns empty RegionalHousingData."""
        result = transformer.transform({})

        assert isinstance(result, RegionalHousingData)
        assert len(result) == 0

    def test_transform_creates_regional_data(
        self, transformer, sample_multi_region_data
    ):
        """Verify regions with data are transformed."""
        result = transformer.transform(sample_multi_region_data)

        assert len(result) == 2  # England and London
        assert Region.ENGLAND in result.regions
        assert Region.LONDON in result.regions
        assert Region.SCOTLAND not in result.regions

    def test_transform_generates_warnings_for_failed_regions(
        self, transformer, sample_multi_region_data
    ):
        """Verify warnings are generated for failed fetches."""
        transformer.transform(sample_multi_region_data)

        assert len(transformer.warnings) > 0
        assert any("Scotland" in w for w in transformer.warnings)

    def test_transform_single_region(self, transformer, sample_region_data):
        """Verify single region transformation works."""
        result = transformer.transform_single(Region.ENGLAND, sample_region_data)

        assert isinstance(result, HousingTimeSeries)
        assert result.region == Region.ENGLAND
        assert len(result) == 12

    def test_transform_creates_data_points(self, transformer, sample_region_data):
        """Verify data points are created correctly."""
        result = transformer.transform_single(Region.ENGLAND, sample_region_data)

        assert all(isinstance(dp, HousingDataPoint) for dp in result.data_points)
        assert all(dp.region == Region.ENGLAND for dp in result.data_points)

    def test_transform_calculates_metrics(self, transformer, sample_region_data):
        """Verify metrics are calculated."""
        result = transformer.transform_single(Region.ENGLAND, sample_region_data)

        assert result.metrics is not None
        assert result.metrics.region == Region.ENGLAND
        assert result.metrics.current_average_price > 0
        assert result.metrics.current_index > 0

    def test_transform_handles_missing_sales_volume(
        self, transformer, sample_region_data
    ):
        """Verify missing sales volume (suppressed months) is handled."""
        result = transformer.transform_single(Region.ENGLAND, sample_region_data)

        # Last two months should have None for sales_volume
        assert result.data_points[-1].sales_volume is None
        assert result.data_points[-2].sales_volume is None
        # Earlier months should have values
        assert result.data_points[0].sales_volume is not None

    def test_transform_validates_ranges(self, transformer):
        """Verify out-of-range values generate warnings."""
        df = pd.DataFrame({
            "ref_month": pd.date_range("2024-01-01", periods=3, freq="MS"),
            "average_price": [300000, 5000000, 300000],  # 5M is out of range
            "house_price_index": [150, 150, 150],
        })

        transformer.transform_single(Region.ENGLAND, df)

        assert len(transformer.warnings) > 0
        assert any("outside expected range" in w for w in transformer.warnings)

    def test_get_region_returns_time_series(
        self, transformer, sample_multi_region_data
    ):
        """Verify get() returns correct time series for region."""
        result = transformer.transform(sample_multi_region_data)

        england_ts = result.get(Region.ENGLAND)
        assert england_ts is not None
        assert england_ts.region == Region.ENGLAND

        scotland_ts = result.get(Region.SCOTLAND)
        assert scotland_ts is None

    def test_to_dataframe(self, transformer, sample_region_data):
        """Verify to_dataframe() works correctly."""
        result = transformer.transform_single(Region.ENGLAND, sample_region_data)
        df = result.to_dataframe()

        assert isinstance(df, pd.DataFrame)
        assert "date" in df.columns
        assert "average_price" in df.columns
        assert len(df) == len(result)

    def test_regional_to_dataframe(self, transformer, sample_multi_region_data):
        """Verify RegionalHousingData.to_dataframe() combines all regions."""
        result = transformer.transform(sample_multi_region_data)
        df = result.to_dataframe()

        assert isinstance(df, pd.DataFrame)
        assert "region" in df.columns
        # Should have data from both England and London
        assert len(df) == 24  # 12 months * 2 regions

    def test_get_heat_map_data(self, transformer, sample_multi_region_data):
        """Verify heat map data preparation."""
        result = transformer.transform(sample_multi_region_data)
        heat_map = result.get_heat_map_data()

        assert len(heat_map) == 2
        for item in heat_map:
            assert "region" in item
            assert "region_name" in item
            assert "annual_change" in item
            assert "average_price" in item

    def test_filter_by_range(self, transformer, sample_region_data):
        """Verify filter_by_range() works correctly."""
        result = transformer.transform_single(Region.ENGLAND, sample_region_data)

        start = date(2024, 4, 1)
        end = date(2024, 8, 31)
        filtered = result.filter_by_range(start, end)

        assert len(filtered) > 0
        assert len(filtered) < len(result)
        for dp in filtered.data_points:
            assert start <= dp.ref_month <= end


class TestHousingTransformerEdgeCases:
    """Edge case tests for HousingTransformer."""

    @pytest.fixture
    def transformer(self):
        """Create transformer instance."""
        return HousingTransformer()

    def test_empty_dataframe(self, transformer):
        """Verify empty DataFrame returns None."""
        df = pd.DataFrame()
        result = transformer.transform_single(Region.ENGLAND, df)

        assert result is None

    def test_single_row_dataframe(self, transformer):
        """Verify single row is handled."""
        df = pd.DataFrame({
            "ref_month": [pd.Timestamp("2024-01-01")],
            "average_price": [300000],
            "house_price_index": [150],
        })

        result = transformer.transform_single(Region.ENGLAND, df)

        assert result is not None
        assert len(result) == 1
        assert result.metrics is not None

    def test_all_failed_regions(self, transformer):
        """Verify all failed regions returns empty RegionalHousingData."""
        data = {
            Region.ENGLAND: FetchResult.error("Failed"),
            Region.LONDON: FetchResult.error("Also failed"),
        }

        result = transformer.transform(data)

        assert len(result) == 0
        assert len(transformer.warnings) == 2

    def test_dates_property(self, transformer):
        """Verify dates property returns correct list."""
        df = pd.DataFrame({
            "ref_month": pd.date_range("2024-01-01", periods=3, freq="MS"),
            "average_price": [300000, 310000, 320000],
            "house_price_index": [150, 151, 152],
        })

        result = transformer.transform_single(Region.ENGLAND, df)

        assert len(result.dates) == 3
        assert all(isinstance(d, date) for d in result.dates)

    def test_average_prices_property(self, transformer):
        """Verify average_prices property returns correct list."""
        df = pd.DataFrame({
            "ref_month": pd.date_range("2024-01-01", periods=3, freq="MS"),
            "average_price": [300000, 310000, 320000],
            "house_price_index": [150, 151, 152],
        })

        result = transformer.transform_single(Region.ENGLAND, df)

        assert len(result.average_prices) == 3
        assert result.average_prices == [300000, 310000, 320000]
