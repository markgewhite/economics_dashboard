"""Dashboard header component with title and refresh controls."""

from typing import Callable, Optional

import streamlit as st

from data.models.cache import CacheMetadata


def render_header(
    metadata: dict[str, Optional[CacheMetadata]],
    on_refresh: Callable[[], None],
) -> None:
    """
    Render dashboard header with title, subtitle, and refresh controls.

    Args:
        metadata: Dict of dataset names to their cache metadata
        on_refresh: Callback function to trigger data refresh
    """
    header_col, status_col, refresh_col = st.columns([5, 4, 1])

    with header_col:
        st.title("UK Housing & Economic Dashboard")
        st.caption(
            "Visualizing relationships between monetary policy, "
            "housing markets, and economic indicators"
        )

    with status_col:
        _render_data_freshness(metadata)

    with refresh_col:
        if st.button("Refresh", type="secondary", use_container_width=True):
            on_refresh()
            st.rerun()


def _render_data_freshness(metadata: dict[str, Optional[CacheMetadata]]) -> None:
    """Render data freshness indicators for each dataset."""
    indicators = []

    for dataset, meta in metadata.items():
        if meta is None:
            status = "loading"
            label = "Loading..."
        elif meta.is_stale:
            status = "stale"
            label = f"{dataset.title()}: Stale"
        else:
            status = "current"
            label = f"{dataset.title()}: {meta.age_description}"

        indicators.append((status, label))

    # Render as inline status indicators
    status_html = " ".join([
        f'<span class="status-indicator">'
        f'<span class="status-dot {status}"></span>'
        f'{label}'
        f'</span>'
        for status, label in indicators
    ])

    st.markdown(
        f'<div style="display: flex; gap: 16px; align-items: center; '
        f'justify-content: flex-end; height: 100%; padding-top: 8px;">'
        f'{status_html}</div>',
        unsafe_allow_html=True,
    )
