"""Unit tests for EconomicTransformer."""

from datetime import date

import pandas as pd
import pytest

from data.transformers.economic import EconomicTransformer
from data.models.economic import EconomicTimeSeries, EconomicDataPoint
from data.clients.base import FetchResult


class TestEconomicTransformer:
    """Tests for EconomicTransformer."""

    @pytest.fixture
    def transformer(self):
        """Create transformer instance."""
        return EconomicTransformer()

    @pytest.fixture
    def sample_cpi_data(self):
        """Sample CPI data spanning 2 years."""
        return pd.DataFrame({
            "date": pd.date_range("2023-01-01", periods=24, freq="MS"),
            "value": [10.0 - i * 0.3 for i in range(24)],  # Decreasing inflation
            "dataset": ["cpi"] * 24,
        })

    @pytest.fixture
    def sample_employment_data(self):
        """Sample employment data."""
        return pd.DataFrame({
            "date": pd.date_range("2023-01-01", periods=24, freq="MS"),
            "value": [75.0 + i * 0.1 for i in range(24)],
            "dataset": ["employment"] * 24,
        })

    @pytest.fixture
    def sample_retail_data(self):
        """Sample retail sales data."""
        return pd.DataFrame({
            "date": pd.date_range("2023-01-01", periods=24, freq="MS"),
            "value": [100.0 + i * 0.5 for i in range(24)],
            "dataset": ["retail_sales"] * 24,
        })

    @pytest.fixture
    def sample_all_data(
        self, sample_cpi_data, sample_employment_data, sample_retail_data
    ):
        """All three datasets as FetchResults."""
        return {
            "cpi": FetchResult.ok(sample_cpi_data),
            "employment": FetchResult.ok(sample_employment_data),
            "retail_sales": FetchResult.ok(sample_retail_data),
        }

    def test_transform_empty_results(self, transformer):
        """Verify empty results dict returns empty time series."""
        result = transformer.transform({})

        assert isinstance(result, EconomicTimeSeries)
        assert len(result) == 0
        assert result.metrics is None

    def test_transform_creates_data_points(self, transformer, sample_all_data):
        """Verify data points are created correctly."""
        result = transformer.transform(sample_all_data)

        assert len(result) > 0
        assert all(isinstance(dp, EconomicDataPoint) for dp in result.data_points)

    def test_transform_merges_datasets(self, transformer, sample_all_data):
        """Verify datasets are merged on date."""
        result = transformer.transform(sample_all_data)

        # All dates should have all three metrics
        for dp in result.data_points:
            assert dp.cpi_annual_rate is not None
            assert dp.employment_rate is not None
            assert dp.retail_sales_index is not None

    def test_transform_calculates_metrics(self, transformer, sample_all_data):
        """Verify metrics are calculated."""
        result = transformer.transform(sample_all_data)

        assert result.metrics is not None
        assert result.metrics.current_cpi is not None
        assert result.metrics.current_employment > 0
        assert result.metrics.current_retail_index > 0

    def test_transform_calculates_yoy_change(self, transformer, sample_all_data):
        """Verify year-over-year change is calculated."""
        result = transformer.transform(sample_all_data)

        assert result.metrics is not None
        # CPI decreased over the year, so YoY change should be negative
        assert result.metrics.cpi_change_yoy != 0

    def test_transform_sets_date_range(self, transformer, sample_all_data):
        """Verify earliest and latest dates are set."""
        result = transformer.transform(sample_all_data)

        assert result.earliest_date is not None
        assert result.latest_date is not None
        assert result.earliest_date <= result.latest_date

    def test_transform_handles_partial_data(
        self, transformer, sample_cpi_data, sample_employment_data
    ):
        """Verify transformation works with partial datasets."""
        data = {
            "cpi": FetchResult.ok(sample_cpi_data),
            "employment": FetchResult.ok(sample_employment_data),
            "retail_sales": FetchResult.error("API unavailable"),
        }

        result = transformer.transform(data)

        assert len(result) > 0
        # Retail should be None, others should have values
        for dp in result.data_points:
            assert dp.cpi_annual_rate is not None
            assert dp.employment_rate is not None
            assert dp.retail_sales_index is None

    def test_transform_generates_warnings_for_failed_fetches(
        self, transformer, sample_cpi_data
    ):
        """Verify warnings are generated for failed fetches."""
        data = {
            "cpi": FetchResult.ok(sample_cpi_data),
            "employment": FetchResult.error("Failed"),
        }

        transformer.transform(data)

        assert len(transformer.warnings) > 0
        assert any("employment" in w for w in transformer.warnings)

    def test_transform_validates_ranges(self, transformer):
        """Verify out-of-range values generate warnings."""
        df = pd.DataFrame({
            "date": pd.date_range("2024-01-01", periods=3, freq="MS"),
            "value": [5.0, 30.0, 5.0],  # 30.0 is out of range for CPI
            "dataset": ["cpi"] * 3,
        })

        transformer.transform({"cpi": FetchResult.ok(df)})

        assert len(transformer.warnings) > 0
        assert any("outside expected range" in w for w in transformer.warnings)

    def test_transform_single_dataset(self, transformer, sample_cpi_data):
        """Verify single dataset transformation works."""
        result = transformer.transform_single("cpi", sample_cpi_data)

        assert len(result) > 0
        for dp in result.data_points:
            assert dp.cpi_annual_rate is not None
            assert dp.employment_rate is None
            assert dp.retail_sales_index is None

    def test_to_dataframe(self, transformer, sample_all_data):
        """Verify to_dataframe() works correctly."""
        result = transformer.transform(sample_all_data)
        df = result.to_dataframe()

        assert isinstance(df, pd.DataFrame)
        assert "date" in df.columns
        assert "cpi_annual_rate" in df.columns
        assert "employment_rate" in df.columns
        assert "retail_sales_index" in df.columns
        assert len(df) == len(result)

    def test_filter_by_range(self, transformer, sample_all_data):
        """Verify filter_by_range() works correctly."""
        result = transformer.transform(sample_all_data)

        start = date(2023, 6, 1)
        end = date(2023, 12, 31)
        filtered = result.filter_by_range(start, end)

        assert len(filtered) > 0
        assert len(filtered) < len(result)
        for dp in filtered.data_points:
            assert start <= dp.ref_month <= end


class TestEconomicTransformerEdgeCases:
    """Edge case tests for EconomicTransformer."""

    @pytest.fixture
    def transformer(self):
        """Create transformer instance."""
        return EconomicTransformer()

    def test_all_failed_fetches(self, transformer):
        """Verify all failed fetches returns empty time series."""
        data = {
            "cpi": FetchResult.error("Failed"),
            "employment": FetchResult.error("Also failed"),
        }

        result = transformer.transform(data)

        assert len(result) == 0
        assert result.metrics is None
        assert len(transformer.warnings) == 2

    def test_single_row_data(self, transformer):
        """Verify single row is handled."""
        df = pd.DataFrame({
            "date": [pd.Timestamp("2024-01-01")],
            "value": [3.0],
            "dataset": ["cpi"],
        })

        result = transformer.transform({"cpi": FetchResult.ok(df)})

        assert len(result) == 1
        # Metrics should exist but YoY change should be 0
        assert result.metrics is not None
        assert result.metrics.cpi_change_yoy == 0

    def test_misaligned_dates(self, transformer):
        """Verify datasets with different dates are merged correctly."""
        cpi = pd.DataFrame({
            "date": pd.date_range("2024-01-01", periods=3, freq="MS"),
            "value": [3.0, 3.1, 3.2],
            "dataset": ["cpi"] * 3,
        })

        employment = pd.DataFrame({
            "date": pd.date_range("2024-02-01", periods=3, freq="MS"),
            "value": [75.0, 75.1, 75.2],
            "dataset": ["employment"] * 3,
        })

        result = transformer.transform({
            "cpi": FetchResult.ok(cpi),
            "employment": FetchResult.ok(employment),
        })

        # Should have 4 months: Jan (CPI only), Feb-Mar (both), Apr (employment only)
        assert len(result) == 4

        # Jan should have CPI but no employment
        jan_dp = next(dp for dp in result.data_points if dp.ref_month.month == 1)
        assert jan_dp.cpi_annual_rate is not None
        assert jan_dp.employment_rate is None

    def test_dates_property(self, transformer):
        """Verify dates property returns correct list."""
        df = pd.DataFrame({
            "date": pd.date_range("2024-01-01", periods=3, freq="MS"),
            "value": [3.0, 3.1, 3.2],
            "dataset": ["cpi"] * 3,
        })

        result = transformer.transform({"cpi": FetchResult.ok(df)})

        assert len(result.dates) == 3
        assert all(isinstance(d, date) for d in result.dates)

    def test_cpi_values_property(self, transformer):
        """Verify cpi_values property returns correct list."""
        df = pd.DataFrame({
            "date": pd.date_range("2024-01-01", periods=3, freq="MS"),
            "value": [3.0, 3.1, 3.2],
            "dataset": ["cpi"] * 3,
        })

        result = transformer.transform({"cpi": FetchResult.ok(df)})

        assert len(result.cpi_values) == 3
        assert result.cpi_values == [3.0, 3.1, 3.2]

    def test_employment_values_property(self, transformer):
        """Verify employment_values property returns correct list."""
        df = pd.DataFrame({
            "date": pd.date_range("2024-01-01", periods=3, freq="MS"),
            "value": [75.0, 75.1, 75.2],
            "dataset": ["employment"] * 3,
        })

        result = transformer.transform({"employment": FetchResult.ok(df)})

        assert len(result.employment_values) == 3

    def test_retail_values_property(self, transformer):
        """Verify retail_values property returns correct list."""
        df = pd.DataFrame({
            "date": pd.date_range("2024-01-01", periods=3, freq="MS"),
            "value": [100.0, 101.0, 102.0],
            "dataset": ["retail_sales"] * 3,
        })

        result = transformer.transform({"retail_sales": FetchResult.ok(df)})

        assert len(result.retail_values) == 3
