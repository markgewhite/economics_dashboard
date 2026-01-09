"""
UK Housing & Economic Dashboard - Main Entry Point

Streamlit dashboard visualizing relationships between UK monetary policy,
housing markets, and economic indicators.
"""

from pathlib import Path

import streamlit as st

from app.config import Config
from app.state import StateManager
from app.services.data_service import DataService
from app.components.filters import render_filters
from app.components.header import render_header
from app.components.hero_metrics import render_hero_metrics
from app.components.charts import (
    render_rates_vs_prices,
    render_regional_heat_map,
    render_rate_trends,
    render_transactions,
)
from app.components.panels import (
    render_housing_panel,
    render_economic_panel,
    render_regional_panel,
    render_footer,
)


def main():
    """Main dashboard entry point."""

    # Page configuration
    st.set_page_config(
        page_title="UK Housing & Economic Dashboard",
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="collapsed",
    )

    # Load custom CSS
    _load_styles()

    # Initialize configuration and state
    config = Config.from_env()
    state = StateManager(st.session_state)

    # Initialize data service
    data_service = DataService(cache_dir=config.cache_dir)

    # Check for refresh trigger
    force_refresh = state.should_force_refresh()

    # Load data
    with st.spinner("Loading dashboard data..."):
        data = data_service.get_dashboard_data(force_refresh=force_refresh)

    # Clear refresh flag
    state.clear_refresh_flag()

    # Header with refresh controls
    render_header(data.metadata, on_refresh=state.trigger_refresh)

    # Show warnings if any
    if data.has_errors:
        for error in data.errors:
            st.warning(error)

    if data.warnings:
        with st.expander("Data Warnings", expanded=False):
            for warning in data.warnings:
                st.info(warning)

    # Hero metrics
    if data.monetary:
        render_hero_metrics(data, selected_region=state.region)

    # Filters
    st.markdown("---")
    time_range, region = render_filters(state)

    # Main content area - Row 1: Rates vs Prices charts
    st.markdown("---")
    row1_left, row1_right = st.columns([3, 2])

    with row1_left:
        # Dual-axis chart: rates vs prices
        if data.monetary and data.housing:
            render_rates_vs_prices(data, time_range, region)

    with row1_right:
        # Rate trends chart
        if data.monetary:
            render_rate_trends(data.monetary, time_range)

    # Divider between chart rows (full-width because we're outside columns)
    st.markdown("---")

    # Row 2: Regional/Transaction charts
    row2_left, row2_right = st.columns([3, 2])

    with row2_left:
        # Regional heat map
        if data.housing:
            render_regional_heat_map(data.housing)

    with row2_right:
        # Transactions chart
        if data.housing:
            render_transactions(data.housing, region, time_range)

    # Deep dive panels
    st.markdown("---")
    st.subheader("Deep Dive")

    panel_cols = st.columns(3)

    with panel_cols[0]:
        if data.housing:
            render_housing_panel(data.housing, region)

    with panel_cols[1]:
        if data.economic:
            render_economic_panel(data.economic)

    with panel_cols[2]:
        if data.housing:
            render_regional_panel(data.housing)

    # Footer
    render_footer(data.metadata)


def _load_styles():
    """Load custom CSS from assets."""
    css_path = Path(__file__).parent.parent / "assets" / "styles.css"
    if css_path.exists():
        st.markdown(
            f"<style>{css_path.read_text()}</style>",
            unsafe_allow_html=True,
        )


if __name__ == "__main__":
    main()
