# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

UK Housing & Economic Conditions Dashboard - a portfolio project visualizing relationships between UK monetary policy, housing markets, and economic indicators.

**Current Status**: Implementation complete (Phases 1-10). Ready for deployment.

**Python Version**: 3.13

## Architecture

### Project Structure
```
app/                        # Application code
  main.py                   # Streamlit entry point
  config.py                 # Configuration settings
  state.py                  # Session state management
  design_tokens.py          # Design system (colors, typography, spacing)
  components/               # UI components
    header.py               # Dashboard header
    hero_metrics.py         # Four main metric cards
    filters.py              # Time range and region filters
    charts/                 # Plotly chart components
      dual_axis.py          # Rates vs house prices
      heat_map.py           # Regional price changes
      rate_trends.py        # Mortgage rate trends
      transactions.py       # Monthly transaction volumes
      sparklines.py         # Mini trend charts
      composition.py        # Donut charts
    panels/                 # Deep dive panels
      housing_composition.py
      economic_context.py
      regional_spotlight.py
      footer.py
  services/
    data_service.py         # Data orchestration layer

data/                       # Data layer
  clients/                  # API clients with retry logic
    base.py                 # BaseAPIClient with tenacity
    bank_of_england.py      # BoE IADB interface
    land_registry.py        # HM Land Registry UKHPI
    ons.py                  # ONS statistics API
  cache/                    # Intelligent caching system
    manager.py              # CacheManager (Parquet storage)
    scheduler.py            # RefreshScheduler (publication-aware)
  transformers/             # Raw data to domain models
    monetary.py
    housing.py
    economic.py
  models/                   # Domain models (dataclasses)
    monetary.py
    housing.py
    economic.py
    cache.py

tests/                      # Test suite (163 tests)
  unit/                     # Unit tests for each module
  integration/              # Pipeline and performance tests

assets/
  styles.css                # Custom CSS styling
```

### Tech Stack
- **Framework**: Streamlit
- **Visualization**: Plotly
- **Data Processing**: Pandas
- **Caching**: Parquet files with JSON metadata
- **HTTP**: httpx with tenacity retry logic

## Data Sources

| Source | Data | Refresh Schedule |
|--------|------|-----------------|
| Bank of England | Bank Rate, Mortgage Rates, SONIA | Daily after 10:00 UK (weekdays) |
| HM Land Registry | House Prices, Transactions (14 regions) | Monthly after 20th working day |
| ONS | CPI, Employment, Retail Sales | Monthly after ~15th |

## Key Implementation Details

### Data Service Pattern
```python
from app.services.data_service import DataService

service = DataService(cache_dir="storage/cache")
data = service.get_dashboard_data()  # Returns DashboardData

# Access typed data
data.monetary      # MonetaryTimeSeries
data.housing       # RegionalHousingData
data.economic      # EconomicTimeSeries
data.metadata      # Dict of CacheMetadata
```

### Graceful Degradation
- Falls back to stale cache on API failures
- Partial data loading (continues if one source fails)
- Error and warning reporting via `data.errors` and `data.warnings`

### Design Tokens
Colors and styling extracted from Figma design:
```python
from app.design_tokens import Colors, ChartConfig

Colors.BANK_RATE         # #1E293B - dark
Colors.MORTGAGE_2YR      # #EF4444 - red
Colors.HOUSE_PRICE_INDEX # #3B82F6 - blue
Colors.POSITIVE          # #10B981 - green
Colors.NEGATIVE          # #EF4444 - red
```

## Commands

```bash
# Run the dashboard
streamlit run app/main.py

# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov=data --cov-report=html

# Run performance tests
pytest tests/integration/test_performance.py -v

# Format code
black app data tests
isort app data tests
```

## Testing

- **163 tests** across unit and integration
- **58% coverage** overall (data layer 82-100%, UI requires manual testing)
- Performance tests verify <3s load time with cached data

## Common Tasks

### Adding a new chart
1. Create component in `app/components/charts/`
2. Use design tokens from `app/design_tokens.py`
3. Register in `app/components/charts/__init__.py`
4. Add to main layout in `app/main.py`

### Adding a new data source
1. Create client in `data/clients/` extending `BaseAPIClient`
2. Create transformer in `data/transformers/`
3. Add model in `data/models/`
4. Register schedule in `data/cache/scheduler.py`
5. Add to `DataService.get_dashboard_data()`

### Modifying cache behavior
- Schedules defined in `data/cache/scheduler.py`
- Cache storage in `data/cache/manager.py`
- Metadata model in `data/models/cache.py`

## Reference Documents

- `design/software_architecture.md` - Comprehensive architecture
- `design/implementation_plan.md` - Phased implementation plan
- `design/dashboard_requirements.md` - Functional requirements
- `design/api_integration_guide.md` - API specifications
