"""Schedule-aware refresh logic for cached data."""

from dataclasses import dataclass
from datetime import datetime, date, time, timedelta
from typing import Optional
from zoneinfo import ZoneInfo
from calendar import monthrange

import holidays

from data.models.cache import RefreshReason


@dataclass
class RefreshSchedule:
    """Configuration for a dataset's refresh schedule."""

    frequency: str  # "daily" or "monthly"
    check_time: time  # Time after which to check for updates (UK time)
    publication_day: Optional[int] = None  # Day of month for monthly
    weekdays_only: bool = True


@dataclass
class RefreshDecision:
    """Result of refresh decision logic."""

    should_refresh: bool
    reason: RefreshReason
    next_expected: datetime


class RefreshScheduler:
    """
    Determines when data refresh is needed based on publication schedules.

    This implements schedule-aware caching rather than arbitrary time intervals,
    minimizing unnecessary API calls while ensuring data freshness.
    """

    # Dataset refresh schedules
    SCHEDULES = {
        "monetary": RefreshSchedule(
            frequency="daily",
            check_time=time(10, 0),  # After 10:00 UK time
            weekdays_only=True,
        ),
        "housing": RefreshSchedule(
            frequency="monthly",
            check_time=time(15, 0),  # After 15:00 UK time
            publication_day=20,  # 20th working day
            weekdays_only=True,
        ),
        "economic": RefreshSchedule(
            frequency="monthly",
            check_time=time(12, 0),  # After 12:00 UK time
            publication_day=15,  # Around 15th
            weekdays_only=True,
        ),
    }

    def __init__(self):
        self.uk_tz = ZoneInfo("Europe/London")
        self.uk_holidays = holidays.UK()

    def should_refresh(
        self,
        dataset: str,
        last_fetch: Optional[datetime],
    ) -> RefreshDecision:
        """
        Determine if dataset needs refresh based on schedule.

        Args:
            dataset: Dataset identifier ("monetary", "housing", "economic")
            last_fetch: Timestamp of last successful fetch (None if never fetched)

        Returns:
            RefreshDecision with should_refresh, reason, and next_expected
        """
        schedule = self.SCHEDULES.get(dataset)
        if not schedule:
            raise ValueError(f"Unknown dataset: {dataset}")

        now = datetime.now(self.uk_tz)

        # Never fetched - refresh needed
        if last_fetch is None:
            return RefreshDecision(
                should_refresh=True,
                reason=RefreshReason.INITIAL_FETCH,
                next_expected=self._calculate_next_expected(schedule, now),
            )

        # Ensure last_fetch is timezone-aware
        if last_fetch.tzinfo is None:
            last_fetch = last_fetch.replace(tzinfo=self.uk_tz)

        if schedule.frequency == "daily":
            return self._check_daily_refresh(schedule, last_fetch, now)
        else:
            return self._check_monthly_refresh(schedule, last_fetch, now)

    def should_refresh_at(
        self,
        dataset: str,
        last_fetch: Optional[datetime],
        at_time: datetime,
    ) -> RefreshDecision:
        """
        Determine if dataset needs refresh at a specific time.

        Useful for testing with controlled timestamps.

        Args:
            dataset: Dataset identifier
            last_fetch: Timestamp of last successful fetch
            at_time: Time to check at (should be timezone-aware)

        Returns:
            RefreshDecision
        """
        schedule = self.SCHEDULES.get(dataset)
        if not schedule:
            raise ValueError(f"Unknown dataset: {dataset}")

        # Ensure at_time is timezone-aware
        if at_time.tzinfo is None:
            at_time = at_time.replace(tzinfo=self.uk_tz)

        # Never fetched - refresh needed
        if last_fetch is None:
            return RefreshDecision(
                should_refresh=True,
                reason=RefreshReason.INITIAL_FETCH,
                next_expected=self._calculate_next_expected(schedule, at_time),
            )

        # Ensure last_fetch is timezone-aware
        if last_fetch.tzinfo is None:
            last_fetch = last_fetch.replace(tzinfo=self.uk_tz)

        if schedule.frequency == "daily":
            return self._check_daily_refresh(schedule, last_fetch, at_time)
        else:
            return self._check_monthly_refresh(schedule, last_fetch, at_time)

    def _check_daily_refresh(
        self,
        schedule: RefreshSchedule,
        last_fetch: datetime,
        now: datetime,
    ) -> RefreshDecision:
        """Check if daily-updated dataset needs refresh."""
        today = now.date()
        last_fetch_date = last_fetch.date()

        # Already fetched today after check time
        if last_fetch_date == today:
            check_datetime = datetime.combine(
                today, schedule.check_time, tzinfo=self.uk_tz
            )
            if last_fetch >= check_datetime:
                return RefreshDecision(
                    should_refresh=False,
                    reason=RefreshReason.ALREADY_CURRENT,
                    next_expected=self._calculate_next_expected(schedule, now),
                )

        # Weekend - no updates published
        if schedule.weekdays_only and today.weekday() >= 5:
            return RefreshDecision(
                should_refresh=False,
                reason=RefreshReason.CACHED_WEEKEND,
                next_expected=self._next_business_day(today, schedule.check_time),
            )

        # UK holiday - no updates published
        if schedule.weekdays_only and today in self.uk_holidays:
            return RefreshDecision(
                should_refresh=False,
                reason=RefreshReason.CACHED_WEEKEND,  # Reuse weekend reason for holidays
                next_expected=self._next_business_day(
                    today + timedelta(days=1), schedule.check_time
                ),
            )

        # Before check time
        check_datetime = datetime.combine(
            today, schedule.check_time, tzinfo=self.uk_tz
        )
        if now < check_datetime:
            return RefreshDecision(
                should_refresh=False,
                reason=RefreshReason.CACHED_BEFORE_CHECK_TIME,
                next_expected=check_datetime,
            )

        # After check time on a weekday - refresh needed
        return RefreshDecision(
            should_refresh=True,
            reason=RefreshReason.DAILY_UPDATE_EXPECTED,
            next_expected=self._calculate_next_expected(schedule, now),
        )

    def _check_monthly_refresh(
        self,
        schedule: RefreshSchedule,
        last_fetch: datetime,
        now: datetime,
    ) -> RefreshDecision:
        """Check if monthly-updated dataset needs refresh."""
        today = now.date()
        last_fetch_date = last_fetch.date()

        # Same month and after publication - already have this month's data
        pub_day = schedule.publication_day or 15
        if (
            last_fetch_date.year == today.year
            and last_fetch_date.month == today.month
            and last_fetch_date.day >= pub_day
        ):
            return RefreshDecision(
                should_refresh=False,
                reason=RefreshReason.ALREADY_CURRENT,
                next_expected=self._calculate_next_expected(schedule, now),
            )

        # Before publication day this month
        if today.day < pub_day:
            return RefreshDecision(
                should_refresh=False,
                reason=RefreshReason.CACHED_BEFORE_RELEASE_DAY,
                next_expected=self._publication_datetime(
                    today.year, today.month, pub_day, schedule.check_time
                ),
            )

        # On or after publication day - check time
        check_datetime = datetime.combine(
            date(today.year, today.month, min(pub_day, monthrange(today.year, today.month)[1])),
            schedule.check_time,
            tzinfo=self.uk_tz,
        )

        if now < check_datetime:
            return RefreshDecision(
                should_refresh=False,
                reason=RefreshReason.CACHED_BEFORE_CHECK_TIME,
                next_expected=check_datetime,
            )

        # After publication day and check time - refresh needed
        return RefreshDecision(
            should_refresh=True,
            reason=RefreshReason.MONTHLY_UPDATE_EXPECTED,
            next_expected=self._calculate_next_expected(schedule, now),
        )

    def _calculate_next_expected(
        self,
        schedule: RefreshSchedule,
        from_datetime: datetime,
    ) -> datetime:
        """Calculate next expected update timestamp."""
        if schedule.frequency == "daily":
            # Next business day at check time
            next_day = from_datetime.date() + timedelta(days=1)
            return self._next_business_day(next_day, schedule.check_time)
        else:
            # Next month's publication day
            year = from_datetime.year
            month = from_datetime.month + 1
            if month > 12:
                month = 1
                year += 1

            pub_day = schedule.publication_day or 15
            return self._publication_datetime(year, month, pub_day, schedule.check_time)

    def _next_business_day(self, from_date: date, at_time: time) -> datetime:
        """Find next business day from given date."""
        check_date = from_date
        while check_date.weekday() >= 5 or check_date in self.uk_holidays:
            check_date += timedelta(days=1)
        return datetime.combine(check_date, at_time, tzinfo=self.uk_tz)

    def _publication_datetime(
        self,
        year: int,
        month: int,
        day: int,
        at_time: time,
    ) -> datetime:
        """Create publication datetime, adjusting for month length."""
        max_day = monthrange(year, month)[1]
        actual_day = min(day, max_day)
        return datetime.combine(
            date(year, month, actual_day),
            at_time,
            tzinfo=self.uk_tz,
        )

    def is_business_day(self, check_date: date) -> bool:
        """Check if date is a UK business day."""
        return check_date.weekday() < 5 and check_date not in self.uk_holidays

    def get_schedule(self, dataset: str) -> RefreshSchedule:
        """Get schedule for a dataset."""
        schedule = self.SCHEDULES.get(dataset)
        if not schedule:
            raise ValueError(f"Unknown dataset: {dataset}")
        return schedule
