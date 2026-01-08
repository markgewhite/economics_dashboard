"""Filter controls for time range and region selection."""

from datetime import date
from dateutil.relativedelta import relativedelta
import streamlit as st

from app.state import StateManager
from data.models.housing import Region


def render_filters(state: StateManager) -> tuple[str, str]:
    """
    Render filter controls for time range and region selection.

    Args:
        state: StateManager instance for session state

    Returns:
        Tuple of (time_range, region) current selections
    """
    col1, col2, col3 = st.columns([2, 2, 6])

    with col1:
        time_range = st.selectbox(
            "Time Range",
            options=list(state.TIME_RANGE_OPTIONS.keys()),
            format_func=lambda x: state.TIME_RANGE_OPTIONS[x],
            index=list(state.TIME_RANGE_OPTIONS.keys()).index(state.time_range),
            key="time_range_select",
        )
        state.time_range = time_range

    with col2:
        # Build region options
        region_options = _get_region_options()
        region_labels = {r.value: r.display_name for r in Region}

        region = st.selectbox(
            "Region",
            options=region_options,
            format_func=lambda x: region_labels.get(x, x),
            index=region_options.index(state.region) if state.region in region_options else 0,
            key="region_select",
        )
        state.region = region

    return time_range, region


def _get_region_options() -> list[str]:
    """Get ordered list of region values for dropdown."""
    options = []

    # Add nations first
    options.append("--- Nations ---")
    for region in Region.nations():
        options.append(region.value)

    # Add English regions
    options.append("--- English Regions ---")
    for region in Region.english_regions():
        options.append(region.value)

    # Filter out separator labels (they won't be selectable)
    return [r for r in options if not r.startswith("---")]


def get_date_range(time_range: str) -> tuple[date, date]:
    """
    Convert time range code to start/end dates.

    Args:
        time_range: Time range code (6M, 1Y, 2Y, 5Y, MAX)

    Returns:
        Tuple of (start_date, end_date)
    """
    end_date = date.today()

    if time_range == "6M":
        start_date = end_date - relativedelta(months=6)
    elif time_range == "1Y":
        start_date = end_date - relativedelta(years=1)
    elif time_range == "2Y":
        start_date = end_date - relativedelta(years=2)
    elif time_range == "5Y":
        start_date = end_date - relativedelta(years=5)
    else:  # MAX
        start_date = date(2015, 1, 1)  # Reasonable default start

    return start_date, end_date
