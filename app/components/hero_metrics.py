"""Hero metrics component displaying key dashboard indicators."""

from typing import Optional

import streamlit as st

from app.services.data_service import DashboardData
from data.models.housing import Region


def render_hero_metrics(data: DashboardData, selected_region: str = "united-kingdom") -> None:
    """
    Render four hero metric cards showing key indicators.

    Cards:
    1. Bank Rate - Current BoE base rate with YoY change
    2. Average Mortgage Rate - 2-year fixed with YoY change
    3. Average House Price - Selected region with YoY change
    4. Annual Price Change - Selected region percentage

    Args:
        data: DashboardData containing all datasets
        selected_region: Region slug for housing metrics
    """
    col1, col2, col3, col4 = st.columns(4)

    # Get monetary metrics
    monetary_metrics = data.monetary.metrics if data.monetary else None

    # Get housing metrics for selected region
    housing_metrics = None
    if data.housing:
        try:
            region_enum = Region.from_string(selected_region)
            region_data = data.housing.get(region_enum)
            if region_data:
                housing_metrics = region_data.metrics
        except ValueError:
            pass

    with col1:
        _render_metric_card(
            title="Bank Rate",
            value=f"{monetary_metrics.current_bank_rate:.2f}%" if monetary_metrics else "N/A",
            delta=f"{monetary_metrics.bank_rate_change_yoy:+.2f}%" if monetary_metrics else None,
            delta_suffix=" YoY",
            help_text="Bank of England base rate",
        )

    with col2:
        _render_metric_card(
            title="2-Year Fixed Rate",
            value=f"{monetary_metrics.current_mortgage_2yr:.2f}%" if monetary_metrics else "N/A",
            delta=f"{monetary_metrics.mortgage_2yr_change_yoy:+.2f}%" if monetary_metrics else None,
            delta_suffix=" YoY",
            help_text="Average 2-year fixed mortgage rate",
        )

    with col3:
        if housing_metrics:
            price_str = f"£{housing_metrics.current_average_price:,.0f}"
        else:
            price_str = "N/A"

        _render_metric_card(
            title="Average House Price",
            value=price_str,
            delta=f"{housing_metrics.price_change_yoy:+.1f}%" if housing_metrics else None,
            delta_suffix=" YoY",
            help_text=f"Average price in {Region.from_string(selected_region).display_name if housing_metrics else 'UK'}",
        )

    with col4:
        _render_metric_card(
            title="5-Year Fixed Rate",
            value=f"{monetary_metrics.current_mortgage_5yr:.2f}%" if monetary_metrics else "N/A",
            delta=f"{monetary_metrics.mortgage_5yr_change_yoy:+.2f}%" if monetary_metrics else None,
            delta_suffix=" YoY",
            help_text="Average 5-year fixed mortgage rate",
        )


def _render_metric_card(
    title: str,
    value: str,
    delta: Optional[str] = None,
    delta_suffix: str = "",
    help_text: Optional[str] = None,
) -> None:
    """
    Render a single metric card.

    Args:
        title: Card title
        value: Main metric value
        delta: Change value (optional)
        delta_suffix: Suffix for delta (e.g., " YoY")
        help_text: Tooltip help text
    """
    # Use st.metric for consistent styling
    if delta:
        # Determine if delta is positive or negative for coloring
        try:
            delta_val = float(delta.replace("%", "").replace("+", ""))
            # For rates, positive = bad (red), for prices context-dependent
            st.metric(
                label=title,
                value=value,
                delta=f"{delta}{delta_suffix}",
                help=help_text,
            )
        except ValueError:
            st.metric(
                label=title,
                value=value,
                delta=f"{delta}{delta_suffix}",
                help=help_text,
            )
    else:
        st.metric(
            label=title,
            value=value,
            help=help_text,
        )
