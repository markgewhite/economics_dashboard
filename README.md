# UK Housing & Economic Conditions Dashboard

A Streamlit dashboard visualizing relationships between UK monetary policy, housing markets, and economic indicators. Built as a portfolio project demonstrating data engineering, visualization, and software architecture skills.

## Features

- **Real-time Data Integration**: Fetches data from Bank of England, HM Land Registry, and ONS APIs
- **Intelligent Caching**: Schedule-aware caching system that refreshes based on data publication schedules
- **Interactive Visualizations**: Dual-axis charts, regional heat maps, sparklines, and composition breakdowns
- **Regional Analysis**: Compare housing metrics across 14 UK regions
- **Economic Context**: View broader economic indicators alongside housing data

## Screenshots

*Dashboard with hero metrics, rate trends, and regional analysis*

## Data Sources

| Source | Data | Update Frequency |
|--------|------|------------------|
| [Bank of England](https://www.bankofengland.co.uk/statistics) | Bank Rate, Mortgage Rates, SONIA | Daily |
| [HM Land Registry](https://landregistry.data.gov.uk/) | House Prices, Transactions | Monthly |
| [ONS](https://www.ons.gov.uk/) | CPI, Employment, Retail Sales | Monthly |

## Tech Stack

- **Framework**: Streamlit
- **Visualization**: Plotly
- **Data Processing**: Pandas
- **Caching**: File-based with Parquet storage
- **Python**: 3.13

## Installation

### Prerequisites

- Python 3.11+ (tested with 3.13)
- pip or uv package manager

### Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/economics_dashboard.git
   cd economics_dashboard
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Copy environment configuration:
   ```bash
   cp .env.example .env
   ```

5. Run the dashboard:
   ```bash
   streamlit run app/main.py
   ```

The dashboard will be available at `http://localhost:8501`

## Project Structure

```
economics_dashboard/
├── app/                    # Application code
│   ├── main.py            # Streamlit entry point
│   ├── config.py          # Configuration settings
│   ├── state.py           # Session state management
│   ├── design_tokens.py   # Design system tokens
│   ├── components/        # UI components
│   │   ├── charts/        # Chart components (Plotly)
│   │   └── panels/        # Deep dive panels
│   └── services/          # Business logic
│       └── data_service.py
├── data/                   # Data layer
│   ├── clients/           # API clients
│   │   ├── bank_of_england.py
│   │   ├── land_registry.py
│   │   └── ons.py
│   ├── cache/             # Caching system
│   │   ├── manager.py
│   │   └── scheduler.py
│   ├── transformers/      # Data transformation
│   └── models/            # Domain models
├── assets/                # Static assets
│   └── styles.css
├── tests/                 # Test suite
│   ├── unit/
│   └── integration/
└── design/                # Design documents
```

## Architecture Highlights

### Intelligent Refresh System

The dashboard uses schedule-aware caching rather than arbitrary time intervals:

- **Daily data** (BoE rates): Checks after 10:00 UK time on business days
- **Monthly data** (housing): Checks after the 20th working day
- **Monthly data** (ONS): Checks after approximately the 15th

This minimizes API calls while ensuring data freshness.

### Graceful Degradation

When API calls fail:
1. Falls back to cached data (even if stale)
2. Shows data freshness warnings
3. Continues displaying available data

### Design System

Colors, typography, and spacing follow a consistent design system extracted from Figma, stored in `app/design_tokens.py`.

## Testing

Run the test suite:

```bash
# All tests
pytest

# With coverage
pytest --cov=app --cov=data --cov-report=html

# Performance tests only
pytest tests/integration/test_performance.py -v

# Unit tests only
pytest tests/unit/
```

Current coverage: 58% (data layer: 82-100%, UI components tested manually)

## Configuration

Environment variables (set in `.env`):

| Variable | Description | Default |
|----------|-------------|---------|
| `CACHE_DIR` | Cache storage directory | `storage/cache` |
| `LOG_LEVEL` | Logging level | `INFO` |

## Development

### Code Quality

```bash
# Format code
black app data tests

# Sort imports
isort app data tests

# Type checking
mypy app data
```

### Adding New Data Sources

1. Create a client in `data/clients/`
2. Add a transformer in `data/transformers/`
3. Register in `DataService`
4. Add cache schedule in `data/cache/scheduler.py`

## License

This project is for portfolio/educational purposes.

## Acknowledgments

- Data provided by Bank of England, HM Land Registry, and ONS
- Design inspired by Bloomberg Terminal aesthetics
- Built with Streamlit, Plotly, and Pandas
