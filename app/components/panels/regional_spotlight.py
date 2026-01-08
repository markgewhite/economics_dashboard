"""Regional spotlight panel for comparing regions."""

import streamlit as st
import plotly.graph_objects as go

from app.design_tokens import Colors, Typography
from data.models.housing import RegionalHousingData, Region


def render_regional_panel(housing_data: RegionalHousingData) -> None:
    """
    Render regional spotlight panel with comparison features.

    Allows selection of regions to compare key metrics.

    Args:
        housing_data: RegionalHousingData containing all regions
    """
    st.markdown(
        '<div class="panel"><div class="panel-title">Regional Spotlight</div>',
        unsafe_allow_html=True,
    )

    if not housing_data or not housing_data.regions:
        st.info("No regional data available.")
        st.markdown('</div>', unsafe_allow_html=True)
        return

    # Region selector for comparison
    available_regions = list(housing_data.regions.keys())
    region_labels = {r: r.display_name for r in available_regions}

    # Default to comparing UK, England, and London if available
    default_regions = []
    for r in [Region.UNITED_KINGDOM, Region.ENGLAND, Region.LONDON]:
        if r in available_regions:
            default_regions.append(r)

    selected_regions = st.multiselect(
        "Compare Regions",
        options=available_regions,
        default=default_regions[:3],
        format_func=lambda x: region_labels[x],
        max_selections=5,
        key="regional_spotlight_select",
    )

    if not selected_regions:
        st.info("Select regions to compare.")
        st.markdown('</div>', unsafe_allow_html=True)
        return

    # Create tabs for different comparisons
    tab1, tab2 = st.tabs(["Price Comparison", "Change Rates"])

    with tab1:
        _render_price_comparison(housing_data, selected_regions)

    with tab2:
        _render_change_comparison(housing_data, selected_regions)

    st.markdown('</div>', unsafe_allow_html=True)


def _render_price_comparison(
    housing_data: RegionalHousingData,
    regions: list[Region],
) -> None:
    """Render price comparison bar chart."""
    labels = []
    prices = []
    colors = []

    color_sequence = [Colors.CHART_1, Colors.CHART_2, Colors.CHART_3, Colors.CHART_4, Colors.CHART_5]

    for i, region in enumerate(regions):
        ts = housing_data.get(region)
        if ts and ts.metrics:
            labels.append(region.display_name)
            prices.append(ts.metrics.current_average_price)
            colors.append(color_sequence[i % len(color_sequence)])

    if not labels:
        st.info("No price data available for selected regions.")
        return

    fig = go.Figure()

    fig.add_trace(
        go.Bar(
            x=labels,
            y=prices,
            marker_color=colors,
            text=[f"£{p:,.0f}" for p in prices],
            textposition="outside",
            hovertemplate="<b>%{x}</b><br>£%{y:,.0f}<extra></extra>",
        )
    )

    fig.update_layout(
        font_family=Typography.FONT_FAMILY,
        font_color=Colors.TEXT_PRIMARY,
        paper_bgcolor=Colors.BG_CARD,
        plot_bgcolor=Colors.BG_CARD,
        margin=dict(l=20, r=20, t=20, b=40),
        height=250,
        showlegend=False,
        yaxis=dict(
            showgrid=True,
            gridwidth=1,
            gridcolor=Colors.CHART_1 + "20",
            tickformat=",.0f",
            tickprefix="£",
        ),
        xaxis=dict(showgrid=False),
    )

    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})


def _render_change_comparison(
    housing_data: RegionalHousingData,
    regions: list[Region],
) -> None:
    """Render annual change comparison."""
    labels = []
    changes = []
    colors = []

    for region in regions:
        ts = housing_data.get(region)
        if ts and ts.metrics:
            labels.append(region.display_name)
            change = ts.metrics.price_change_yoy
            changes.append(change)
            colors.append(Colors.POSITIVE if change >= 0 else Colors.NEGATIVE)

    if not labels:
        st.info("No change data available for selected regions.")
        return

    fig = go.Figure()

    fig.add_trace(
        go.Bar(
            x=labels,
            y=changes,
            marker_color=colors,
            text=[f"{c:+.1f}%" for c in changes],
            textposition="outside",
            hovertemplate="<b>%{x}</b><br>%{y:+.1f}%<extra></extra>",
        )
    )

    fig.update_layout(
        font_family=Typography.FONT_FAMILY,
        font_color=Colors.TEXT_PRIMARY,
        paper_bgcolor=Colors.BG_CARD,
        plot_bgcolor=Colors.BG_CARD,
        margin=dict(l=20, r=20, t=20, b=40),
        height=250,
        showlegend=False,
        yaxis=dict(
            showgrid=True,
            gridwidth=1,
            gridcolor=Colors.CHART_1 + "20",
            tickformat="+.1f",
            ticksuffix="%",
            zeroline=True,
            zerolinewidth=2,
            zerolinecolor=Colors.TEXT_MUTED,
        ),
        xaxis=dict(showgrid=False),
    )

    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    # Show ranking
    st.markdown("**Regional Ranking (by annual change)**")
    sorted_data = sorted(zip(labels, changes), key=lambda x: x[1], reverse=True)
    for i, (label, change) in enumerate(sorted_data, 1):
        icon = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
        color = "green" if change >= 0 else "red"
        st.markdown(
            f"{icon} **{label}**: <span style='color: {color};'>{change:+.1f}%</span>",
            unsafe_allow_html=True,
        )
