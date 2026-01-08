"""Session state management for Streamlit dashboard."""

from typing import Optional
from streamlit.runtime.state import SessionStateProxy


class StateManager:
    """
    Manages Streamlit session state for dashboard.

    Provides a clean interface over st.session_state with
    type hints and default values.
    """

    DEFAULT_TIME_RANGE = "1Y"
    DEFAULT_REGION = "united-kingdom"

    # Available time range options
    TIME_RANGE_OPTIONS = {
        "6M": "6 Months",
        "1Y": "1 Year",
        "2Y": "2 Years",
        "5Y": "5 Years",
        "MAX": "All Time",
    }

    def __init__(self, session_state: SessionStateProxy):
        self._state = session_state
        self._initialize_defaults()

    def _initialize_defaults(self):
        """Set default values if not already in session state."""
        defaults = {
            "time_range": self.DEFAULT_TIME_RANGE,
            "region": self.DEFAULT_REGION,
            "force_refresh": False,
        }

        for key, value in defaults.items():
            if key not in self._state:
                self._state[key] = value

    @property
    def time_range(self) -> str:
        """Current time range selection."""
        return self._state.time_range

    @time_range.setter
    def time_range(self, value: str):
        self._state.time_range = value

    @property
    def region(self) -> str:
        """Current region selection."""
        return self._state.region

    @region.setter
    def region(self, value: str):
        self._state.region = value

    def trigger_refresh(self):
        """Flag that manual refresh was requested."""
        self._state.force_refresh = True

    def should_force_refresh(self) -> bool:
        """Check if manual refresh was requested."""
        return self._state.get("force_refresh", False)

    def clear_refresh_flag(self):
        """Clear the refresh flag after processing."""
        self._state.force_refresh = False
