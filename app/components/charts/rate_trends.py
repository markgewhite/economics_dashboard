"""Rate trends chart showing mortgage rate movements over time."""

import plotly.graph_objects as go
import streamlit as st

from app.design_tokens import Colors, Typography
from app.components.filters import get_date_range
from data.models.monetary import MonetaryTimeSeries


def render_rate_trends(monetary_data: MonetaryTimeSeries, time_range: str) -> None:
    """
    Render multi-line chart showing mortgage rate trends.

    Displays Bank Rate, 2-Year Fixed, and 5-Year Fixed mortgage rates
    over the selected time period.

    Args:
        monetary_data: MonetaryTimeSeries containing rate data
        time_range: Time range code for filtering
    """
    st.subheader("Interest Rate Trends")

    if not monetary_data or not monetary_data.data_points:
        st.info("No monetary data available.")
        return

    # Filter by time range
    start_date, end_date = get_date_range(time_range)
    filtered = monetary_data.filter_by_range(start_date, end_date)

    if not filtered.data_points:
        st.info("No data available for selected time range.")
        return

    # Extract data
    dates = [dp.observation_date for dp in filtered.data_points]
    bank_rates = [dp.bank_rate for dp in filtered.data_points]
    mortgage_2yr = [dp.mortgage_2yr for dp in filtered.data_points]
    mortgage_5yr = [dp.mortgage_5yr for dp in filtered.data_points]

    # Create figure
    fig = go.Figure()

    # Add Bank Rate
    fig.add_trace(
        go.Scatter(
            x=dates,
            y=bank_rates,
            name="Bank Rate",
            line=dict(color=Colors.CHART_1, width=3),
            hovertemplate="Bank Rate: %{y:.2f}%<extra></extra>",
        )
    )

    # Add 2-Year Fixed
    fig.add_trace(
        go.Scatter(
            x=dates,
            y=mortgage_2yr,
            name="2-Year Fixed",
            line=dict(color=Colors.CHART_2, width=2),
            hovertemplate="2-Year Fixed: %{y:.2f}%<extra></extra>",
        )
    )

    # Add 5-Year Fixed
    fig.add_trace(
        go.Scatter(
            x=dates,
            y=mortgage_5yr,
            name="5-Year Fixed",
            line=dict(color=Colors.CHART_3, width=2),
            hovertemplate="5-Year Fixed: %{y:.2f}%<extra></extra>",
        )
    )

    # Update layout
    fig.update_layout(
        font_family=Typography.FONT_FAMILY,
        font_color=Colors.TEXT_PRIMARY,
        paper_bgcolor=Colors.BG_CARD,
        plot_bgcolor=Colors.BG_CARD,
        margin=dict(l=50, r=20, t=20, b=40),
        height=300,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="left",
            x=0,
        ),
        hovermode="x unified",
        xaxis=dict(
            showgrid=True,
            gridwidth=1,
            gridcolor=Colors.CHART_1 + "20",
            tickformat="%b %Y",
        ),
        yaxis=dict(
            title="Rate (%)",
            showgrid=True,
            gridwidth=1,
            gridcolor=Colors.CHART_1 + "20",
            ticksuffix="%",
        ),
    )

    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    # Show current rates summary
    if filtered.data_points:
        latest = filtered.data_points[-1]
        col1, col2, col3 = st.columns(3)

        with col1:
            if latest.bank_rate is not None:
                st.metric("Current Bank Rate", f"{latest.bank_rate:.2f}%")

        with col2:
            if latest.mortgage_2yr is not None:
                st.metric("Current 2-Year", f"{latest.mortgage_2yr:.2f}%")

        with col3:
            if latest.mortgage_5yr is not None:
                st.metric("Current 5-Year", f"{latest.mortgage_5yr:.2f}%")
