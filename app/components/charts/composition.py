"""Composition donut chart for property type breakdowns."""

from typing import Optional

import plotly.graph_objects as go
import streamlit as st

from app.design_tokens import Colors, Typography, ChartConfig


def render_composition_donut(
    labels: list[str],
    values: list[float],
    title: Optional[str] = None,
    center_label: Optional[str] = None,
    center_value: Optional[str] = None,
    height: int = 350,
) -> None:
    """
    Render a donut chart showing composition/breakdown.

    Args:
        labels: Category labels
        values: Category values (will be normalized to percentages)
        title: Optional chart title
        center_label: Label to show in center of donut
        center_value: Value to show in center of donut
        height: Chart height in pixels
    """
    if not labels or not values:
        st.info("No composition data available.")
        return

    # Define colors for property types
    color_map = {
        "Detached": Colors.CHART_1,
        "Semi-Detached": Colors.CHART_2,
        "Terraced": Colors.CHART_3,
        "Flat/Maisonette": Colors.CHART_4,
        "Other": Colors.CHART_5,
    }

    # Get colors, defaulting to chart sequence
    colors = []
    for i, label in enumerate(labels):
        if label in color_map:
            colors.append(color_map[label])
        else:
            colors.append(ChartConfig.COLOR_SEQUENCE[i % len(ChartConfig.COLOR_SEQUENCE)])

    # Use design token colors if no specific mapping
    if not colors:
        colors = [Colors.CHART_1, Colors.CHART_2, Colors.CHART_3, Colors.CHART_4, Colors.CHART_5]

    fig = go.Figure()

    fig.add_trace(
        go.Pie(
            labels=labels,
            values=values,
            hole=0.6,
            marker=dict(
                colors=colors[:len(labels)],
                line=dict(color=Colors.BG_CARD, width=2),
            ),
            textinfo="percent",
            textposition="outside",
            textfont=dict(size=12, color=Colors.TEXT_PRIMARY),
            hovertemplate="<b>%{label}</b><br>%{value:,.0f}<br>%{percent}<extra></extra>",
        )
    )

    # Add center annotation if provided
    annotations = []
    if center_label and center_value:
        annotations = [
            dict(
                text=f"<b>{center_value}</b><br><span style='font-size: 12px;'>{center_label}</span>",
                x=0.5,
                y=0.5,
                font=dict(size=16, color=Colors.TEXT_PRIMARY),
                showarrow=False,
            )
        ]

    fig.update_layout(
        title=dict(text=title, font=dict(size=16, color=Colors.TEXT_PRIMARY)) if title else None,
        font_family=Typography.FONT_FAMILY,
        paper_bgcolor=Colors.BG_CARD,
        plot_bgcolor=Colors.BG_CARD,
        margin=dict(l=20, r=20, t=40 if title else 20, b=20),
        height=height,
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.2,
            xanchor="center",
            x=0.5,
            font=dict(size=11),
        ),
        annotations=annotations,
    )

    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})


def render_property_type_breakdown(
    detached: Optional[float],
    semi_detached: Optional[float],
    terraced: Optional[float],
    flat: Optional[float],
) -> None:
    """
    Render property type price breakdown as donut chart.

    Args:
        detached: Average detached house price
        semi_detached: Average semi-detached house price
        terraced: Average terraced house price
        flat: Average flat/maisonette price
    """
    labels = []
    values = []

    if detached and detached > 0:
        labels.append("Detached")
        values.append(detached)

    if semi_detached and semi_detached > 0:
        labels.append("Semi-Detached")
        values.append(semi_detached)

    if terraced and terraced > 0:
        labels.append("Terraced")
        values.append(terraced)

    if flat and flat > 0:
        labels.append("Flat/Maisonette")
        values.append(flat)

    if not labels:
        st.info("Property type breakdown not available.")
        return

    # Calculate average for center
    avg_price = sum(values) / len(values)

    render_composition_donut(
        labels=labels,
        values=values,
        title="Average Prices by Property Type",
        center_label="Avg Price",
        center_value=f"£{avg_price:,.0f}",
    )
