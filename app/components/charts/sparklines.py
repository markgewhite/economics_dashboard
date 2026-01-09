"""Sparkline mini charts for trend indicators."""

from typing import Optional

import plotly.graph_objects as go
import streamlit as st

from app.design_tokens import Colors


def _hex_to_rgba(hex_color: str, alpha: float = 0.125) -> str:
    """Convert hex color to rgba string for Plotly compatibility."""
    hex_color = hex_color.lstrip("#")
    r = int(hex_color[0:2], 16)
    g = int(hex_color[2:4], 16)
    b = int(hex_color[4:6], 16)
    return f"rgba({r}, {g}, {b}, {alpha})"


def render_sparkline(
    values: list[float],
    positive_is_good: bool = True,
    height: int = 50,
    show_change: bool = True,
) -> None:
    """
    Render a minimal sparkline chart.

    Args:
        values: List of numeric values to plot
        positive_is_good: If True, upward trend is green; if False, downward is green
        height: Chart height in pixels
        show_change: Whether to show percentage change annotation
    """
    # Filter out None values
    clean_values = [v for v in values if v is not None]

    if not clean_values or len(clean_values) < 2:
        st.write("--")
        return

    # Calculate change
    first_val = clean_values[0] if clean_values[0] != 0 else 0.001
    last_val = clean_values[-1]
    pct_change = ((last_val - first_val) / abs(first_val)) * 100

    # Determine color based on trend direction and preference
    is_positive_trend = last_val > first_val
    if positive_is_good:
        line_color = Colors.POSITIVE if is_positive_trend else Colors.NEGATIVE
    else:
        line_color = Colors.NEGATIVE if is_positive_trend else Colors.POSITIVE

    # Create sparkline
    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            y=clean_values,
            mode="lines",
            line=dict(color=line_color, width=2),
            fill="tozeroy",
            fillcolor=_hex_to_rgba(line_color, 0.125),
            hoverinfo="skip",
        )
    )

    # Minimal layout
    fig.update_layout(
        height=height,
        margin=dict(l=0, r=0, t=0, b=0),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        showlegend=False,
        xaxis=dict(visible=False),
        yaxis=dict(visible=False),
    )

    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    if show_change:
        change_color = "green" if (pct_change > 0) == positive_is_good else "red"
        st.markdown(
            f'<span style="color: {change_color}; font-size: 12px;">'
            f'{pct_change:+.1f}%</span>',
            unsafe_allow_html=True,
        )


def render_metric_with_sparkline(
    label: str,
    value: str,
    sparkline_values: list[float],
    positive_is_good: bool = True,
    help_text: Optional[str] = None,
) -> None:
    """
    Render a metric value with an inline sparkline.

    Args:
        label: Metric label
        value: Current value as formatted string
        sparkline_values: Historical values for sparkline
        positive_is_good: Direction preference for coloring
        help_text: Optional tooltip text
    """
    col1, col2 = st.columns([2, 1])

    with col1:
        st.markdown(f"**{label}**")
        st.markdown(f"<span style='font-size: 24px; font-weight: 600;'>{value}</span>",
                   unsafe_allow_html=True)
        if help_text:
            st.caption(help_text)

    with col2:
        render_sparkline(
            sparkline_values,
            positive_is_good=positive_is_good,
            height=40,
            show_change=True,
        )
