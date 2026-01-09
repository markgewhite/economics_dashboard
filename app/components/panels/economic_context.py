"""Economic context panel showing CPI, employment, and retail trends."""

import streamlit as st

from app.design_tokens import Colors
from app.components.charts.sparklines import render_metric_with_sparkline
from data.models.economic import EconomicTimeSeries


def render_economic_panel(economic_data: EconomicTimeSeries) -> None:
    """
    Render economic context panel with key indicators.

    Shows CPI inflation, employment rate, and retail sales index
    with sparkline trends.

    Args:
        economic_data: EconomicTimeSeries containing economic indicators
    """
    st.markdown(
        '<div class="panel"><div class="panel-title">Economic Context</div>',
        unsafe_allow_html=True,
    )

    if not economic_data or not economic_data.data_points:
        st.info("No economic data available.")
        st.markdown('</div>', unsafe_allow_html=True)
        return

    metrics = economic_data.metrics

    # CPI Inflation
    st.markdown("---")
    _render_cpi_section(economic_data, metrics)

    # Employment Rate
    st.markdown("---")
    _render_employment_section(economic_data, metrics)

    # Retail Sales
    st.markdown("---")
    _render_retail_section(economic_data, metrics)

    st.markdown('</div>', unsafe_allow_html=True)


def _render_cpi_section(economic_data: EconomicTimeSeries, metrics) -> None:
    """Render CPI inflation section."""
    cpi_values = economic_data.cpi_values

    if metrics and metrics.current_cpi is not None:
        current_value = f"{metrics.current_cpi:.1f}%"

        # Build caption based on target comparison
        if metrics.current_cpi > 2:
            caption = f"📈 {metrics.current_cpi - 2:.1f}pp above 2% target"
        elif metrics.current_cpi < 2:
            caption = f"📉 {2 - metrics.current_cpi:.1f}pp below 2% target"
        else:
            caption = "✓ At 2% target"

        # For inflation, lower is generally better (positive_is_good=False)
        render_metric_with_sparkline(
            label="CPI Inflation",
            value=current_value,
            sparkline_values=cpi_values[-12:] if len(cpi_values) > 12 else cpi_values,
            positive_is_good=False,
            help_text="Annual rate of inflation (target: 2%)",
            caption=caption,
        )
    else:
        st.write("CPI data not available")


def _render_employment_section(economic_data: EconomicTimeSeries, metrics) -> None:
    """Render employment rate section."""
    employment_values = economic_data.employment_values

    if metrics and metrics.current_employment is not None:
        current_value = f"{metrics.current_employment:.1f}%"
        # Higher employment is good
        render_metric_with_sparkline(
            label="Employment Rate",
            value=current_value,
            sparkline_values=employment_values[-12:] if len(employment_values) > 12 else employment_values,
            positive_is_good=True,
            help_text="Percentage of working-age population employed",
        )
    else:
        st.write("Employment data not available")


def _render_retail_section(economic_data: EconomicTimeSeries, metrics) -> None:
    """Render retail sales section."""
    retail_values = economic_data.retail_values

    if metrics and metrics.current_retail_index is not None:
        current_value = f"{metrics.current_retail_index:.1f}"

        # Build caption based on YoY change
        caption = None
        if metrics.retail_change_yoy is not None:
            if metrics.retail_change_yoy > 0:
                caption = f"📈 {metrics.retail_change_yoy:+.1f}% vs last year"
            else:
                caption = f"📉 {metrics.retail_change_yoy:+.1f}% vs last year"

        # Higher retail is generally positive
        render_metric_with_sparkline(
            label="Retail Sales Index",
            value=current_value,
            sparkline_values=retail_values[-12:] if len(retail_values) > 12 else retail_values,
            positive_is_good=True,
            help_text="Index of retail sales volume (seasonally adjusted)",
            caption=caption,
        )
    else:
        st.write("Retail sales data not available")
