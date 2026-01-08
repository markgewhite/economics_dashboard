"""
Design tokens extracted from Figma design.

These are placeholder values. Update after extracting actual values
from the Figma design file via MCP.
"""


class Colors:
    """Color palette from Figma."""

    # Primary palette
    PRIMARY = "#1E3A8A"
    SECONDARY = "#3B82F6"
    ACCENT = "#10B981"

    # Background colors
    BG_PRIMARY = "#FFFFFF"
    BG_SECONDARY = "#F8FAFC"
    BG_CARD = "#FFFFFF"

    # Text colors
    TEXT_PRIMARY = "#1E293B"
    TEXT_SECONDARY = "#64748B"
    TEXT_MUTED = "#94A3B8"

    # Status colors
    POSITIVE = "#10B981"
    NEGATIVE = "#EF4444"
    NEUTRAL = "#6B7280"

    # Chart colors
    CHART_1 = "#3B82F6"
    CHART_2 = "#10B981"
    CHART_3 = "#F59E0B"
    CHART_4 = "#8B5CF6"
    CHART_5 = "#EC4899"


class Typography:
    """Typography specifications from Figma."""

    FONT_FAMILY = "Inter, -apple-system, BlinkMacSystemFont, sans-serif"

    # Font sizes
    SIZE_H1 = "32px"
    SIZE_H2 = "24px"
    SIZE_H3 = "18px"
    SIZE_BODY = "14px"
    SIZE_CAPTION = "12px"
    SIZE_METRIC_VALUE = "36px"

    # Font weights
    WEIGHT_REGULAR = 400
    WEIGHT_MEDIUM = 500
    WEIGHT_SEMIBOLD = 600
    WEIGHT_BOLD = 700

    # Line heights
    LINE_HEIGHT_TIGHT = 1.2
    LINE_HEIGHT_NORMAL = 1.5
    LINE_HEIGHT_RELAXED = 1.75


class Spacing:
    """Spacing system from Figma."""

    # Base unit: 4px
    XS = "4px"
    SM = "8px"
    MD = "16px"
    LG = "24px"
    XL = "32px"
    XXL = "48px"

    # Component-specific
    CARD_PADDING = "24px"
    SECTION_GAP = "24px"
    GRID_GUTTER = "16px"


class Effects:
    """Visual effects from Figma."""

    SHADOW_SM = "0 1px 2px rgba(0, 0, 0, 0.05)"
    SHADOW_MD = "0 4px 6px rgba(0, 0, 0, 0.1)"
    SHADOW_LG = "0 10px 15px rgba(0, 0, 0, 0.1)"

    BORDER_RADIUS_SM = "4px"
    BORDER_RADIUS_MD = "8px"
    BORDER_RADIUS_LG = "12px"

    BORDER_COLOR = "#E2E8F0"
    BORDER_WIDTH = "1px"


class ChartConfig:
    """Plotly chart configuration derived from design tokens."""

    # Color sequences for multi-series charts
    COLOR_SEQUENCE = [
        Colors.CHART_1,
        Colors.CHART_2,
        Colors.CHART_3,
        Colors.CHART_4,
        Colors.CHART_5,
    ]

    # Heat map color scale (negative -> neutral -> positive)
    HEAT_MAP_SCALE = [
        [0.0, Colors.NEGATIVE],
        [0.5, "#FFFFFF"],
        [1.0, Colors.POSITIVE],
    ]

    # Layout defaults
    LAYOUT_DEFAULTS = {
        "font_family": Typography.FONT_FAMILY,
        "font_color": Colors.TEXT_PRIMARY,
        "paper_bgcolor": Colors.BG_CARD,
        "plot_bgcolor": Colors.BG_CARD,
        "margin": {"l": 60, "r": 20, "t": 40, "b": 40},
    }
