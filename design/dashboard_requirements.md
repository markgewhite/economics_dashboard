# UK Housing & Economic Conditions Dashboard - Requirements Specification

## 1. Project Overview

### 1.0 Implementation Workflow

This project follows a design-first approach using Figma as the design source. The implementation workflow is:

**Phase 1: Design (Completed)**
1. ✅ Design brief created for Figma AI
2. ✅ Figma generates dashboard UI design
3. ✅ Design reviewed and approved

**Phase 2: Implementation (Current)**
1. Connect to Figma file via MCP server
2. Extract design specifications (colors, typography, spacing, layouts)
3. Implement data layer (API clients for BoE, Land Registry, ONS)
4. Build UI components matching Figma design exactly
5. Wire components together with data
6. Test and refine

**Phase 3: Deployment**
1. Deploy to hosting platform (Streamlit Cloud, Heroku, Railway)
2. Configure custom domain
3. Add to portfolio

**Key Documents**:
- `dashboard_requirements.md` (this file) - Architecture and functional requirements
- `api_integration_guide.md` - Complete API implementation details with code examples
- Figma design file - Visual design specifications (accessed via MCP)

### 1.1 Purpose
A web-based analytics dashboard that visualizes the relationship between UK monetary policy, housing markets, and economic indicators. This is a portfolio demonstration piece showcasing data science, data engineering, and full-stack development capabilities.

### 1.2 Target Users
- Potential employers evaluating technical capabilities
- Property investors and analysts
- Economic researchers
- Financial professionals interested in UK housing market trends

### 1.3 Success Criteria
- Loads and displays data from three external APIs (Bank of England, HM Land Registry, ONS)
- Updates data automatically on a defined schedule
- Provides interactive filtering by time range and geographic region
- Renders correctly on desktop browsers (Chrome, Firefox, Safari, Edge)
- Demonstrates professional code quality and architecture
- Deploys to a public URL for portfolio sharing

## 2. Functional Requirements

### 2.1 Core Features

#### 2.1.1 Data Display
- **Hero Metrics**: Display four key metrics with current values and change indicators
  - Bank of England Base Rate
  - 2-Year Fixed Mortgage Rate
  - UK Average House Price
  - CPI Inflation Rate
  
- **Main Visualizations**:
  - Dual-axis line chart showing interest rates vs. house prices over time
  - UK regional heat map showing house price changes by geographic area
  - Multi-line chart showing base rate and mortgage rate trends
  - Bar chart showing monthly transaction volumes
  - Compact display of three economic indicators (CPI, Employment, Retail Sales)

- **Deep Dive Panels**:
  - Housing market composition breakdown (by property type, buyer status, payment method)
  - Economic context trends (GDP, unemployment, business confidence)
  - Regional spotlight allowing detailed exploration of specific areas

#### 2.1.2 Interactive Controls
- **Time Range Selector**: Toggle between 6 months, 1 year, 2 years, 5 years, and all available data
- **Region Filter**: Dropdown to select specific UK regions for detailed analysis
- **Tab Navigation**: Switch between different views in composition panel
- **Chart Interactions**: Hover tooltips showing precise values, clickable legends

#### 2.1.3 Data Management
- **Initial Load**: Check cache for current data; fetch only if refresh is needed
- **Intelligent Refresh**: System tracks expected update times for each dataset and fetches only when new data should be available
- **Manual Refresh**: Button to force immediate data fetch regardless of schedule
- **Smart Caching**: Store fetched data with metadata about next expected update
- **Data Validation**: Verify data integrity and handle missing/malformed data gracefully

#### 2.1.4 User Feedback
- **Loading States**: Show loading indicators during data fetches
- **Error States**: Display user-friendly error messages if data fails to load
- **Last Updated Timestamp**: Show when data was last refreshed
- **Empty States**: Handle cases where no data is available for selected filters

### 2.2 Non-Functional Requirements

#### 2.2.1 Performance
- Initial page load: < 3 seconds on broadband connection
- Data refresh: < 2 seconds for cached data updates
- Chart rendering: < 500ms after data updates
- Smooth interactions: 60fps for animations and transitions

#### 2.2.2 Reliability
- Graceful degradation if one API source fails (show available data)
- Retry logic for failed API requests (exponential backoff)
- Fallback to cached data if refresh fails
- No data loss on network interruptions

#### 2.2.3 Maintainability
- Modular code structure with clear separation of concerns
- Comprehensive inline documentation
- Type safety (TypeScript or Python type hints)
- Automated linting and formatting
- Unit tests for data transformation logic

#### 2.2.4 Accessibility
- Keyboard navigation support
- Screen reader compatible
- WCAG 2.1 AA compliance for color contrast
- Alternative text for all visualizations
- Semantic HTML structure

#### 2.2.5 Browser Compatibility
- Chrome/Edge (latest 2 versions)
- Firefox (latest 2 versions)
- Safari (latest 2 versions)
- Minimum viewport width: 1024px (desktop-first approach)

## 3. Technical Architecture

### 3.0 Figma Design Integration

#### 3.0.1 Design Source
The UI design has been created in Figma using the design brief provided. The implementation must match this design accurately.

#### 3.0.2 Figma MCP Server Integration
Claude Code will use the Figma MCP server to:

**Extract Design Tokens**:
- Access the Figma file containing the dashboard design
- Extract color palette (primary, secondary, chart colors, backgrounds)
- Extract typography system (font families, sizes, weights, line heights)
- Extract spacing values (padding, margins, gaps between components)
- Extract effects (shadows, border radius, hover states)

**Get Layout Specifications**:
- Component dimensions (card heights, chart containers)
- Grid structure (column widths, gutters)
- Element positioning and alignment
- Responsive breakpoint values (if defined)

**Component Details**:
- Hero metrics card layout (icon size, value size, spacing)
- Chart container specifications (padding, header styles)
- Button styles (primary, secondary, hover states)
- Dropdown designs (border, padding, arrow icon)
- Tooltip designs (background, border, shadow)

#### 3.0.3 Design-to-Code Workflow

**Step 1: Connect to Figma**
- Access the Figma file via MCP
- Identify the main dashboard frame/page
- Confirm all components are visible

**Step 2: Extract Design System**
- Generate CSS variables or Python constants for:
  - Color palette
  - Typography scale
  - Spacing system
  - Effects (shadows, borders)

**Step 3: Component Mapping**
- Map each Figma component to code implementation
- Hero Metrics → Streamlit columns with custom CSS
- Charts → Plotly figures with matching colors
- Filters → Streamlit widgets with custom styling

**Step 4: Apply Styles**
- Use extracted design tokens throughout application
- Create custom CSS to match Figma design
- Ensure visual consistency across all components

#### 3.0.4 Design Token Requirements

The system shall extract and store design specifications from Figma in a structured format that can be referenced throughout the implementation.

**Required Design Token Categories:**

**Colors:**
- Primary, secondary, and accent colors
- Background and surface colors
- Text colors (primary, secondary, muted)
- Success, warning, and danger indicator colors
- Chart colors (multiple colors for multi-series charts)
- Border and divider colors

**Typography:**
- Font family specifications
- Font size hierarchy (H1, H2, body, caption, etc.)
- Font weights (regular, medium, bold)
- Line heights for each text size
- Letter spacing where specified

**Spacing:**
- Base spacing unit
- Component padding values
- Section gaps and margins
- Card padding specifications
- Grid gutters

**Visual Effects:**
- Shadow specifications for cards and elevated elements
- Border radius values for different component types
- Border widths and styles
- Opacity values for hover and disabled states

**Component Dimensions:**
- Hero metric card dimensions
- Chart container sizes
- Button heights and widths
- Input field specifications

The extracted tokens shall be stored in a format that allows:
- Easy reference during component development
- Consistency across all dashboard elements
- Simple updates if design specifications change
- Clear mapping between Figma design and implementation

#### 3.0.5 Maintaining Design Consistency

**During Development**:
- Reference Figma file frequently for visual verification
- Use extracted tokens rather than hardcoding values
- Take screenshots of Figma design for comparison during testing
- Iterate on styling until match is achieved

**If Design Updates**:
- Re-extract tokens from updated Figma file
- Update design token constants
- Rebuild affected components
- Maintain version tracking of design iterations

### 3.1 Technology Stack Recommendations

#### 3.1.1 Backend/Data Layer (Python)
- **Framework**: Flask or FastAPI for API endpoints (if needed)
- **Data Processing**: Pandas for data transformation and aggregation
- **API Clients**: Requests library for HTTP calls
- **Caching**: Redis or simple file-based caching
- **Scheduling**: APScheduler for periodic data updates
- **Configuration**: python-dotenv for environment variables

#### 3.1.2 Frontend (Python Web Framework)
- **Framework**: Streamlit, Dash, or Plotly Dash
  - Streamlit: Fastest development, good for demos
  - Dash: More control over layout, better for complex interactions
  - Alternative: Flask + vanilla JavaScript + Plotly.js

- **Visualization**: Plotly for interactive charts
- **State Management**: Framework's built-in state handling
- **Styling**: Custom CSS to match Figma design

#### 3.1.3 Deployment
- **Platform**: Streamlit Community Cloud (free), Heroku, or Railway
- **CI/CD**: GitHub Actions for automated deployment
- **Monitoring**: Application logs and health checks
- **Domain**: Custom subdomain or free platform URL

### 3.2 Application Structure

```
uk-economic-dashboard/
├── app/
│   ├── __init__.py
│   ├── main.py                 # Application entry point
│   ├── config.py               # Configuration settings
│   └── components/             # UI components
│       ├── __init__.py
│       ├── hero_metrics.py     # Hero metrics cards
│       ├── charts.py           # Chart components
│       └── filters.py          # Interactive controls
├── data/
│   ├── __init__.py
│   ├── clients/                # API client modules
│   │   ├── __init__.py
│   │   ├── bank_of_england.py
│   │   ├── land_registry.py
│   │   └── ons.py
│   ├── transformers/           # Data transformation logic
│   │   ├── __init__.py
│   │   ├── monetary.py         # BoE data transformations
│   │   ├── housing.py          # Housing data transformations
│   │   └── economic.py         # Economic indicators
│   └── cache/                  # Cached data storage
│       ├── raw/                # Raw API responses
│       └── processed/          # Processed data
├── tests/
│   ├── test_clients.py
│   ├── test_transformers.py
│   └── test_components.py
├── assets/
│   ├── styles.css              # Custom styling
│   └── images/                 # Icons, logos
├── docs/
│   ├── api_integration.md      # API documentation
│   └── deployment.md           # Deployment guide
├── .env.example                # Example environment variables
├── .gitignore
├── requirements.txt            # Python dependencies
└── README.md                   # Project documentation
```

### 3.3 Data Flow

The dashboard shall implement the following data flow sequence:

**1. Dashboard Initialization**
   - User opens dashboard or clicks refresh
   - System checks local cache for each required dataset
   - For each dataset, system loads associated metadata if available

**2. Refresh Decision Logic**
   - System evaluates whether each dataset requires refresh based on:
     - Last fetch timestamp from cache metadata
     - Known publication schedule for that data source
     - Current date and time (UK timezone)
     - Whether today is a business day (for daily updates)
   - Decision outcomes:
     - Refresh needed: New data should be available based on schedule
     - Cache current: Last fetch was after most recent expected update
     - No cache: First time fetch required

**3. Data Acquisition**
   - For datasets requiring refresh:
     - Fetch data from respective API endpoints in parallel
     - Handle network errors with retry logic (3 attempts, exponential backoff)
     - Fall back to stale cache if fetch fails
   - For current cached datasets:
     - Load data immediately from local storage
     - No API calls required

**4. Data Transformation**
   - Parse API responses (CSV, JSON formats)
   - Calculate derived metrics (year-over-year changes, percentage changes)
   - Align time series to consistent frequencies
   - Handle missing values through interpolation or forward-fill
   - Validate data quality and completeness

**5. Cache Update**
   - Store transformed data to local cache
   - Write metadata including:
     - Fetch timestamp
     - Next expected update timestamp
     - Reason for refresh/cache decision
     - Record count for validation
   - Set file permissions appropriately

**6. Dashboard Rendering**
   - Generate interactive charts using plotting library
   - Apply user-selected filters (time range, region)
   - Display hero metrics with latest values
   - Show data freshness indicators
   - Enable interactive elements (hover, drill-down)

**7. User Interaction Handling**
   - Filter changes: Re-render affected components without data refetch
   - Manual refresh: Force immediate fetch of all sources regardless of schedule
   - Chart interactions: Display tooltips and details without data refetch

### 3.4 State Management

#### 3.4.1 Application State
- **Current Filters**: Time range (default: 1 year), Region (default: United Kingdom)
- **Data Cache**: Raw and processed data with timestamps
- **Loading States**: Per-component loading indicators
- **Error States**: Error messages and retry mechanisms

#### 3.4.2 State Flow
```
Initial State
  ├── filters: { timeRange: "1Y", region: "UK" }
  ├── data: null
  ├── loading: true
  └── error: null

After Data Load
  ├── filters: { timeRange: "1Y", region: "UK" }
  ├── data: { monetary, housing, economic }
  ├── loading: false
  └── error: null

After Filter Change
  ├── filters: { timeRange: "2Y", region: "UK" }  ← Updated
  ├── data: { monetary, housing, economic }        ← Filtered in-memory
  ├── loading: false
  └── error: null
```

## 4. Component Specifications

### 4.1 Hero Metrics Component
**Purpose**: Display four key economic indicators with change indicators

**Inputs**:
- Current values (Bank Rate, Mortgage Rate, House Price, Inflation)
- Previous values (for calculating change)

**Outputs**:
- Four metric cards with icon, label, value, change percentage, change direction

**Logic**:
- Calculate percentage change: `(current - previous) / previous * 100`
- Determine direction: positive (↑ green), negative (↓ red), neutral (→ gray)
- Format currency values: £296,000
- Format percentages: 4.75%

### 4.2 Interest Rates & House Prices Chart
**Purpose**: Show correlation between monetary policy and housing market

**Inputs**:
- Time series data: dates, bank rates, average house prices
- Time range filter

**Outputs**:
- Dual-axis line chart (Plotly)

**Logic**:
- Filter data to selected time range
- Normalize axes to show proportional changes
- Add hover tooltips with both values
- Highlight key events (rate changes) with annotations

### 4.3 Regional Heat Map
**Purpose**: Visualize geographic variation in house price changes

**Inputs**:
- Regional house price data by area code
- Most recent month's data

**Outputs**:
- Choropleth map of UK regions

**Logic**:
- Calculate YoY percentage change per region
- Map region codes to geographic boundaries
- Color scale: Red (negative) → White (0%) → Green (positive)
- Interactive: Click region to update "Regional Spotlight" panel

### 4.4 Time Range Selector
**Purpose**: Filter all time-based visualizations

**Inputs**:
- Available data date range
- Current selection

**Outputs**:
- Button group with selected state

**Logic**:
- On selection change: Update application state
- Trigger re-render of affected components
- Persist selection in URL query params (optional)

### 4.5 Region Filter Dropdown
**Purpose**: Filter data to specific geographic areas

**Inputs**:
- List of available regions from HM Land Registry
- Current selection

**Outputs**:
- Dropdown with hierarchical options (National → Regional → Local)

**Logic**:
- On selection change: Update application state
- Filter housing data to selected region
- Update relevant charts (heat map becomes detail view)

## 5. Data Requirements

### 5.1 Minimum Viable Dataset

#### 5.1.1 Monetary Policy Data (Bank of England)
- Bank Rate: Daily values, last 5 years
- SONIA benchmark: Daily values, last 5 years
- 2-year fixed mortgage rate: Monthly averages, last 5 years
- 5-year fixed mortgage rate: Monthly averages, last 5 years
- GBP/USD exchange rate: Monthly averages, last 5 years

#### 5.1.2 Housing Market Data (HM Land Registry)
- Average house prices: Monthly, all regions, last 5 years
- House price index: Monthly, all regions, last 5 years
- Transaction volumes: Monthly, all regions, last 5 years (excluding most recent 2 months)
- Breakdown by property type: Detached, semi-detached, terraced, flat

#### 5.1.3 Economic Indicators (ONS)
- CPI inflation: Monthly, last 5 years
- Employment rate: Monthly, last 5 years
- Retail sales index: Monthly, last 5 years

### 5.2 Data Update Frequency & Intelligent Refresh

#### 5.2.1 Source Update Schedules

**Bank of England**:
- **Exchange rates** (GBP/USD, GBP/EUR): Daily at 9:30 AM UK time (weekdays only)
- **SONIA benchmark**: Daily by noon next business day (weekdays only)
- **Bank Rate**: As announced (irregular, typically quarterly)
- **Mortgage rates** (2yr, 5yr): Monthly around mid-month

**HM Land Registry**:
- **House prices & index**: Monthly on 20th working day of month at ~9:30 AM
- **Transaction volumes**: Monthly (but suppressed for most recent 2 months)

**ONS**:
- **CPI inflation**: Monthly around 15th at 7:00 AM UK time
- **Employment rate**: Monthly around 15th at 7:00 AM UK time
- **Retail sales**: Monthly around 20th at 7:00 AM UK time

#### 5.2.2 Intelligent Refresh Strategy

The dashboard shall implement a schedule-aware refresh mechanism that determines when to fetch new data based on known publication schedules rather than arbitrary time intervals.

**Refresh Schedule Configuration Requirements:**

The system shall maintain configuration for each data source specifying:
- **Monetary data (Bank of England)**:
  - Update frequency: Daily
  - Publication time: 09:30 UK time
  - Check window: After 10:00 UK time (30-minute buffer)
  - Availability: Weekdays only (no weekend updates)

- **Housing data (HM Land Registry)**:
  - Update frequency: Monthly
  - Publication day: 20th working day of each month
  - Check window: After 15:00 UK time on publication day
  - Availability: Working days only

- **Economic data (ONS)**:
  - Update frequency: Monthly
  - Publication day: Approximately 15th of each month
  - Check window: After 12:00 UK time on publication day
  - Availability: Working days only

**Daily Refresh Decision Logic:**

For datasets with daily updates, the system shall:
1. Check if today is a weekday (if weekend updates are disabled)
2. Compare last fetch date with current date
3. If dates match, return "already current" - no refresh needed
4. If dates differ, check current time against configured check window
5. If before check window, return "before check time" - no refresh needed
6. If after check window and weekday, return "refresh needed" with reason "daily update expected"

**Monthly Refresh Decision Logic:**

For datasets with monthly updates, the system shall:
1. Compare last fetch month/year with current month/year
2. If months match, return "already current" - no refresh needed
3. If months differ, check if current day >= configured publication day
4. If before publication day, return "before release day" - no refresh needed
5. If on or after publication day, check current time against configured check window
6. If before check window, return "before check time" - no refresh needed
7. If after check window, return "refresh needed" with reason "monthly update expected"

**Next Expected Update Calculation:**

The system shall calculate and store the next expected update timestamp for each dataset:
- **Daily updates**: Next business day at configured check time (skip weekends)
- **Monthly updates**: Next month's publication day at configured check time
  - If current day >= publication day: Calculate for following month
  - If current day < publication day: Calculate for current month

**Refresh Decision Outcomes:**

Each refresh decision shall return:
- Boolean flag: Whether refresh is needed
- Reason code: Machine-readable reason (e.g., "daily_update_expected", "already_current", "weekend_no_update")
- This information shall be logged for monitoring and stored with cache metadata

**Benefits of This Approach:**

This intelligent refresh strategy provides:
- Minimized unnecessary API calls (respect for free public APIs)
- Faster dashboard load times when data is already current
- Guaranteed freshness when new data becomes available
- Transparent behavior through logged decision reasons
- Predictable load patterns on data sources

#### 5.2.3 Cache Metadata Structure

The system shall store metadata alongside each cached dataset to support intelligent refresh decisions and provide transparency to users.

**Required Metadata Fields:**

Each cached dataset shall have associated metadata containing:
- **dataset**: Identifier for the data source (e.g., "monetary", "housing", "economic")
- **last_fetch**: ISO 8601 timestamp of when data was last retrieved from API
- **next_expected**: ISO 8601 timestamp of when next update is expected based on publication schedule
- **data_date**: Date string representing the latest data point in the dataset (e.g., "2026-01-08")
- **refresh_reason**: Machine-readable code explaining why refresh occurred or cache was used
- **record_count**: Integer count of records in dataset for validation purposes

**Metadata Storage Requirements:**

- Metadata shall be stored in JSON format alongside cached data files
- File naming convention: `{dataset}_meta.json` paired with `{dataset}_data.csv`
- Timestamps shall use ISO 8601 format with timezone information
- Metadata shall be updated atomically when cache is written
- System shall handle missing metadata gracefully (treat as no cache available)

**Metadata Usage:**

The metadata shall be used to:
- Make refresh decisions without loading full dataset
- Display data freshness information to users
- Calculate next expected update timestamp
- Validate cache integrity (record count check)
- Log refresh behavior for monitoring
- Support debugging and troubleshooting

**Refresh Reason Codes:**

The system shall use standardized reason codes including:
- `initial_fetch`: First time fetching this dataset
- `forced_refresh`: User manually triggered refresh
- `daily_update_expected`: Daily schedule indicates new data available
- `monthly_update_expected`: Monthly schedule indicates new data available
- `already_current`: Data fetched after most recent expected update
- `cached_weekend_no_update`: Weekend access, no updates published
- `cached_before_check_time`: Before scheduled check window
- `cached_before_release_day`: Before monthly publication day
- `cached_current_month_fetched`: Already have current month's data

#### 5.2.4 User Experience Requirements

**Fast Path (Current Data):**

When cached data is current and no refresh is needed:
- Dashboard shall load in under 500 milliseconds
- System shall display cached data immediately without API calls
- User shall see indicator: "Data current as of [timestamp]" where timestamp shows last fetch time
- No loading spinner or delay shall be presented to user

**Refresh Path (New Data Available):**

When refresh decision indicates new data should be available:
- Dashboard shall display cached data immediately while fetching updates in background
- Loading indicator shall show: "Checking for updates..." during API calls
- Upon successful fetch, display shall update with message: "Updated to [new date]"
- Total time from load to updated display: 2-5 seconds depending on API response times
- If fetch fails, cached data remains visible with warning indicator

**Manual Refresh Path (User-Initiated):**

When user clicks manual refresh button:
- System shall force immediate fetch of all data sources regardless of schedule
- Loading indicator shall show: "Refreshing all data sources..."
- User shall see which datasets were actually updated vs. remained unchanged
- Use cases supported: checking for unexpected updates, debugging, demonstration purposes
- Completion message shall list refreshed sources: "Updated: monetary, housing" or "All data was already current"

**Data Freshness Transparency:**

The dashboard shall always display:
- Last update timestamp for each dataset or aggregate "Data last updated: [timestamp]"
- Next expected update: "Next update expected: [timestamp]" 
- Time elapsed since last update: e.g., "Updated 2 hours ago"
- Clear distinction between "current" (after expected update) and "stale" (refresh failed) states

**Error State Handling:**

When data refresh fails:
- Display stale cached data with prominent warning
- Show message: "Unable to fetch latest data. Showing cached data from [timestamp]"
- Provide manual refresh option to retry
- Do not hide information or show empty state if cached data exists

### 5.3 Data Validation Rules
- All date fields must be valid ISO 8601 format
- Numeric values must be non-negative (prices, rates, volumes)
- Missing values: Use forward fill for continuous series
- Outliers: Flag values > 3 standard deviations from mean
- Data completeness: Require 95%+ of expected data points

## 6. Error Handling

### 6.1 API Errors

#### 6.1.1 Network Errors
- **Symptom**: Connection timeout, DNS failure
- **Handling**: Retry 3 times with exponential backoff (1s, 2s, 4s)
- **User Feedback**: "Connecting to data sources..."
- **Fallback**: Load cached data if available

#### 6.1.2 HTTP Errors
- **4xx Client Errors**: Log error, display message to user
- **429 Rate Limit**: Wait for `Retry-After` header duration
- **5xx Server Errors**: Retry with backoff, fallback to cache
- **User Feedback**: "Data temporarily unavailable. Showing cached data from [timestamp]"

#### 6.1.3 Data Format Errors
- **Symptom**: Unexpected JSON structure, malformed CSV
- **Handling**: Log detailed error, skip problematic records
- **User Feedback**: "Some data could not be loaded. Partial results shown."
- **Fallback**: Display available data, hide broken components

### 6.2 Application Errors

#### 6.2.1 Rendering Errors
- **Symptom**: Chart fails to render, component crashes
- **Handling**: Error boundary catches exception
- **User Feedback**: "This chart is temporarily unavailable"
- **Logging**: Send error to console with stack trace

#### 6.2.2 Data Transformation Errors
- **Symptom**: NaN values, division by zero, type mismatches
- **Handling**: Validate data at transformation boundaries
- **User Feedback**: Exclude invalid data points, show warning icon
- **Logging**: Log specific transformation failures

## 7. Performance Optimization

### 7.1 Data Loading
- **Parallel API Requests**: Fetch all sources simultaneously
- **Lazy Loading**: Load deep dive panels only when visible
- **Data Pagination**: Limit initial dataset to selected time range

### 7.2 Rendering
- **Debounce Interactions**: 300ms delay on filter changes
- **Virtual Scrolling**: For large data tables (if implemented)
- **Chart Optimization**: Reduce data points for long time series (e.g., weekly aggregates for 5-year view)

### 7.3 Caching Strategy
- **L1 Cache**: In-memory application cache (lasts while app runs)
- **L2 Cache**: File-based or Redis cache with metadata
- **Cache Keys**: Include dataset name and data date
- **Cache Metadata**: Store last fetch time, next expected update, refresh reason
- **Intelligent Invalidation**: Based on update schedules, not time-based expiry
- **Fallback**: Use stale cache if refresh fails (show warning to user)

## 8. Testing Requirements

### 8.1 Unit Tests
- Data client functions (API calls return expected structure)
- Data transformation functions (correct calculations, handles edge cases)
- Date range filtering (correct subset of data)
- Percentage change calculations (positive, negative, zero cases)

### 8.2 Integration Tests
- End-to-end API fetch → transform → cache pipeline
- Filter changes propagate to all components
- Error handling triggers correct fallback behavior

### 8.3 Manual Testing Checklist
- [ ] Dashboard loads within 3 seconds
- [ ] All four hero metrics display correctly
- [ ] Main chart shows data for selected time range
- [ ] Heat map renders all UK regions
- [ ] Time range selector updates charts
- [ ] Region filter updates relevant data
- [ ] Refresh button fetches new data
- [ ] Hover tooltips show correct values
- [ ] Error states display when API unavailable
- [ ] Mobile/tablet view renders acceptably (if responsive)

## 9. Deployment

### 9.1 Environment Variables
```
# API Configuration
BOE_API_BASE_URL=https://www.bankofengland.co.uk/boeapps/database
LAND_REGISTRY_API_BASE_URL=http://landregistry.data.gov.uk
ONS_API_BASE_URL=https://api.beta.ons.gov.uk/v1

# Cache Configuration
CACHE_BACKEND=file  # or redis
CACHE_DIR=./data/cache

# Refresh Configuration (override defaults if needed)
MONETARY_CHECK_TIME=10:00
HOUSING_CHECK_TIME=15:00
ECONOMIC_CHECK_TIME=12:00
ENABLE_INTELLIGENT_REFRESH=true

# Application Configuration
PORT=8501
LOG_LEVEL=INFO
TIMEZONE=Europe/London
```

### 9.2 Deployment Checklist
- [ ] Environment variables configured
- [ ] Dependencies installed (requirements.txt)
- [ ] Health check endpoint implemented
- [ ] Error logging configured
- [ ] Production mode enabled (debug=False)
- [ ] Custom domain configured (if applicable)
- [ ] SSL certificate enabled (HTTPS)
- [ ] Analytics tracking added (optional)

### 9.3 Monitoring
- **Application Health**: HTTP 200 response from root URL
- **Data Freshness**: Check cache metadata for last update and next expected
- **Refresh Decisions**: Log each refresh decision (refresh/cache) with reason
- **Error Rate**: Log 5xx errors and exceptions
- **Performance**: Track page load time and data fetch duration
- **Cache Hit Rate**: Monitor percentage of loads that use cached data

## 10. Future Enhancements (Out of Scope for MVP)

### 10.1 Phase 2 Features
- Export data as CSV/Excel
- Email alerts for significant changes (e.g., rate changes)
- Historical scenario comparisons ("What if rates stayed at X%?")
- User-created custom regions (postcode areas)
- Annotation tools for saving insights

### 10.2 Technical Improvements
- Backend API for better performance
- Database for faster queries (PostgreSQL + TimescaleDB)
- Real-time WebSocket updates
- Mobile-responsive design
- Progressive Web App (PWA) capabilities

### 10.3 Data Expansions
- Rental market data
- Commercial property data
- International comparisons (US, EU markets)
- Mortgage application volumes
- First-time buyer statistics

## 11. Documentation Requirements

### 11.1 Code Documentation
- Docstrings for all functions and classes
- Inline comments for complex logic
- Type hints for function signatures

### 11.2 User Documentation
- README with project overview
- Quick start guide
- Interpretation guide (how to read the dashboard)

### 11.3 Developer Documentation
- Architecture overview diagram
- API integration guide (separate document)
- Deployment instructions
- Troubleshooting guide

## 12. Acceptance Criteria

The dashboard is considered complete when:

1. **Functional**:
   - [ ] All three data sources successfully integrated
   - [ ] All specified charts render with real data
   - [ ] Time range and region filters work correctly
   - [ ] Manual refresh updates data

2. **Performance**:
   - [ ] Initial load < 3 seconds
   - [ ] Data refresh < 2 seconds
   - [ ] No lag in interactions

3. **Quality**:
   - [ ] Code is properly structured and documented
   - [ ] Error handling is comprehensive
   - [ ] Design matches Figma mockup
   - [ ] Accessible via keyboard navigation

4. **Deployment**:
   - [ ] Deployed to public URL
   - [ ] Application remains stable for 24+ hours
   - [ ] Data updates automatically

5. **Portfolio Ready**:
   - [ ] README explains project and technologies
   - [ ] Code is in public GitHub repository
   - [ ] Link works in portfolio website
   - [ ] Demonstrates technical competence to recruiters

## 13. Figma MCP Integration Guide

### 13.1 Accessing the Figma Design

**Step 1: Connect to Figma**
When starting implementation with Claude Code, first establish connection to the Figma file:

```
"Connect to my Figma design file for the UK Economic Dashboard"
```

**Step 2: Verify Design Access**
Confirm Claude Code can see the design:

```
"List all frames and components in the dashboard design"
"Show me the main dashboard layout"
```

### 13.2 Extracting Design Specifications

**Colors**:
```
"Extract the complete color palette from the Figma design"
"What colors are used for positive/negative indicators?"
"Get the background color, primary color, and chart colors"
```

**Typography**:
```
"What fonts and sizes are used in the design?"
"Extract typography specifications for headers, body text, and metric values"
```

**Spacing & Layout**:
```
"What are the spacing values between components?"
"Get the dimensions of the hero metrics section"
"What padding is used in the chart cards?"
```

**Components**:
```
"Extract specifications for the hero metrics cards"
"Get the button styles (primary and secondary)"
"What are the dropdown menu specifications?"
```

### 13.3 Implementation Requirements from Figma Specs

Once design tokens are extracted from Figma, the implementation shall:

**1. Create Centralized Design Constants**

Extracted design specifications shall be stored in a centralized location that:
- Contains all color values in hexadecimal format
- Includes all typography specifications (families, sizes, weights, line heights)
- Defines spacing values with clear naming conventions
- Documents visual effects (shadows, borders, radii)
- Can be imported and referenced by any component
- Includes comments indicating values were extracted from Figma

**2. Apply Design Tokens to Components**

Each UI component shall:
- Reference centralized design constants rather than hard-coded values
- Use extracted colors for backgrounds, text, and interactive states
- Apply typography specifications consistently across all text elements
- Use spacing values from design tokens for padding, margins, and gaps
- Implement visual effects (shadows, borders) exactly as specified in Figma

**3. Style Custom Components**

For custom styling requirements:
- Apply extracted color palette to custom CSS or styling
- Use typography specifications for font families and sizes
- Apply spacing values consistently in custom layouts
- Ensure hover states, active states, and disabled states match Figma specifications
- Maintain responsive behavior as indicated in design

**4. Configure Chart Styling**

Charts shall be styled to match Figma specifications:
- Use extracted colors for chart series, axes, and gridlines
- Apply typography tokens to axis labels, titles, and tooltips
- Match chart dimensions to specifications in design
- Use consistent border radius and shadow effects on chart containers
- Ensure color accessibility for positive/negative indicators

### 13.4 Visual Verification Process

**During Implementation**:
1. Take screenshots of Figma design for reference
2. Build component in code
3. Compare rendered output with Figma design
4. Adjust until match is achieved
5. Repeat for each component

**Prompts for Verification**:
```
"Does this component match the Figma design?"
"Compare the current hero metrics with the Figma version"
"What differences are there between my implementation and the design?"
```

### 13.5 Handling Design Updates

If the Figma design is modified:
1. Re-extract affected design tokens
2. Update design_tokens.py constants
3. Rebuild affected components
4. Test for visual consistency

### 13.6 Common Figma MCP Commands

```
# Access
"Open the UK Economic Dashboard Figma file"
"Switch to the Dashboard frame"

# Inspect
"What's the width of the hero metrics section?"
"Show me the shadow effect on the cards"
"What icon is used for the Bank Rate metric?"

# Extract
"Get all color values used in the design"
"Export the typography scale as JSON"
"List all spacing values (padding, margins, gaps)"

# Compare
"Does my current layout match the Figma design?"
"Compare this chart with the Figma version"
```

### 13.7 Design Token Export Format

Request design tokens in structured format:

```
"Export design tokens as Python dictionary"
"Create a JSON file with all color, typography, and spacing values"
```

Expected output structure:
```python
{
    "colors": {
        "primary": {"value": "#1E3A8A", "usage": "Main brand color, headers"},
        "secondary": {"value": "#3B82F6", "usage": "Interactive elements"},
        # ...
    },
    "typography": {
        "heading_1": {
            "font_family": "Inter",
            "font_size": "32px",
            "font_weight": "700",
            "line_height": "1.2",
            "usage": "Page title"
        },
        # ...
    },
    "spacing": {
        "card_padding": {"value": "24px", "usage": "Interior padding for cards"},
        "section_gap": {"value": "24px", "usage": "Space between sections"},
        # ...
    }
}
```

### 13.8 Implementation Checklist with Figma

- [ ] Connect to Figma design file
- [ ] Extract complete color palette
- [ ] Extract typography specifications  
- [ ] Extract spacing system
- [ ] Extract component dimensions
- [ ] Create design_tokens.py file
- [ ] Apply colors to all components
- [ ] Apply typography to text elements
- [ ] Apply spacing throughout layout
- [ ] Match shadows, borders, and effects
- [ ] Verify each component visually against Figma
- [ ] Test hover states and interactions
- [ ] Ensure responsive behavior matches design (if specified)

---

**Document Version**: 1.0  
**Last Updated**: January 2026  
**Author**: Project Requirements  
**Next Steps**: Connect to Figma via MCP, extract design tokens, then proceed with implementation following the API Integration Guide
