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
from app.components.filters import render_filters, get_date_range


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

    # Header
    _render_header(state)

    # Check for refresh trigger
    force_refresh = state.should_force_refresh()

    # Load data
    with st.spinner("Loading dashboard data..."):
        data = data_service.get_dashboard_data(force_refresh=force_refresh)

    # Clear refresh flag
    state.clear_refresh_flag()

    # Show warnings if any
    if data.has_errors:
        for error in data.errors:
            st.warning(error)

    if data.warnings:
        with st.expander("Data Warnings", expanded=False):
            for warning in data.warnings:
                st.info(warning)

    # Filters
    st.markdown("---")
    time_range, region = render_filters(state)

    # Get date range for filtering
    start_date, end_date = get_date_range(time_range)

    # Data status section
    st.markdown("---")
    _render_data_status(data)

    # Main content placeholder (components added in Phase 7)
    st.markdown("---")
    _render_main_content_placeholder(data, time_range, region)

    # Deep dive panels placeholder (components added in Phase 8)
    st.markdown("---")
    _render_panels_placeholder(data)

    # Footer
    _render_footer(data.metadata)


def _load_styles():
    """Load custom CSS from assets."""
    css_path = Path(__file__).parent.parent / "assets" / "styles.css"
    if css_path.exists():
        st.markdown(
            f"<style>{css_path.read_text()}</style>",
            unsafe_allow_html=True,
        )


def _render_header(state: StateManager):
    """Render dashboard header with title and refresh button."""
    col1, col2 = st.columns([6, 1])

    with col1:
        st.title("UK Housing & Economic Dashboard")
        st.caption("Visualizing monetary policy, housing markets, and economic indicators")

    with col2:
        if st.button("Refresh Data", type="secondary", use_container_width=True):
            state.trigger_refresh()
            st.rerun()


def _render_data_status(data):
    """Render data status summary."""
    st.subheader("Data Status")

    col1, col2, col3 = st.columns(3)

    with col1:
        _render_dataset_status(
            "Monetary Data",
            data.monetary is not None,
            data.metadata.get("monetary"),
        )

    with col2:
        _render_dataset_status(
            "Housing Data",
            data.housing is not None,
            data.metadata.get("housing"),
        )

    with col3:
        _render_dataset_status(
            "Economic Data",
            data.economic is not None,
            data.metadata.get("economic"),
        )


def _render_dataset_status(name: str, has_data: bool, metadata):
    """Render status for a single dataset."""
    if has_data:
        st.success(f"{name}: Loaded")
        if metadata:
            st.caption(f"Last updated: {metadata.age_description}")
    else:
        st.error(f"{name}: Not available")


def _render_main_content_placeholder(data, time_range: str, region: str):
    """Placeholder for main content area (Phase 7)."""
    st.subheader("Dashboard Overview")

    # Hero metrics placeholder
    st.markdown("#### Key Metrics")
    metric_cols = st.columns(4)

    if data.monetary and data.monetary.metrics:
        metrics = data.monetary.metrics
        with metric_cols[0]:
            st.metric(
                "Bank Rate",
                f"{metrics.current_bank_rate:.2f}%",
                f"{metrics.bank_rate_change_yoy:+.2f}% YoY",
            )
        with metric_cols[1]:
            st.metric(
                "2-Year Fixed",
                f"{metrics.current_mortgage_2yr:.2f}%",
                f"{metrics.mortgage_2yr_change_yoy:+.2f}% YoY",
            )
        with metric_cols[2]:
            st.metric(
                "5-Year Fixed",
                f"{metrics.current_mortgage_5yr:.2f}%",
                f"{metrics.mortgage_5yr_change_yoy:+.2f}% YoY",
            )

    if data.housing:
        from data.models.housing import Region as RegionEnum
        try:
            selected_region = RegionEnum.from_string(region)
            region_data = data.housing.get(selected_region)
            if region_data and region_data.metrics:
                with metric_cols[3]:
                    st.metric(
                        f"Avg Price ({selected_region.display_name})",
                        f"£{region_data.metrics.current_average_price:,.0f}",
                        f"{region_data.metrics.price_change_yoy:+.1f}% YoY",
                    )
        except ValueError:
            pass

    # Charts placeholder
    st.markdown("#### Charts")
    st.info(
        "Chart components (Rates vs Prices, Regional Heat Map, Rate Trends, Transactions) "
        "will be implemented in Phase 7."
    )

    # Show data summary
    left_col, right_col = st.columns(2)

    with left_col:
        st.markdown("##### Monetary Data Summary")
        if data.monetary:
            st.write(f"- Data points: {len(data.monetary)}")
            if data.monetary.earliest_date and data.monetary.latest_date:
                st.write(f"- Date range: {data.monetary.earliest_date} to {data.monetary.latest_date}")
        else:
            st.write("No monetary data available")

    with right_col:
        st.markdown("##### Housing Data Summary")
        if data.housing:
            st.write(f"- Regions loaded: {len(data.housing)}")
            regions_list = [r.display_name for r in data.housing.regions.keys()]
            st.write(f"- Regions: {', '.join(regions_list[:5])}...")
        else:
            st.write("No housing data available")


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


def _render_footer(metadata: dict):
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
