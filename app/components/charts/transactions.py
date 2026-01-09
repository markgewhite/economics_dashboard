"""Transaction volume chart showing monthly sales volumes."""

import plotly.graph_objects as go
import streamlit as st

from app.design_tokens import Colors, Typography
from app.components.filters import get_date_range
from data.models.housing import RegionalHousingData, Region


def render_transactions(
    housing_data: RegionalHousingData,
    region: str,
    time_range: str,
) -> None:
    """
    Render bar chart showing monthly transaction volumes.

    Args:
        housing_data: RegionalHousingData containing all regions
        region: Region slug for filtering
        time_range: Time range code for filtering
    """
    st.subheader("Monthly Transactions")

    # Get region data
    try:
        region_enum = Region.from_string(region)
        region_ts = housing_data.get(region_enum)
    except ValueError:
        st.info("Invalid region selected.")
        return

    if not region_ts or not region_ts.data_points:
        st.info(f"No transaction data available for {region_enum.display_name}.")
        return

    # Filter by time range
    start_date, end_date = get_date_range(time_range)
    filtered = region_ts.filter_by_range(start_date, end_date)

    if not filtered.data_points:
        st.info("No data available for selected time range.")
        return

    # Extract data (filter out None values for sales volume)
    data_with_volume = [
        dp for dp in filtered.data_points
        if dp.sales_volume is not None
    ]

    if not data_with_volume:
        st.info(
            "Sales volume data is not yet available for recent months. "
            "This data is typically published with a 2-3 month delay."
        )
        return

    dates = [dp.ref_month for dp in data_with_volume]
    volumes = [dp.sales_volume for dp in data_with_volume]

    # Calculate average for reference line
    avg_volume = sum(volumes) / len(volumes) if volumes else 0

    # Create figure
    fig = go.Figure()

    # Add volume bars (primary blue from Figma design)
    fig.add_trace(
        go.Bar(
            x=dates,
            y=volumes,
            name="Transactions",
            marker_color=Colors.PRIMARY,
            hovertemplate="<b>%{x|%b %Y}</b><br>Transactions: %{y:,.0f}<extra></extra>",
        )
    )

    # Add average line
    fig.add_hline(
        y=avg_volume,
        line_dash="dash",
        line_color=Colors.TEXT_MUTED,
        annotation_text=f"Avg: {avg_volume:,.0f}",
        annotation_position="right",
    )

    # Update layout
    fig.update_layout(
        font_family=Typography.FONT_FAMILY,
        font_color=Colors.TEXT_PRIMARY,
        paper_bgcolor=Colors.BG_CARD,
        plot_bgcolor=Colors.BG_CARD,
        margin=dict(l=50, r=20, t=20, b=40),
        height=300,
        showlegend=False,
        xaxis=dict(
            showgrid=False,
            tickformat="%b %Y",
        ),
        yaxis=dict(
            title="Number of Transactions",
            showgrid=True,
            gridwidth=1,
            gridcolor="#E2E8F0",
            tickformat=",",
        ),
    )

    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    # Show summary stats
    col1, col2, col3 = st.columns(3)

    total_volume = sum(volumes)
    max_volume = max(volumes)
    min_volume = min(volumes)

    with col1:
        st.metric("Total Transactions", f"{total_volume:,.0f}")

    with col2:
        st.metric("Peak Month", f"{max_volume:,.0f}")

    with col3:
        st.metric("Lowest Month", f"{min_volume:,.0f}")
