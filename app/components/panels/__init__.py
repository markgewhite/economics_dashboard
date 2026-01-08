"""Deep dive panel components for the dashboard."""

from app.components.panels.housing_composition import render_housing_panel
from app.components.panels.economic_context import render_economic_panel
from app.components.panels.regional_spotlight import render_regional_panel
from app.components.panels.footer import render_footer

__all__ = [
    "render_housing_panel",
    "render_economic_panel",
    "render_regional_panel",
    "render_footer",
]
