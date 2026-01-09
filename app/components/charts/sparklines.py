"""Sparkline mini charts for trend indicators."""

from typing import Optional

import plotly.graph_objects as go
import streamlit as st

from app.design_tokens import Colors, hex_to_rgba


def render_sparkline(
    values: list[float],
    positive_is_good: bool = True,
    height: int = 50,
    show_change: bool = True,
    show_range: bool = False,
    show_axes: bool = False,
) -> None:
    """
    Render a minimal sparkline chart.

    Args:
        values: List of numeric values to plot
        positive_is_good: If True, upward trend is green; if False, downward is green
        height: Chart height in pixels
        show_change: Whether to show percentage change annotation
        show_range: Whether to show min/max range labels
        show_axes: Whether to show minimal y-axis with min/max values
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

    # Calculate min/max for axis
    min_val = min(clean_values)
    max_val = max(clean_values)

    # Create sparkline
    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            y=clean_values,
            mode="lines",
            line=dict(color=line_color, width=2),
            fill="tozeroy",
            fillcolor=hex_to_rgba(line_color, 0.125),
            hoverinfo="skip",
        )
    )

    # Layout with optional axes
    num_points = len(clean_values)

    # Add 25% padding to y-axis range so line doesn't touch edges
    y_range_span = max_val - min_val
    y_padding = y_range_span * 0.25
    y_min = min_val - y_padding
    y_max = max_val + y_padding

    if show_axes:
        fig.update_layout(
            height=height,
            margin=dict(l=35, r=35, t=5, b=18),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            showlegend=False,
            xaxis=dict(
                visible=True,
                showgrid=False,
                showline=False,
                tickmode="array",
                tickvals=[0, num_points - 1],
                ticktext=[f"-{num_points}m", "Now"],
                tickfont=dict(size=8, color="#64748B"),
            ),
            yaxis=dict(
                visible=True,
                showgrid=False,
                showline=False,
                range=[y_min, y_max],
                tickmode="array",
                tickvals=[min_val, max_val],
                ticktext=[f"{min_val:.1f}", f"{max_val:.1f}"],
                tickfont=dict(size=9, color="#64748B"),
                side="left",
            ),
        )
    else:
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

    if show_range and not show_axes:
        st.markdown(
            f'<span style="color: #64748B; font-size: 12px;">'
            f'{min_val:.1f} – {max_val:.1f}</span>',
            unsafe_allow_html=True,
        )

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
    caption: Optional[str] = None,
) -> None:
    """
    Render a metric value with an inline sparkline.

    Args:
        label: Metric label
        value: Current value as formatted string
        sparkline_values: Historical values for sparkline
        positive_is_good: Direction preference for coloring
        help_text: Optional descriptive text (displays full width below)
        caption: Optional highlight caption (e.g., "📈 1.5pp above target")
    """
    # Row 1: Label/Value/Caption on left, Sparkline on right
    col1, col2 = st.columns([1, 1])

    with col1:
        st.markdown(f"**{label}**")
        st.markdown(f"<span style='font-size: 24px; font-weight: 600;'>{value}</span>",
                   unsafe_allow_html=True)
        # Caption goes directly below the value
        if caption:
            st.caption(caption)

    with col2:
        render_sparkline(
            sparkline_values,
            positive_is_good=positive_is_good,
            height=100,
            show_change=False,
            show_range=False,
            show_axes=True,
        )

    # Help text extends full width (outside columns)
    if help_text:
        st.caption(help_text)
