"""Data models for cache metadata."""

from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum
from typing import Any
import json


class RefreshReason(Enum):
    """Reason codes for cache refresh decisions."""

    # Refresh was triggered
    INITIAL_FETCH = "initial_fetch"
    FORCED_REFRESH = "forced_refresh"
    DAILY_UPDATE_EXPECTED = "daily_update_expected"
    MONTHLY_UPDATE_EXPECTED = "monthly_update_expected"

    # Cache was used (no refresh)
    ALREADY_CURRENT = "already_current"
    CACHED_WEEKEND = "cached_weekend_no_update"
    CACHED_BEFORE_CHECK_TIME = "cached_before_check_time"
    CACHED_BEFORE_RELEASE_DAY = "cached_before_release_day"

    # Error states
    FETCH_FAILED_USING_STALE = "fetch_failed_using_stale"


@dataclass
class CacheMetadata:
    """Metadata for a cached dataset."""

    dataset: str  # "monetary", "housing", "economic"
    last_fetch: datetime
    next_expected: datetime
    data_date: str  # Latest data point date (ISO format: YYYY-MM-DD)
    refresh_reason: RefreshReason
    record_count: int
    is_stale: bool = False  # True if fetch failed and using old cache

    def to_dict(self) -> dict[str, Any]:
        """Convert to JSON-serializable dict."""
        data = asdict(self)
        data["last_fetch"] = self.last_fetch.isoformat()
        data["next_expected"] = self.next_expected.isoformat()
        data["refresh_reason"] = self.refresh_reason.value
        return data

    def to_json(self) -> str:
        """Serialize to JSON string."""
        return json.dumps(self.to_dict(), indent=2)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "CacheMetadata":
        """Create from dict (e.g., from JSON)."""
        return cls(
            dataset=data["dataset"],
            last_fetch=datetime.fromisoformat(data["last_fetch"]),
            next_expected=datetime.fromisoformat(data["next_expected"]),
            data_date=data["data_date"],
            refresh_reason=RefreshReason(data["refresh_reason"]),
            record_count=data["record_count"],
            is_stale=data.get("is_stale", False),
        )

    @classmethod
    def from_json(cls, json_str: str) -> "CacheMetadata":
        """Deserialize from JSON string."""
        data = json.loads(json_str)
        return cls.from_dict(data)

    def _get_now(self) -> datetime:
        """Get current time, matching timezone of stored datetimes."""
        if self.last_fetch.tzinfo is not None:
            from zoneinfo import ZoneInfo
            return datetime.now(self.last_fetch.tzinfo)
        return datetime.now()

    @property
    def age_seconds(self) -> float:
        """Return age of cache in seconds."""
        return (self._get_now() - self.last_fetch).total_seconds()

    @property
    def age_description(self) -> str:
        """Human-readable description of data age."""
        age = self._get_now() - self.last_fetch
        days = age.days
        hours = age.seconds // 3600
        minutes = (age.seconds % 3600) // 60

        if days > 0:
            return f"Updated {days} day{'s' if days != 1 else ''} ago"
        if hours > 0:
            return f"Updated {hours} hour{'s' if hours != 1 else ''} ago"
        if minutes > 0:
            return f"Updated {minutes} minute{'s' if minutes != 1 else ''} ago"
        return "Updated just now"

    @property
    def next_update_description(self) -> str:
        """Human-readable description of next expected update."""
        now = self._get_now()
        # Handle timezone mismatch by comparing naive versions if needed
        next_exp = self.next_expected
        if next_exp.tzinfo is not None and now.tzinfo is None:
            next_exp = next_exp.replace(tzinfo=None)
        elif next_exp.tzinfo is None and now.tzinfo is not None:
            now = now.replace(tzinfo=None)
        if next_exp <= now:
            return "Update available"

        delta = next_exp - now
        days = delta.days
        hours = delta.seconds // 3600

        if days > 0:
            return f"Next update in {days} day{'s' if days != 1 else ''}"
        if hours > 0:
            return f"Next update in {hours} hour{'s' if hours != 1 else ''}"
        return "Next update soon"
