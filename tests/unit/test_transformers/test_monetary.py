"""Unit tests for MonetaryTransformer."""

from datetime import date

import pandas as pd
import pytest

from data.transformers.monetary import MonetaryTransformer
from data.models.monetary import MonetaryTimeSeries, MonetaryDataPoint


class TestMonetaryTransformer:
    """Tests for MonetaryTransformer."""

    @pytest.fixture
    def transformer(self):
        """Create transformer instance."""
        return MonetaryTransformer()

    @pytest.fixture
    def sample_daily_data(self):
        """Sample daily monetary data."""
        dates = pd.date_range("2024-01-01", periods=30, freq="D")
        return pd.DataFrame({
            "date": dates,
            "bank_rate": [5.25] * 30,
            "sonia": [5.2 + i * 0.01 for i in range(30)],
            "mortgage_2yr": [5.95] * 30,
            "mortgage_5yr": [5.45] * 30,
            "gbp_usd": [1.27 + i * 0.001 for i in range(30)],
            "gbp_eur": [1.15 + i * 0.001 for i in range(30)],
        })

    @pytest.fixture
    def sample_monthly_data(self):
        """Sample monthly monetary data spanning 2 years."""
        dates = pd.date_range("2023-01-31", periods=24, freq="ME")
        return pd.DataFrame({
            "date": dates,
            "bank_rate": [4.0 + i * 0.05 for i in range(24)],
            "mortgage_2yr": [5.0 + i * 0.04 for i in range(24)],
            "mortgage_5yr": [4.5 + i * 0.03 for i in range(24)],
        })

    def test_transform_empty_dataframe(self, transformer):
        """Verify empty DataFrame returns empty time series."""
        df = pd.DataFrame()
        result = transformer.transform(df)

        assert isinstance(result, MonetaryTimeSeries)
        assert len(result) == 0
        assert result.metrics is None

    def test_transform_creates_data_points(self, transformer, sample_daily_data):
        """Verify data points are created correctly."""
        result = transformer.transform(sample_daily_data)

        assert len(result) > 0
        assert all(isinstance(dp, MonetaryDataPoint) for dp in result.data_points)

    def test_transform_aggregates_daily_to_monthly(self, transformer, sample_daily_data):
        """Verify daily data is aggregated to monthly."""
        result = transformer.transform(sample_daily_data)

        # 30 days of January should become 1 monthly observation
        assert len(result) == 1

    def test_transform_keeps_monthly_data_as_is(self, transformer, sample_monthly_data):
        """Verify monthly data is not re-aggregated."""
        result = transformer.transform(sample_monthly_data)

        # Should keep same number of monthly observations
        assert len(result) == 24

    def test_transform_calculates_metrics(self, transformer, sample_monthly_data):
        """Verify metrics are calculated."""
        result = transformer.transform(sample_monthly_data)

        assert result.metrics is not None
        assert result.metrics.current_bank_rate > 0
        assert result.metrics.current_mortgage_2yr > 0

    def test_transform_calculates_yoy_change(self, transformer, sample_monthly_data):
        """Verify year-over-year change is calculated."""
        result = transformer.transform(sample_monthly_data)

        assert result.metrics is not None
        # Bank rate increased from 4.0 to ~5.15 over 24 months
        # YoY change should be positive (point change)
        assert result.metrics.bank_rate_change_yoy != 0

    def test_transform_sets_date_range(self, transformer, sample_monthly_data):
        """Verify earliest and latest dates are set."""
        result = transformer.transform(sample_monthly_data)

        assert result.earliest_date is not None
        assert result.latest_date is not None
        assert result.earliest_date <= result.latest_date

    def test_transform_handles_missing_values(self, transformer):
        """Verify missing values are handled with forward fill."""
        df = pd.DataFrame({
            "date": pd.date_range("2024-01-31", periods=5, freq="ME"),
            "bank_rate": [5.0, None, None, 5.25, 5.25],
            "mortgage_2yr": [5.5, 5.5, None, None, 5.75],
        })

        result = transformer.transform(df)

        # After forward fill, no NaN should propagate
        assert len(result) == 5
        # Forward fill should have filled in the gaps
        assert result.data_points[1].bank_rate == 5.0
        assert result.data_points[2].bank_rate == 5.0

    def test_transform_validates_ranges(self, transformer):
        """Verify out-of-range values generate warnings."""
        df = pd.DataFrame({
            "date": pd.date_range("2024-01-31", periods=3, freq="ME"),
            "bank_rate": [5.0, 25.0, 5.0],  # 25.0 is out of range
        })

        transformer.transform(df)

        assert len(transformer.warnings) > 0
        assert any("outside expected range" in w for w in transformer.warnings)

    def test_transform_to_dataframe(self, transformer, sample_monthly_data):
        """Verify to_dataframe() works correctly."""
        result = transformer.transform(sample_monthly_data)
        df = result.to_dataframe()

        assert isinstance(df, pd.DataFrame)
        assert "date" in df.columns
        assert "bank_rate" in df.columns
        assert len(df) == len(result)

    def test_transform_filter_by_range(self, transformer, sample_monthly_data):
        """Verify filter_by_range() works correctly."""
        result = transformer.transform(sample_monthly_data)

        start = date(2023, 6, 1)
        end = date(2023, 12, 31)
        filtered = result.filter_by_range(start, end)

        assert len(filtered) > 0
        assert len(filtered) < len(result)
        for dp in filtered.data_points:
            assert start <= dp.observation_date <= end


class TestMonetaryTransformerEdgeCases:
    """Edge case tests for MonetaryTransformer."""

    @pytest.fixture
    def transformer(self):
        """Create transformer instance."""
        return MonetaryTransformer()

    def test_single_row_dataframe(self, transformer):
        """Verify single row is handled."""
        df = pd.DataFrame({
            "date": [pd.Timestamp("2024-01-31")],
            "bank_rate": [5.25],
            "mortgage_2yr": [5.95],
        })

        result = transformer.transform(df)

        assert len(result) == 1
        # Metrics should be None without YoY data
        assert result.metrics is None or result.metrics.bank_rate_change_yoy == 0

    def test_all_null_column(self, transformer):
        """Verify all-null column is handled."""
        df = pd.DataFrame({
            "date": pd.date_range("2024-01-31", periods=3, freq="ME"),
            "bank_rate": [5.0, 5.1, 5.2],
            "sonia": [None, None, None],
        })

        result = transformer.transform(df)

        assert len(result) == 3
        # SONIA should remain None
        assert all(dp.sonia is None for dp in result.data_points)

    def test_data_points_dates_property(self, transformer):
        """Verify dates property returns correct list."""
        df = pd.DataFrame({
            "date": pd.date_range("2024-01-31", periods=3, freq="ME"),
            "bank_rate": [5.0, 5.1, 5.2],
        })

        result = transformer.transform(df)

        assert len(result.dates) == 3
        assert all(isinstance(d, date) for d in result.dates)

    def test_bank_rates_property(self, transformer):
        """Verify bank_rates property returns correct list."""
        df = pd.DataFrame({
            "date": pd.date_range("2024-01-31", periods=3, freq="ME"),
            "bank_rate": [5.0, 5.1, 5.2],
        })

        result = transformer.transform(df)

        assert len(result.bank_rates) == 3
        assert result.bank_rates == [5.0, 5.1, 5.2]
