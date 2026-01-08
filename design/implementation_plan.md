# UK Housing & Economic Dashboard - Implementation Plan

## Document Information

| Field | Value |
|-------|-------|
| Version | 1.0 |
| Date | January 2026 |
| Status | Draft |
| Reference | `design/software_architecture.md` |

---

## 1. Overview

This document outlines the phased implementation approach for the UK Housing & Economic Dashboard. Each phase builds on the previous, with clear deliverables and testing criteria.

### 1.1 Implementation Principles

1. **Incremental Delivery**: Each phase produces working, testable code
2. **Test-Driven**: Write tests alongside implementation
3. **Documentation**: Update CLAUDE.md as architecture evolves
4. **Version Control**: Commit frequently with meaningful messages

### 1.2 Technical Foundation

- **Python**: 3.13 (latest stable)
- **Package Versions**: Resolved by pip at install time, then documented
- **Virtual Environment**: Use `venv` for isolation

---

## 2. Phase Overview

| Phase | Focus | Key Deliverables |
|-------|-------|------------------|
| 1 | Foundation | Project structure, config, data models |
| 2 | API Clients | Three working API clients with tests |
| 3 | Caching | Schedule-aware cache system |
| 4 | Transformers | Data transformation logic |
| 5 | Data Service | Orchestration layer |
| 6 | App Shell | Basic Streamlit app |
| 7 | Main Components | Hero metrics and primary charts |
| 8 | Deep Dive | Secondary panels and interactions |
| 9 | Design Polish | Figma integration, styling |
| 10 | Testing | Comprehensive test coverage |
| 11 | Deployment | Production deployment |

---

## 3. Phase Details

### Phase 1: Foundation

**Objective**: Establish project structure and core infrastructure.

#### Tasks

| # | Task | Files Created |
|---|------|---------------|
| 1.1 | Create project directory structure | All directories per architecture |
| 1.2 | Initialize Python environment | `pyproject.toml`, `requirements.txt` |
| 1.3 | Set up environment configuration | `.env.example`, `app/config.py` |
| 1.4 | Implement data models | `data/models/*.py` |
| 1.5 | Create exception hierarchy | `data/exceptions.py` |
| 1.6 | Configure logging | `app/config.py` (logging setup) |
| 1.7 | Initialize git repository | `.gitignore`, initial commit |

#### Files to Create

```
pyproject.toml
requirements.txt
.env.example
.gitignore
app/__init__.py
app/config.py
data/__init__.py
data/exceptions.py
data/models/__init__.py
data/models/monetary.py
data/models/housing.py
data/models/economic.py
data/models/cache.py
```

#### Verification

- [ ] `pip install -r requirements.txt` succeeds
- [ ] `python -c "from app.config import Config; Config.from_env()"` works
- [ ] All data models can be imported and instantiated
- [ ] Unit tests pass: `pytest tests/unit/test_models/`

#### Testing

```python
# tests/unit/test_models/test_monetary.py
def test_monetary_data_point_creation():
    """Test MonetaryDataPoint can be created."""
    from data.models.monetary import MonetaryDataPoint
    from datetime import date

    dp = MonetaryDataPoint(
        observation_date=date(2024, 1, 1),
        bank_rate=5.25,
    )
    assert dp.observation_date == date(2024, 1, 1)
    assert dp.bank_rate == 5.25
```

---

### Phase 2: API Clients

**Objective**: Implement all three API clients with retry logic and error handling.

#### Dependencies

- Phase 1 complete

#### Tasks

| # | Task | Files Created |
|---|------|---------------|
| 2.1 | Implement BaseAPIClient | `data/clients/base.py` |
| 2.2 | Implement BankOfEnglandClient | `data/clients/bank_of_england.py` |
| 2.3 | Implement LandRegistryClient | `data/clients/land_registry.py` |
| 2.4 | Implement ONSClient | `data/clients/ons.py` |
| 2.5 | Create test fixtures | `tests/fixtures/sample_*.csv` |
| 2.6 | Write unit tests | `tests/unit/test_clients/*.py` |

#### Files to Create

```
data/clients/__init__.py
data/clients/base.py
data/clients/bank_of_england.py
data/clients/land_registry.py
data/clients/ons.py
tests/fixtures/sample_boe_response.csv
tests/fixtures/sample_land_registry.csv
tests/fixtures/sample_ons_response.csv
tests/unit/test_clients/__init__.py
tests/unit/test_clients/test_boe_client.py
tests/unit/test_clients/test_land_registry_client.py
tests/unit/test_clients/test_ons_client.py
```

#### Verification

- [ ] Each client can fetch sample data from live APIs
- [ ] Retry logic triggers on simulated failures
- [ ] User-Agent header is set for BoE client
- [ ] Unit tests pass with mocked responses

#### Testing

```python
# tests/unit/test_clients/test_boe_client.py
import pytest
from unittest.mock import patch, Mock

def test_boe_client_requires_user_agent():
    """Verify User-Agent header is set."""
    from data.clients.bank_of_england import BankOfEnglandClient

    client = BankOfEnglandClient()
    assert "User-Agent" in client.session.headers

def test_boe_client_parses_csv_response(sample_boe_response):
    """Test CSV parsing handles BoE format."""
    # Test with fixture data
    ...
```

#### Live API Smoke Test

```python
# Manual verification (not in automated tests)
from data.clients.bank_of_england import BankOfEnglandClient
from datetime import date

client = BankOfEnglandClient()
result = client.fetch(
    series=["bank_rate"],
    start_date=date(2024, 1, 1),
    end_date=date(2024, 1, 31)
)
assert result.success
print(f"Fetched {len(result.data)} rows")
```

---

### Phase 3: Caching System

**Objective**: Implement schedule-aware caching with metadata tracking.

#### Dependencies

- Phase 1 complete
- Phase 2 complete (for integration testing)

#### Tasks

| # | Task | Files Created |
|---|------|---------------|
| 3.1 | Implement RefreshScheduler | `data/cache/scheduler.py` |
| 3.2 | Implement CacheManager | `data/cache/manager.py` |
| 3.3 | Add metadata handling | `data/cache/metadata.py` |
| 3.4 | Write unit tests | `tests/unit/test_cache/*.py` |

#### Files to Create

```
data/cache/__init__.py
data/cache/scheduler.py
data/cache/manager.py
data/cache/metadata.py
tests/unit/test_cache/__init__.py
tests/unit/test_cache/test_scheduler.py
tests/unit/test_cache/test_manager.py
```

#### Verification

- [ ] RefreshScheduler correctly determines refresh need for various scenarios
- [ ] CacheManager can write and read parquet files
- [ ] Metadata is persisted and loaded correctly
- [ ] UK business day logic handles weekends and holidays

#### Testing

```python
# tests/unit/test_cache/test_scheduler.py
import pytest
from datetime import datetime, time
from zoneinfo import ZoneInfo

def test_daily_refresh_not_needed_same_day():
    """If fetched today after check time, no refresh needed."""
    from data.cache.scheduler import RefreshScheduler

    scheduler = RefreshScheduler()
    uk_tz = ZoneInfo("Europe/London")

    # Last fetch was today at 11:00
    last_fetch = datetime(2026, 1, 8, 11, 0, tzinfo=uk_tz)

    # Check at 14:00 same day
    with patch_now(datetime(2026, 1, 8, 14, 0, tzinfo=uk_tz)):
        decision = scheduler.should_refresh("monetary", last_fetch)

    assert decision.should_refresh is False
    assert decision.reason == RefreshReason.ALREADY_CURRENT

def test_weekend_no_refresh():
    """No refresh needed on weekends for daily data."""
    ...

def test_monthly_refresh_after_publication_day():
    """Refresh needed after publication day for monthly data."""
    ...
```

---

### Phase 4: Transformers

**Objective**: Implement data transformation from raw API responses to domain models.

#### Dependencies

- Phase 1 complete (data models)
- Phase 2 complete (API clients for fixture generation)

#### Tasks

| # | Task | Files Created |
|---|------|---------------|
| 4.1 | Implement BaseTransformer | `data/transformers/base.py` |
| 4.2 | Implement MonetaryTransformer | `data/transformers/monetary.py` |
| 4.3 | Implement HousingTransformer | `data/transformers/housing.py` |
| 4.4 | Implement EconomicTransformer | `data/transformers/economic.py` |
| 4.5 | Write unit tests | `tests/unit/test_transformers/*.py` |

#### Files to Create

```
data/transformers/__init__.py
data/transformers/base.py
data/transformers/monetary.py
data/transformers/housing.py
data/transformers/economic.py
tests/unit/test_transformers/__init__.py
tests/unit/test_transformers/test_monetary.py
tests/unit/test_transformers/test_housing.py
tests/unit/test_transformers/test_economic.py
```

#### Verification

- [ ] Transformers correctly parse dates in various formats
- [ ] Missing values handled appropriately (forward fill)
- [ ] Metrics calculated correctly (YoY changes)
- [ ] Validation warnings generated for out-of-range values

#### Testing

```python
# tests/unit/test_transformers/test_monetary.py
def test_monthly_aggregation():
    """Test daily data aggregates to monthly correctly."""
    from data.transformers.monetary import MonetaryTransformer
    import pandas as pd

    # Create daily test data
    df = pd.DataFrame({
        "date": pd.date_range("2024-01-01", "2024-01-31"),
        "bank_rate": [5.25] * 31,
        "sonia": [5.19 + i * 0.01 for i in range(31)],
    })

    transformer = MonetaryTransformer()
    result = transformer.transform(df)

    # Should have 1 month of data
    assert len(result.data_points) == 1
    # SONIA should be averaged
    assert result.data_points[0].sonia == pytest.approx(5.34, rel=0.01)
```

---

### Phase 5: Data Service Layer

**Objective**: Create orchestration layer that coordinates clients, transformers, and cache.

#### Dependencies

- Phases 1-4 complete

#### Tasks

| # | Task | Files Created |
|---|------|---------------|
| 5.1 | Implement DataService | `app/services/data_service.py` |
| 5.2 | Implement graceful degradation | (in DataService) |
| 5.3 | Add refresh status API | (in DataService) |
| 5.4 | Write integration tests | `tests/integration/test_data_pipeline.py` |

#### Files to Create

```
app/services/__init__.py
app/services/data_service.py
tests/integration/__init__.py
tests/integration/test_data_pipeline.py
```

#### Verification

- [ ] DataService returns complete DashboardData on success
- [ ] Falls back to stale cache when API fails
- [ ] Parallel fetching works for Land Registry regions
- [ ] Refresh status correctly reports data freshness

#### Testing

```python
# tests/integration/test_data_pipeline.py
def test_full_pipeline_with_cache(tmp_path):
    """Test complete data pipeline."""
    from app.services.data_service import DataService

    service = DataService(cache_dir=tmp_path)

    # First call - fetches from APIs
    data1 = service.get_dashboard_data()
    assert data1.is_complete

    # Second call - uses cache
    data2 = service.get_dashboard_data()
    assert data2.is_complete
    # Verify cache was used (check metadata timestamps)

def test_graceful_degradation_on_api_failure(tmp_path):
    """Test fallback to stale cache when API fails."""
    ...
```

---

### Phase 6: Streamlit Application Shell

**Objective**: Create basic Streamlit application with layout and state management.

#### Dependencies

- Phase 5 complete

#### Tasks

| # | Task | Files Created |
|---|------|---------------|
| 6.1 | Create main.py entry point | `app/main.py` |
| 6.2 | Implement StateManager | `app/state.py` |
| 6.3 | Create placeholder design tokens | `app/design_tokens.py` |
| 6.4 | Implement filter controls | `app/components/filters.py` |
| 6.5 | Create basic styles.css | `assets/styles.css` |

#### Files to Create

```
app/main.py
app/state.py
app/design_tokens.py
app/components/__init__.py
app/components/filters.py
assets/styles.css
```

#### Verification

- [ ] `streamlit run app/main.py` launches dashboard
- [ ] Time range selector updates session state
- [ ] Region dropdown shows all regions
- [ ] Page loads data without errors

#### Testing

Manual testing:
1. Run `streamlit run app/main.py`
2. Verify page loads without errors
3. Verify filters are interactive
4. Verify data loading spinner appears

---

### Phase 7: Main Components

**Objective**: Implement hero metrics and primary chart visualizations.

#### Dependencies

- Phase 6 complete

#### Tasks

| # | Task | Files Created |
|---|------|---------------|
| 7.1 | Implement header component | `app/components/header.py` |
| 7.2 | Implement hero_metrics | `app/components/hero_metrics.py` |
| 7.3 | Implement dual_axis chart | `app/components/charts/dual_axis.py` |
| 7.4 | Implement heat_map | `app/components/charts/heat_map.py` |
| 7.5 | Implement rate_trends | `app/components/charts/rate_trends.py` |
| 7.6 | Implement transactions | `app/components/charts/transactions.py` |

#### Files to Create

```
app/components/header.py
app/components/hero_metrics.py
app/components/charts/__init__.py
app/components/charts/dual_axis.py
app/components/charts/heat_map.py
app/components/charts/rate_trends.py
app/components/charts/transactions.py
```

#### Verification

- [ ] Hero metrics display 4 cards with values and changes
- [ ] Dual-axis chart shows rates and prices together
- [ ] Heat map renders UK regions with color scale
- [ ] Rate trends shows multiple mortgage rate lines
- [ ] Transactions shows bar chart of volumes

#### Testing

Manual visual testing:
1. Compare each component to Figma design
2. Verify tooltips show correct values
3. Verify charts respond to time range filter

---

### Phase 8: Deep Dive Components

**Objective**: Implement secondary panels and complete UI.

#### Dependencies

- Phase 7 complete

#### Tasks

| # | Task | Files Created |
|---|------|---------------|
| 8.1 | Implement housing_composition panel | `app/components/panels/housing_composition.py` |
| 8.2 | Implement economic_context panel | `app/components/panels/economic_context.py` |
| 8.3 | Implement regional_spotlight panel | `app/components/panels/regional_spotlight.py` |
| 8.4 | Implement footer | `app/components/panels/footer.py` |
| 8.5 | Add sparkline charts | `app/components/charts/sparklines.py` |
| 8.6 | Add composition donut | `app/components/charts/composition.py` |

#### Files to Create

```
app/components/panels/__init__.py
app/components/panels/housing_composition.py
app/components/panels/economic_context.py
app/components/panels/regional_spotlight.py
app/components/panels/footer.py
app/components/charts/sparklines.py
app/components/charts/composition.py
```

#### Verification

- [ ] Housing composition panel shows property type breakdown
- [ ] Economic context shows CPI, employment, retail trends
- [ ] Regional spotlight allows region selection and detail view
- [ ] Footer displays data attribution
- [ ] Tab navigation works in composition panel

---

### Phase 9: Design Polish

**Objective**: Extract Figma design tokens and achieve visual parity with design.

#### Dependencies

- Phase 8 complete
- Access to Figma file via MCP

#### Tasks

| # | Task | Files Modified |
|---|------|----------------|
| 9.1 | Connect to Figma via MCP | (manual) |
| 9.2 | Extract color palette | `app/design_tokens.py` |
| 9.3 | Extract typography | `app/design_tokens.py` |
| 9.4 | Extract spacing | `app/design_tokens.py` |
| 9.5 | Update styles.css | `assets/styles.css` |
| 9.6 | Apply tokens to all charts | All chart components |
| 9.7 | Visual comparison and refinement | Multiple files |

#### Verification

- [ ] Colors match Figma design exactly
- [ ] Typography matches Figma specifications
- [ ] Spacing and layout match design
- [ ] Card shadows and borders match design
- [ ] Side-by-side comparison shows visual parity

---

### Phase 10: Testing and Documentation

**Objective**: Achieve comprehensive test coverage and complete documentation.

#### Dependencies

- Phase 9 complete

#### Tasks

| # | Task | Deliverable |
|---|------|-------------|
| 10.1 | Complete unit test coverage | >80% coverage |
| 10.2 | Write integration tests | Full pipeline tests |
| 10.3 | Performance testing | <3s load time verified |
| 10.4 | Update README.md | Complete documentation |
| 10.5 | Update CLAUDE.md | Accurate project guidance |
| 10.6 | Add docstrings | All public functions |
| 10.7 | Document resolved package versions | `requirements.txt` updated |

#### Verification

- [ ] `pytest --cov` shows >80% coverage
- [ ] `pytest tests/integration/` passes
- [ ] Initial load completes in <3 seconds
- [ ] README explains project and setup
- [ ] All public functions have docstrings

#### Testing Commands

```bash
# Run all tests with coverage
pytest --cov=app --cov=data --cov-report=html

# Run performance tests
pytest tests/integration/test_performance.py -v

# Type checking
mypy app data

# Code quality
black --check app data
isort --check-only app data
flake8 app data
```

---

### Phase 11: Deployment

**Objective**: Deploy to production and verify stability.

#### Dependencies

- Phase 10 complete

#### Tasks

| # | Task | Description |
|---|------|-------------|
| 11.1 | Prepare for Streamlit Cloud | Add `requirements.txt` to root |
| 11.2 | Configure secrets | Add API keys if needed |
| 11.3 | Deploy to Streamlit Cloud | Connect GitHub repo |
| 11.4 | Verify deployment | Test all features |
| 11.5 | Monitor for 24 hours | Check for errors |
| 11.6 | Document deployment | Add URL to README |

#### Verification

- [ ] Dashboard accessible at public URL
- [ ] All features work in production
- [ ] Data refreshes correctly
- [ ] No errors in logs after 24 hours
- [ ] URL added to portfolio

---

## 4. Critical Path

```
Phase 1 ──► Phase 2 ──► Phase 4 ──► Phase 5 ──► Phase 6 ──► Phase 7 ──► Phase 8 ──► Phase 9 ──► Phase 10 ──► Phase 11
               │
               └──► Phase 3 (can parallel with Phase 2)
```

**Critical Dependencies**:
- Phase 5 (Data Service) cannot start until Phases 2, 3, 4 complete
- Phase 9 (Design Polish) requires Figma MCP access
- Phase 11 (Deployment) requires all tests passing

---

## 5. Risk Mitigation

| Risk | Mitigation |
|------|------------|
| API behavior differs from docs | Write integration tests early, use fixtures |
| Rate limiting | Implement conservative client-side limits |
| Figma MCP unavailable | Use placeholder design tokens, polish later |
| Package incompatibilities | Let pip resolve, document working versions |
| Performance issues | Profile early, optimize caching strategy |

---

## 6. Post-Implementation

### Package Version Documentation

After `pip install -r requirements.txt`:

```bash
# Capture resolved versions
pip freeze > requirements-lock.txt

# Update architecture document with actual versions
```

### Maintenance Tasks

1. Monitor API endpoints for changes
2. Update cache schedules if publication dates change
3. Refresh design tokens if Figma design updates
4. Review and update dependencies quarterly

---

## Appendix A: Command Reference

```bash
# Development
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
streamlit run app/main.py

# Testing
pytest                           # Run all tests
pytest tests/unit/               # Run unit tests only
pytest -v -k "test_boe"         # Run specific tests
pytest --cov=app --cov=data     # Run with coverage

# Code Quality
black app data tests            # Format code
isort app data tests            # Sort imports
flake8 app data                 # Lint
mypy app data                   # Type check

# Cache Management
rm -rf storage/*                # Clear cache
```

---

## Appendix B: File Checklist

### Phase 1 Files
- [ ] `pyproject.toml`
- [ ] `requirements.txt`
- [ ] `.env.example`
- [ ] `.gitignore`
- [ ] `app/__init__.py`
- [ ] `app/config.py`
- [ ] `data/__init__.py`
- [ ] `data/exceptions.py`
- [ ] `data/models/__init__.py`
- [ ] `data/models/monetary.py`
- [ ] `data/models/housing.py`
- [ ] `data/models/economic.py`
- [ ] `data/models/cache.py`

### Phase 2 Files
- [ ] `data/clients/__init__.py`
- [ ] `data/clients/base.py`
- [ ] `data/clients/bank_of_england.py`
- [ ] `data/clients/land_registry.py`
- [ ] `data/clients/ons.py`

### Phase 3 Files
- [ ] `data/cache/__init__.py`
- [ ] `data/cache/scheduler.py`
- [ ] `data/cache/manager.py`

### Phase 4 Files
- [ ] `data/transformers/__init__.py`
- [ ] `data/transformers/base.py`
- [ ] `data/transformers/monetary.py`
- [ ] `data/transformers/housing.py`
- [ ] `data/transformers/economic.py`

### Phase 5 Files
- [ ] `app/services/__init__.py`
- [ ] `app/services/data_service.py`

### Phase 6 Files
- [ ] `app/main.py`
- [ ] `app/state.py`
- [ ] `app/design_tokens.py`
- [ ] `app/components/__init__.py`
- [ ] `app/components/filters.py`
- [ ] `assets/styles.css`

### Phase 7 Files
- [ ] `app/components/header.py`
- [ ] `app/components/hero_metrics.py`
- [ ] `app/components/charts/__init__.py`
- [ ] `app/components/charts/dual_axis.py`
- [ ] `app/components/charts/heat_map.py`
- [ ] `app/components/charts/rate_trends.py`
- [ ] `app/components/charts/transactions.py`

### Phase 8 Files
- [ ] `app/components/panels/__init__.py`
- [ ] `app/components/panels/housing_composition.py`
- [ ] `app/components/panels/economic_context.py`
- [ ] `app/components/panels/regional_spotlight.py`
- [ ] `app/components/panels/footer.py`
- [ ] `app/components/charts/sparklines.py`
- [ ] `app/components/charts/composition.py`

### Test Files
- [ ] `tests/__init__.py`
- [ ] `tests/conftest.py`
- [ ] `tests/unit/test_models/*.py`
- [ ] `tests/unit/test_clients/*.py`
- [ ] `tests/unit/test_cache/*.py`
- [ ] `tests/unit/test_transformers/*.py`
- [ ] `tests/integration/test_data_pipeline.py`
- [ ] `tests/fixtures/*.csv`
