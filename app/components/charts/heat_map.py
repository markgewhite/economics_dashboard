"""Regional heat map showing house price changes across UK regions."""

import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from app.design_tokens import Colors, Typography
from data.models.housing import RegionalHousingData, Region


def render_regional_heat_map(housing_data: RegionalHousingData) -> None:
    """
    Render heat map showing annual house price changes by region.

    Displays a bar chart with regions colored by their annual price change.
    Positive changes are green, negative are red.

    Args:
        housing_data: RegionalHousingData containing all regions
    """
    st.subheader("Regional House Price Changes")

    # Get heat map data
    heat_map_data = housing_data.get_heat_map_data()

    if not heat_map_data:
        st.info("No regional data available.")
        return

    # Sort by annual change
    heat_map_data.sort(key=lambda x: x["annual_change"], reverse=True)

    # Prepare data for bar chart
    regions = [d["region_name"] for d in heat_map_data]
    changes = [d["annual_change"] for d in heat_map_data]
    prices = [d["average_price"] for d in heat_map_data]

    # Create colors based on positive/negative values
    colors = [
        Colors.POSITIVE if c >= 0 else Colors.NEGATIVE
        for c in changes
    ]

    # Create horizontal bar chart
    fig = go.Figure()

    fig.add_trace(
        go.Bar(
            y=regions,
            x=changes,
            orientation="h",
            marker_color=colors,
            text=[f"{c:+.1f}%" for c in changes],
            textposition="outside",
            hovertemplate=(
                "<b>%{y}</b><br>"
                "Annual Change: %{x:+.1f}%<br>"
                "<extra></extra>"
            ),
            customdata=prices,
        )
    )

    # Update layout
    fig.update_layout(
        font_family=Typography.FONT_FAMILY,
        font_color=Colors.TEXT_PRIMARY,
        paper_bgcolor=Colors.BG_CARD,
        plot_bgcolor=Colors.BG_CARD,
        margin=dict(l=150, r=60, t=20, b=40),
        height=400,
        showlegend=False,
        xaxis=dict(
            title="Annual Price Change (%)",
            showgrid=True,
            gridwidth=1,
            gridcolor=Colors.CHART_1 + "20",
            zeroline=True,
            zerolinewidth=2,
            zerolinecolor=Colors.TEXT_MUTED,
        ),
        yaxis=dict(
            showgrid=False,
            categoryorder="total ascending",
        ),
    )

    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    # Show summary stats
    col1, col2, col3 = st.columns(3)

    positive_regions = sum(1 for c in changes if c > 0)
    negative_regions = sum(1 for c in changes if c < 0)
    avg_change = sum(changes) / len(changes) if changes else 0

    with col1:
        st.metric("Regions Rising", positive_regions)
    with col2:
        st.metric("Regions Falling", negative_regions)
    with col3:
        st.metric("Avg Change", f"{avg_change:+.1f}%")
