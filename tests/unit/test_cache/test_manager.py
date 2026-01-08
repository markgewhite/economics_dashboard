"""Unit tests for CacheManager."""

from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import pandas as pd
import pytest

from data.cache.manager import CacheManager
from data.cache.scheduler import RefreshScheduler
from data.models.cache import CacheMetadata, RefreshReason


class TestCacheManager:
    """Tests for CacheManager."""

    @pytest.fixture
    def cache_dir(self, tmp_path):
        """Create temporary cache directory."""
        return tmp_path / "cache"

    @pytest.fixture
    def manager(self, cache_dir):
        """Create CacheManager instance."""
        return CacheManager(cache_dir)

    @pytest.fixture
    def sample_df(self):
        """Create sample DataFrame for testing."""
        return pd.DataFrame({
            "date": pd.date_range("2024-01-01", periods=10, freq="D"),
            "value": range(10),
        })

    @pytest.fixture
    def uk_tz(self):
        """UK timezone."""
        return ZoneInfo("Europe/London")

    def test_creates_directories_on_init(self, cache_dir):
        """Verify cache directories are created."""
        manager = CacheManager(cache_dir)

        assert manager.processed_dir.exists()
        assert manager.metadata_dir.exists()

    def test_get_returns_none_for_missing_dataset(self, manager):
        """Verify get returns None tuple for uncached dataset."""
        data, metadata = manager.get("monetary")

        assert data is None
        assert metadata is None

    def test_put_stores_data_and_metadata(self, manager, sample_df):
        """Verify put stores both data and metadata."""
        metadata = manager.put(
            "monetary",
            sample_df,
            RefreshReason.INITIAL_FETCH,
        )

        assert metadata.dataset == "monetary"
        assert metadata.record_count == 10
        assert metadata.refresh_reason == RefreshReason.INITIAL_FETCH

        # Verify files exist
        assert (manager.processed_dir / "monetary.parquet").exists()
        assert (manager.metadata_dir / "monetary.json").exists()

    def test_put_then_get_round_trip(self, manager, sample_df):
        """Verify data survives put/get round trip."""
        manager.put("monetary", sample_df, RefreshReason.INITIAL_FETCH)

        data, metadata = manager.get("monetary")

        assert data is not None
        assert len(data) == 10
        assert metadata is not None
        assert metadata.dataset == "monetary"

    def test_put_extracts_data_date(self, manager, sample_df):
        """Verify data_date is extracted from date column."""
        metadata = manager.put(
            "monetary",
            sample_df,
            RefreshReason.INITIAL_FETCH,
        )

        # Should be last date in DataFrame
        assert metadata.data_date == "2024-01-10"

    def test_put_handles_ref_month_column(self, manager):
        """Verify ref_month column is recognized for data_date."""
        df = pd.DataFrame({
            "ref_month": pd.date_range("2024-01-01", periods=5, freq="MS"),
            "value": range(5),
        })

        metadata = manager.put("housing", df, RefreshReason.INITIAL_FETCH)

        assert metadata.data_date == "2024-05-01"

    def test_get_metadata_without_data(self, manager, sample_df):
        """Verify metadata can be loaded independently."""
        manager.put("monetary", sample_df, RefreshReason.INITIAL_FETCH)

        metadata = manager.get_metadata("monetary")

        assert metadata is not None
        assert metadata.dataset == "monetary"

    def test_get_metadata_returns_none_if_missing(self, manager):
        """Verify get_metadata returns None for uncached dataset."""
        metadata = manager.get_metadata("monetary")

        assert metadata is None

    def test_invalidate_removes_data_and_metadata(self, manager, sample_df):
        """Verify invalidate removes both files."""
        manager.put("monetary", sample_df, RefreshReason.INITIAL_FETCH)

        # Verify exists
        assert manager.exists("monetary")

        manager.invalidate("monetary")

        # Verify removed
        assert not manager.exists("monetary")
        data, metadata = manager.get("monetary")
        assert data is None
        assert metadata is None

    def test_invalidate_all_clears_everything(self, manager, sample_df):
        """Verify invalidate_all clears all datasets."""
        for dataset in ["monetary", "housing", "economic"]:
            manager.put(dataset, sample_df, RefreshReason.INITIAL_FETCH)

        manager.invalidate_all()

        for dataset in ["monetary", "housing", "economic"]:
            assert not manager.exists(dataset)

    def test_needs_refresh_returns_decision(self, manager, sample_df):
        """Verify needs_refresh returns RefreshDecision."""
        # Uncached - should need refresh
        decision = manager.needs_refresh("monetary")
        assert decision.should_refresh is True
        assert decision.reason == RefreshReason.INITIAL_FETCH

        # Cache it
        manager.put("monetary", sample_df, RefreshReason.INITIAL_FETCH)

        # Now check again - depends on current time vs schedule
        decision = manager.needs_refresh("monetary")
        assert isinstance(decision.should_refresh, bool)

    def test_mark_stale_updates_metadata(self, manager, sample_df):
        """Verify mark_stale sets is_stale flag."""
        manager.put("monetary", sample_df, RefreshReason.DAILY_UPDATE_EXPECTED)

        manager.mark_stale("monetary")

        metadata = manager.get_metadata("monetary")
        assert metadata.is_stale is True
        assert metadata.refresh_reason == RefreshReason.FETCH_FAILED_USING_STALE

    def test_mark_stale_does_nothing_if_not_cached(self, manager):
        """Verify mark_stale doesn't fail for uncached dataset."""
        # Should not raise
        manager.mark_stale("monetary")

    def test_get_all_metadata(self, manager, sample_df):
        """Verify get_all_metadata returns dict for all datasets."""
        manager.put("monetary", sample_df, RefreshReason.INITIAL_FETCH)
        manager.put("housing", sample_df, RefreshReason.INITIAL_FETCH)

        all_meta = manager.get_all_metadata()

        assert "monetary" in all_meta
        assert "housing" in all_meta
        assert "economic" in all_meta
        assert all_meta["monetary"] is not None
        assert all_meta["housing"] is not None
        assert all_meta["economic"] is None  # Not cached

    def test_get_cache_status(self, manager, sample_df):
        """Verify get_cache_status returns comprehensive status."""
        manager.put("monetary", sample_df, RefreshReason.INITIAL_FETCH)

        status = manager.get_cache_status()

        assert "monetary" in status
        assert status["monetary"]["cached"] is True
        assert status["monetary"]["record_count"] == 10
        assert status["monetary"]["data_date"] == "2024-01-10"
        assert "age_description" in status["monetary"]

        assert "housing" in status
        assert status["housing"]["cached"] is False
        assert status["housing"]["needs_refresh"] is True

    def test_exists_returns_false_for_missing(self, manager):
        """Verify exists returns False for uncached dataset."""
        assert manager.exists("monetary") is False

    def test_exists_returns_true_for_cached(self, manager, sample_df):
        """Verify exists returns True for cached dataset."""
        manager.put("monetary", sample_df, RefreshReason.INITIAL_FETCH)
        assert manager.exists("monetary") is True

    def test_custom_scheduler_injection(self, cache_dir):
        """Verify custom scheduler can be injected."""
        scheduler = RefreshScheduler()
        manager = CacheManager(cache_dir, scheduler=scheduler)

        assert manager.scheduler is scheduler

    def test_lazy_scheduler_initialization(self, cache_dir):
        """Verify scheduler is created lazily if not provided."""
        manager = CacheManager(cache_dir)

        # Scheduler should be None initially
        assert manager._scheduler is None

        # Access scheduler property
        scheduler = manager.scheduler

        assert scheduler is not None
        assert isinstance(scheduler, RefreshScheduler)


class TestCacheManagerEdgeCases:
    """Edge case tests for CacheManager."""

    @pytest.fixture
    def cache_dir(self, tmp_path):
        """Create temporary cache directory."""
        return tmp_path / "cache"

    @pytest.fixture
    def manager(self, cache_dir):
        """Create CacheManager instance."""
        return CacheManager(cache_dir)

    @pytest.fixture
    def sample_df(self):
        """Create sample DataFrame for testing."""
        return pd.DataFrame({
            "date": pd.date_range("2024-01-01", periods=10, freq="D"),
            "value": range(10),
        })

    def test_handles_empty_dataframe(self, manager):
        """Verify empty DataFrame is handled."""
        df = pd.DataFrame({"value": []})

        metadata = manager.put("monetary", df, RefreshReason.INITIAL_FETCH)

        assert metadata.record_count == 0
        assert metadata.data_date == "unknown"

    def test_handles_dataframe_without_date_column(self, manager):
        """Verify DataFrame without standard date column is handled."""
        df = pd.DataFrame({"value": [1, 2, 3]})

        metadata = manager.put("monetary", df, RefreshReason.INITIAL_FETCH)

        assert metadata.data_date == "unknown"

    def test_corrupted_metadata_returns_none(self, manager, sample_df):
        """Verify corrupted metadata file returns None gracefully."""
        manager.put("monetary", sample_df, RefreshReason.INITIAL_FETCH)

        # Corrupt the metadata file
        meta_path = manager.metadata_dir / "monetary.json"
        meta_path.write_text("not valid json")

        metadata = manager.get_metadata("monetary")
        assert metadata is None

    def test_corrupted_data_returns_none(self, manager, sample_df):
        """Verify corrupted data file returns None gracefully."""
        manager.put("monetary", sample_df, RefreshReason.INITIAL_FETCH)

        # Corrupt the data file
        data_path = manager.processed_dir / "monetary.parquet"
        data_path.write_bytes(b"not valid parquet")

        data, metadata = manager.get("monetary")
        assert data is None
        assert metadata is None

    def test_path_as_string(self, tmp_path):
        """Verify cache_dir can be passed as string."""
        cache_dir = str(tmp_path / "cache")
        manager = CacheManager(cache_dir)

        assert manager.cache_dir == Path(cache_dir)
        assert manager.processed_dir.exists()
