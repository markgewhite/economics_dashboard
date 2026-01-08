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

    # Main content area - two columns
    st.markdown("---")
    left_col, right_col = st.columns([3, 2])

    with left_col:
        # Dual-axis chart: rates vs prices
        if data.monetary and data.housing:
            render_rates_vs_prices(data, time_range, region)

        # Regional heat map
        if data.housing:
            st.markdown("---")
            render_regional_heat_map(data.housing)

    with right_col:
        # Rate trends chart
        if data.monetary:
            render_rate_trends(data.monetary, time_range)

        # Transactions chart
        if data.housing:
            st.markdown("---")
            render_transactions(data.housing, region, time_range)

    # Deep dive panels placeholder (Phase 8)
    st.markdown("---")
    _render_panels_placeholder(data)

    # Footer
    _render_footer()


def _load_styles():
    """Load custom CSS from assets."""
    css_path = Path(__file__).parent.parent / "assets" / "styles.css"
    if css_path.exists():
        st.markdown(
            f"<style>{css_path.read_text()}</style>",
            unsafe_allow_html=True,
        )


def _render_panels_placeholder(data):
    """Placeholder for deep dive panels (Phase 8)."""
    st.subheader("Deep Dive Panels")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("##### Housing Composition")
        st.info("Property type breakdown will be implemented in Phase 8.")

    with col2:
        st.markdown("##### Economic Context")
        if data.economic:
            st.write(f"- Data points: {len(data.economic)}")
            if data.economic.metrics:
                st.write(f"- Current CPI: {data.economic.metrics.current_cpi:.1f}%")
                st.write(f"- Employment Rate: {data.economic.metrics.current_employment:.1f}%")
        else:
            st.write("No economic data available")
        st.info("Full economic panel will be implemented in Phase 8.")

    with col3:
        st.markdown("##### Regional Spotlight")
        st.info("Regional comparison panel will be implemented in Phase 8.")


def _render_footer():
    """Render dashboard footer with data attribution."""
    st.markdown(
        """
        <div class="footer">
            <p>Data sources: Bank of England, HM Land Registry, Office for National Statistics</p>
            <p>UK Housing & Economic Dashboard - Portfolio Project</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
