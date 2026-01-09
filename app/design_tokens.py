"""
Design tokens extracted from Figma Make design.

Values extracted from UK Housing & Economic Conditions Dashboard
Figma Make project on 2026-01-09.
"""


class Colors:
    """Color palette from Figma Make design."""

    # Primary palette
    PRIMARY = "#3B82F6"  # Primary blue (header icon, links, accents)
    PRIMARY_DARK = "#1E3A8A"  # Darker blue for emphasis
    SECONDARY = "#64748B"  # Slate gray
    ACCENT = "#10B981"  # Emerald green

    # Background colors
    BG_PRIMARY = "#FFFFFF"  # White - cards, panels
    BG_SECONDARY = "#F8FAFC"  # Slate 50 - page background
    BG_CARD = "#FFFFFF"  # White - card backgrounds
    BG_HEADER = "#FFFFFF"  # White - header background

    # Text colors
    TEXT_PRIMARY = "#1E293B"  # Slate 800 - headings, primary text
    TEXT_SECONDARY = "#64748B"  # Slate 500 - subtitles, labels
    TEXT_MUTED = "#94A3B8"  # Slate 400 - captions, metadata

    # Status colors (from trend indicators in design)
    POSITIVE = "#10B981"  # Emerald 500 - positive changes
    NEGATIVE = "#EF4444"  # Red 500 - negative changes
    NEUTRAL = "#6B7280"  # Gray 500 - neutral/unchanged

    # Chart colors - specific to dashboard charts
    BANK_RATE = "#1E293B"  # Dark - Bank Rate line
    MORTGAGE_2YR = "#EF4444"  # Red - 2yr Mortgage Rate
    MORTGAGE_5YR = "#F97316"  # Orange - 5yr Fixed
    TRACKER_RATE = "#8B5CF6"  # Purple - Tracker rate
    HOUSE_PRICE_INDEX = "#3B82F6"  # Blue - House Price Index

    # Regional heat map gradient
    HEAT_STRONG_GROWTH = "#10B981"  # Green - >2% growth
    HEAT_MODEST = "#94A3B8"  # Gray - modest change
    HEAT_DECLINE = "#EF4444"  # Red - <-1% decline

    # General chart palette
    CHART_1 = "#3B82F6"  # Blue
    CHART_2 = "#10B981"  # Green
    CHART_3 = "#F59E0B"  # Amber
    CHART_4 = "#8B5CF6"  # Purple
    CHART_5 = "#EC4899"  # Pink


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

    # Rate chart colors (from Figma design)
    RATE_COLORS = {
        "bank_rate": Colors.BANK_RATE,
        "mortgage_2yr": Colors.MORTGAGE_2YR,
        "mortgage_5yr": Colors.MORTGAGE_5YR,
        "tracker": Colors.TRACKER_RATE,
        "house_price_index": Colors.HOUSE_PRICE_INDEX,
    }

    # Regional heat map gradient thresholds
    HEAT_MAP_THRESHOLDS = {
        "strong_growth": 2.0,  # >2% is strong growth
        "decline": -1.0,  # <-1% is decline
    }

    # Heat map color scale (negative -> neutral -> positive)
    HEAT_MAP_SCALE = [
        [0.0, Colors.HEAT_DECLINE],
        [0.5, Colors.HEAT_MODEST],
        [1.0, Colors.HEAT_STRONG_GROWTH],
    ]

    # Layout defaults
    LAYOUT_DEFAULTS = {
        "font_family": Typography.FONT_FAMILY,
        "font_color": Colors.TEXT_PRIMARY,
        "paper_bgcolor": Colors.BG_CARD,
        "plot_bgcolor": Colors.BG_CARD,
        "margin": {"l": 60, "r": 20, "t": 40, "b": 40},
    }

    # Grid styling
    GRID_STYLE = {
        "gridcolor": "#E2E8F0",
        "gridwidth": 1,
        "showgrid": True,
    }

    # Axis styling
    AXIS_STYLE = {
        "linecolor": "#E2E8F0",
        "linewidth": 1,
        "tickfont": {"size": 12, "color": Colors.TEXT_SECONDARY},
        "title_font": {"size": 12, "color": Colors.TEXT_SECONDARY},
    }
