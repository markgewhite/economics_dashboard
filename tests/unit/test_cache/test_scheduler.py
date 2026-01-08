"""Unit tests for RefreshScheduler."""

from datetime import datetime, date, time, timedelta
from zoneinfo import ZoneInfo

import pytest

from data.cache.scheduler import RefreshScheduler, RefreshSchedule, RefreshDecision
from data.models.cache import RefreshReason


class TestRefreshScheduler:
    """Tests for RefreshScheduler."""

    @pytest.fixture
    def scheduler(self):
        """Create a scheduler instance."""
        return RefreshScheduler()

    @pytest.fixture
    def uk_tz(self):
        """UK timezone."""
        return ZoneInfo("Europe/London")

    def test_schedules_defined_for_all_datasets(self, scheduler):
        """Verify schedules are defined for all expected datasets."""
        expected = ["monetary", "housing", "economic"]
        for dataset in expected:
            assert dataset in scheduler.SCHEDULES

    def test_unknown_dataset_raises_error(self, scheduler):
        """Verify unknown dataset raises ValueError."""
        with pytest.raises(ValueError, match="Unknown dataset"):
            scheduler.should_refresh("invalid_dataset", None)

    def test_initial_fetch_always_refreshes(self, scheduler):
        """Verify first fetch (no last_fetch) triggers refresh."""
        decision = scheduler.should_refresh("monetary", None)

        assert decision.should_refresh is True
        assert decision.reason == RefreshReason.INITIAL_FETCH

    # --- Daily refresh tests (monetary data) ---

    def test_daily_already_fetched_today_no_refresh(self, scheduler, uk_tz):
        """If fetched today after check time, no refresh needed."""
        # Fetched today at 11:00
        last_fetch = datetime(2026, 1, 8, 11, 0, tzinfo=uk_tz)

        # Check at 14:00 same day (Wednesday)
        at_time = datetime(2026, 1, 8, 14, 0, tzinfo=uk_tz)
        decision = scheduler.should_refresh_at("monetary", last_fetch, at_time)

        assert decision.should_refresh is False
        assert decision.reason == RefreshReason.ALREADY_CURRENT

    def test_daily_weekend_no_refresh(self, scheduler, uk_tz):
        """No refresh needed on weekends for daily data."""
        # Fetched Friday
        last_fetch = datetime(2026, 1, 3, 11, 0, tzinfo=uk_tz)  # Friday

        # Check on Saturday
        at_time = datetime(2026, 1, 4, 14, 0, tzinfo=uk_tz)  # Saturday
        decision = scheduler.should_refresh_at("monetary", last_fetch, at_time)

        assert decision.should_refresh is False
        assert decision.reason == RefreshReason.CACHED_WEEKEND

    def test_daily_before_check_time_no_refresh(self, scheduler, uk_tz):
        """No refresh before check time even on new day."""
        # Fetched yesterday
        last_fetch = datetime(2026, 1, 7, 11, 0, tzinfo=uk_tz)  # Tuesday

        # Check early Wednesday morning before 10:00
        at_time = datetime(2026, 1, 8, 9, 0, tzinfo=uk_tz)  # Wednesday 9:00
        decision = scheduler.should_refresh_at("monetary", last_fetch, at_time)

        assert decision.should_refresh is False
        assert decision.reason == RefreshReason.CACHED_BEFORE_CHECK_TIME

    def test_daily_after_check_time_new_day_refresh(self, scheduler, uk_tz):
        """Refresh needed after check time on new weekday."""
        # Fetched yesterday
        last_fetch = datetime(2026, 1, 7, 11, 0, tzinfo=uk_tz)  # Tuesday

        # Check Wednesday after 10:00
        at_time = datetime(2026, 1, 8, 11, 0, tzinfo=uk_tz)  # Wednesday 11:00
        decision = scheduler.should_refresh_at("monetary", last_fetch, at_time)

        assert decision.should_refresh is True
        assert decision.reason == RefreshReason.DAILY_UPDATE_EXPECTED

    # --- Monthly refresh tests (housing/economic data) ---

    def test_monthly_same_month_after_pub_no_refresh(self, scheduler, uk_tz):
        """No refresh if fetched this month after publication day."""
        # Housing publishes on 20th
        # Fetched on 21st of this month
        last_fetch = datetime(2026, 1, 21, 16, 0, tzinfo=uk_tz)

        # Check on 25th same month
        at_time = datetime(2026, 1, 25, 10, 0, tzinfo=uk_tz)
        decision = scheduler.should_refresh_at("housing", last_fetch, at_time)

        assert decision.should_refresh is False
        assert decision.reason == RefreshReason.ALREADY_CURRENT

    def test_monthly_before_publication_day_no_refresh(self, scheduler, uk_tz):
        """No refresh before publication day."""
        # Fetched last month
        last_fetch = datetime(2025, 12, 21, 16, 0, tzinfo=uk_tz)

        # Check on 15th (before 20th pub day)
        at_time = datetime(2026, 1, 15, 10, 0, tzinfo=uk_tz)
        decision = scheduler.should_refresh_at("housing", last_fetch, at_time)

        assert decision.should_refresh is False
        assert decision.reason == RefreshReason.CACHED_BEFORE_RELEASE_DAY

    def test_monthly_on_publication_day_before_time_no_refresh(self, scheduler, uk_tz):
        """No refresh on publication day before check time."""
        # Fetched last month
        last_fetch = datetime(2025, 12, 21, 16, 0, tzinfo=uk_tz)

        # Check on 20th at 10:00 (before 15:00 check time)
        at_time = datetime(2026, 1, 20, 10, 0, tzinfo=uk_tz)
        decision = scheduler.should_refresh_at("housing", last_fetch, at_time)

        assert decision.should_refresh is False
        assert decision.reason == RefreshReason.CACHED_BEFORE_CHECK_TIME

    def test_monthly_on_publication_day_after_time_refresh(self, scheduler, uk_tz):
        """Refresh needed on publication day after check time."""
        # Fetched last month
        last_fetch = datetime(2025, 12, 21, 16, 0, tzinfo=uk_tz)

        # Check on 20th at 16:00 (after 15:00 check time)
        at_time = datetime(2026, 1, 20, 16, 0, tzinfo=uk_tz)
        decision = scheduler.should_refresh_at("housing", last_fetch, at_time)

        assert decision.should_refresh is True
        assert decision.reason == RefreshReason.MONTHLY_UPDATE_EXPECTED

    def test_economic_publication_day_15(self, scheduler, uk_tz):
        """Economic data publishes around 15th."""
        # Fetched last month
        last_fetch = datetime(2025, 12, 16, 13, 0, tzinfo=uk_tz)

        # Check on 15th at 13:00 (after 12:00 check time)
        at_time = datetime(2026, 1, 15, 13, 0, tzinfo=uk_tz)
        decision = scheduler.should_refresh_at("economic", last_fetch, at_time)

        assert decision.should_refresh is True
        assert decision.reason == RefreshReason.MONTHLY_UPDATE_EXPECTED

    # --- Business day logic ---

    def test_next_business_day_skips_weekend(self, scheduler, uk_tz):
        """Next business day skips weekends."""
        saturday = date(2026, 1, 3)  # Saturday
        check_time = time(10, 0)

        result = scheduler._next_business_day(saturday, check_time)

        assert result.date() == date(2026, 1, 5)  # Monday
        assert result.time() == check_time

    def test_is_business_day(self, scheduler):
        """Verify business day detection."""
        monday = date(2026, 1, 5)
        saturday = date(2026, 1, 3)
        christmas = date(2025, 12, 25)

        assert scheduler.is_business_day(monday) is True
        assert scheduler.is_business_day(saturday) is False
        assert scheduler.is_business_day(christmas) is False

    # --- Next expected calculation ---

    def test_next_expected_daily(self, scheduler, uk_tz):
        """Next expected for daily data is next business day."""
        at_time = datetime(2026, 1, 8, 14, 0, tzinfo=uk_tz)  # Wednesday
        schedule = scheduler.SCHEDULES["monetary"]

        next_expected = scheduler._calculate_next_expected(schedule, at_time)

        # Should be Thursday at 10:00
        assert next_expected.date() == date(2026, 1, 9)
        assert next_expected.time() == time(10, 0)

    def test_next_expected_monthly(self, scheduler, uk_tz):
        """Next expected for monthly data is next month's pub day."""
        at_time = datetime(2026, 1, 21, 14, 0, tzinfo=uk_tz)  # After Jan publication
        schedule = scheduler.SCHEDULES["housing"]

        next_expected = scheduler._calculate_next_expected(schedule, at_time)

        # Should be Feb 20th at 15:00
        assert next_expected.date() == date(2026, 2, 20)
        assert next_expected.time() == time(15, 0)

    def test_get_schedule(self, scheduler):
        """Verify get_schedule returns correct schedule."""
        schedule = scheduler.get_schedule("monetary")

        assert schedule.frequency == "daily"
        assert schedule.check_time == time(10, 0)


class TestRefreshSchedule:
    """Tests for RefreshSchedule dataclass."""

    def test_daily_schedule_creation(self):
        """Verify daily schedule can be created."""
        schedule = RefreshSchedule(
            frequency="daily",
            check_time=time(10, 0),
            weekdays_only=True,
        )

        assert schedule.frequency == "daily"
        assert schedule.publication_day is None

    def test_monthly_schedule_creation(self):
        """Verify monthly schedule can be created."""
        schedule = RefreshSchedule(
            frequency="monthly",
            check_time=time(15, 0),
            publication_day=20,
            weekdays_only=True,
        )

        assert schedule.frequency == "monthly"
        assert schedule.publication_day == 20


class TestRefreshDecision:
    """Tests for RefreshDecision dataclass."""

    def test_decision_creation(self):
        """Verify decision can be created."""
        uk_tz = ZoneInfo("Europe/London")
        decision = RefreshDecision(
            should_refresh=True,
            reason=RefreshReason.DAILY_UPDATE_EXPECTED,
            next_expected=datetime(2026, 1, 9, 10, 0, tzinfo=uk_tz),
        )

        assert decision.should_refresh is True
        assert decision.reason == RefreshReason.DAILY_UPDATE_EXPECTED
