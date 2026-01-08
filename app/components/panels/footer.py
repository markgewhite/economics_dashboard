"""Dashboard footer with data attribution and metadata."""

from datetime import datetime
from typing import Optional

import streamlit as st

from data.models.cache import CacheMetadata


def render_footer(metadata: Optional[dict[str, Optional[CacheMetadata]]] = None) -> None:
    """
    Render dashboard footer with data attribution and update times.

    Args:
        metadata: Optional dict of dataset names to their cache metadata
    """
    st.markdown("---")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("**Data Sources**")
        st.markdown(
            """
            - [Bank of England](https://www.bankofengland.co.uk/statistics)
            - [HM Land Registry](https://landregistry.data.gov.uk/)
            - [Office for National Statistics](https://www.ons.gov.uk/)
            """,
        )

    with col2:
        st.markdown("**Last Updated**")
        if metadata:
            for dataset, meta in metadata.items():
                if meta:
                    st.caption(f"{dataset.title()}: {meta.age_description}")
                else:
                    st.caption(f"{dataset.title()}: Not loaded")
        else:
            st.caption(f"Dashboard loaded: {datetime.now().strftime('%Y-%m-%d %H:%M')}")

    with col3:
        st.markdown("**About**")
        st.markdown(
            """
            UK Housing & Economic Dashboard

            A portfolio project visualizing relationships between
            monetary policy, housing markets, and economic indicators.
            """,
        )

    # Copyright and version
    st.markdown(
        """
        <div style="text-align: center; padding: 20px 0; color: #94A3B8; font-size: 12px;">
            <p>UK Housing & Economic Dashboard | Built with Streamlit & Plotly</p>
            <p>Data refreshes automatically based on publication schedules</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
