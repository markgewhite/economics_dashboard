# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

UK Housing & Economic Conditions Dashboard - a portfolio project visualizing relationships between UK monetary policy, housing markets, and economic indicators.

**Current Phase**: Pre-implementation (architecture and planning complete)

**Python Version**: 3.13 (latest stable)

## Architecture

### Planned Structure
```
app/                    # Application code
  main.py              # Streamlit entry point
  config.py            # Configuration settings
  components/          # UI components (hero_metrics, charts, filters)
data/
  clients/             # API client modules
    bank_of_england.py # BoE IADB interface
    land_registry.py   # HM Land Registry UKHPI
    ons.py             # ONS statistics API
  transformers/        # Data transformation logic
  cache/               # Cached data storage (raw/ and processed/)
tests/
assets/
  styles.css           # Custom styling from Figma design tokens
```

### Tech Stack
- **Framework**: Streamlit (Python)
- **Visualization**: Plotly
- **Data Processing**: Pandas
- **Caching**: File-based with intelligent refresh

## Data Sources

| Source | Base URL | Auth | Notes |
|--------|----------|------|-------|
| Bank of England | `bankofengland.co.uk/boeapps/database` | None | Requires User-Agent header |
| HM Land Registry | `landregistry.data.gov.uk/data/ukhpi` | None | 13 regions need separate requests |
| ONS | `api.beta.ons.gov.uk/v1` | None | Rate limited: 200/min |

## Key Implementation Details

### Intelligent Refresh System
The dashboard uses schedule-aware caching rather than arbitrary time intervals:
- Daily data (BoE rates): Check after 10:00 UK time on weekdays
- Monthly data (housing): Check after 20th working day
- Monthly data (ONS): Check after ~15th of month

Cache metadata stored alongside data files tracks `last_fetch`, `next_expected`, and `refresh_reason`.

### Design Integration
Design tokens (colors, typography, spacing) should be extracted from the Figma design file via MCP before building UI components. Store in a centralized `design_tokens.py`.

## Commands

```bash
# Run the dashboard
streamlit run app/main.py

# Run tests
pytest tests/

# Run single test
pytest tests/test_clients.py::test_boe_fetch -v
```

## Reference Documents

- `design/software_architecture.md` - **Comprehensive architecture with code examples** (start here for implementation)
- `design/implementation_plan.md` - **Phased implementation plan with task checklists**
- `design/dashboard_requirements.md` - Full functional and technical requirements
- `design/api_integration_guide.md` - Complete API specifications with examples
- `design/figma_ai_dashboard_prompt.txt` - Design brief used for Figma generation