"""UI components for the dashboard."""

from app.components.filters import render_filters
from app.components.header import render_header
from app.components.hero_metrics import render_hero_metrics
from app.components.charts import (
    render_rates_vs_prices,
    render_regional_heat_map,
    render_rate_trends,
    render_transactions,
)
from app.components.panels import (
    render_housing_panel,
    render_economic_panel,
    render_regional_panel,
    render_footer,
)

__all__ = [
    "render_filters",
    "render_header",
    "render_hero_metrics",
    "render_rates_vs_prices",
    "render_regional_heat_map",
    "render_rate_trends",
    "render_transactions",
    "render_housing_panel",
    "render_economic_panel",
    "render_regional_panel",
    "render_footer",
]
