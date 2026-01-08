"""Housing composition panel showing property type breakdown."""

import streamlit as st

from app.design_tokens import Colors
from app.components.charts.composition import render_property_type_breakdown
from data.models.housing import RegionalHousingData, Region


def render_housing_panel(housing_data: RegionalHousingData, region: str) -> None:
    """
    Render housing composition panel with property type breakdown.

    Shows average prices by property type (detached, semi-detached,
    terraced, flat) for the selected region.

    Args:
        housing_data: RegionalHousingData containing all regions
        region: Selected region slug
    """
    st.markdown(
        '<div class="panel"><div class="panel-title">Housing Composition</div>',
        unsafe_allow_html=True,
    )

    # Get region data
    try:
        region_enum = Region.from_string(region)
        region_ts = housing_data.get(region_enum)
    except ValueError:
        st.info("Select a region to view property breakdown.")
        st.markdown('</div>', unsafe_allow_html=True)
        return

    if not region_ts or not region_ts.data_points:
        st.info(f"No data available for {region_enum.display_name}.")
        st.markdown('</div>', unsafe_allow_html=True)
        return

    # Get latest data point with property type prices
    latest = region_ts.data_points[-1]

    # Create tabs for different views
    tab1, tab2 = st.tabs(["Price Breakdown", "Details"])

    with tab1:
        render_property_type_breakdown(
            detached=latest.price_detached,
            semi_detached=latest.price_semi_detached,
            terraced=latest.price_terraced,
            flat=latest.price_flat,
        )

    with tab2:
        _render_property_details(latest, region_enum)

    st.markdown('</div>', unsafe_allow_html=True)


def _render_property_details(data_point, region: Region) -> None:
    """Render detailed property type statistics."""
    st.markdown(f"**{region.display_name}** - {data_point.ref_month.strftime('%B %Y')}")

    # Show individual prices in a clean format
    price_data = [
        ("Detached", data_point.price_detached),
        ("Semi-Detached", data_point.price_semi_detached),
        ("Terraced", data_point.price_terraced),
        ("Flat/Maisonette", data_point.price_flat),
    ]

    for label, price in price_data:
        if price and price > 0:
            col1, col2 = st.columns([2, 1])
            with col1:
                st.write(label)
            with col2:
                st.write(f"£{price:,.0f}")
        else:
            col1, col2 = st.columns([2, 1])
            with col1:
                st.write(label)
            with col2:
                st.write("--")

    st.markdown("---")

    # Show overall metrics
    st.markdown("**Overall Metrics**")
    col1, col2 = st.columns(2)

    with col1:
        st.metric(
            "Average Price",
            f"£{data_point.average_price:,.0f}",
        )

    with col2:
        st.metric(
            "Annual Change",
            f"{data_point.annual_change_pct:+.1f}%",
        )

    # Show index
    st.caption(f"House Price Index: {data_point.house_price_index:.1f}")
