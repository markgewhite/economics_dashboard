"""Dual-axis chart showing interest rates vs house prices."""

from datetime import date

import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st

from app.design_tokens import Colors, Typography, ChartConfig
from app.services.data_service import DashboardData
from app.components.filters import get_date_range
from data.models.housing import Region


def render_rates_vs_prices(
    data: DashboardData,
    time_range: str,
    region: str = "united-kingdom",
) -> None:
    """
    Render dual-axis chart comparing interest rates and house prices.

    Left Y-axis: Interest rates (Bank Rate, Mortgage Rates)
    Right Y-axis: Average house price

    Args:
        data: DashboardData containing monetary and housing data
        time_range: Time range code for filtering
        region: Region slug for housing data
    """
    st.subheader("Interest Rates vs House Prices")

    if not data.monetary or not data.housing:
        st.info("Insufficient data to display this chart.")
        return

    # Get date range
    start_date, end_date = get_date_range(time_range)

    # Filter monetary data
    monetary_filtered = data.monetary.filter_by_range(start_date, end_date)

    # Get housing data for region
    try:
        region_enum = Region.from_string(region)
        housing_ts = data.housing.get(region_enum)
        if housing_ts:
            housing_filtered = housing_ts.filter_by_range(start_date, end_date)
        else:
            housing_filtered = None
    except ValueError:
        housing_filtered = None

    if not monetary_filtered.data_points:
        st.info("No monetary data available for selected time range.")
        return

    # Create figure with secondary y-axis
    fig = make_subplots(specs=[[{"secondary_y": True}]])

    # Add Bank Rate trace (dark color from Figma design)
    bank_rate_dates = [dp.observation_date for dp in monetary_filtered.data_points]
    bank_rates = [dp.bank_rate for dp in monetary_filtered.data_points]

    fig.add_trace(
        go.Scatter(
            x=bank_rate_dates,
            y=bank_rates,
            name="Bank Rate",
            line=dict(color=Colors.BANK_RATE, width=2),
            hovertemplate="Bank Rate: %{y:.2f}%<extra></extra>",
        ),
        secondary_y=False,
    )

    # Add 2-Year Mortgage Rate trace (red from Figma design)
    mortgage_2yr = [dp.mortgage_2yr for dp in monetary_filtered.data_points]
    fig.add_trace(
        go.Scatter(
            x=bank_rate_dates,
            y=mortgage_2yr,
            name="2yr Mortgage Rate",
            line=dict(color=Colors.MORTGAGE_2YR, width=2),
            hovertemplate="2yr Mortgage Rate: %{y:.2f}%<extra></extra>",
        ),
        secondary_y=False,
    )

    # Add house prices on secondary axis (blue from Figma design)
    if housing_filtered and housing_filtered.data_points:
        housing_dates = [dp.ref_month for dp in housing_filtered.data_points]
        housing_prices = [dp.average_price for dp in housing_filtered.data_points]

        fig.add_trace(
            go.Scatter(
                x=housing_dates,
                y=housing_prices,
                name="House Price Index",
                line=dict(color=Colors.HOUSE_PRICE_INDEX, width=2),
                hovertemplate="Avg Price: £%{y:,.0f}<extra></extra>",
            ),
            secondary_y=True,
        )

    # Update layout
    fig.update_layout(
        font_family=Typography.FONT_FAMILY,
        font_color=Colors.TEXT_PRIMARY,
        paper_bgcolor=Colors.BG_CARD,
        plot_bgcolor=Colors.BG_CARD,
        margin=dict(l=60, r=60, t=20, b=40),
        height=400,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="left",
            x=0,
        ),
        hovermode="x unified",
    )

    # Update axes with Figma design grid styling
    fig.update_xaxes(
        showgrid=True,
        gridwidth=1,
        gridcolor="#E2E8F0",
        tickformat="%b %Y",
    )

    fig.update_yaxes(
        title_text="Interest Rate (%)",
        showgrid=True,
        gridwidth=1,
        gridcolor="#E2E8F0",
        secondary_y=False,
    )

    fig.update_yaxes(
        title_text="Average House Price (£)",
        showgrid=False,
        tickformat=",.0f",
        tickprefix="£",
        secondary_y=True,
    )

    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
