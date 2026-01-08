# UK Housing & Economic Dashboard - API Integration Guide

## Document Purpose

This guide documents the API interfaces for three UK public data sources required for the economic dashboard. It specifies endpoints, request/response formats, authentication requirements, rate limits, and data schemas. Implementation details are intentionally excluded - this document serves as a reference for understanding the external data sources.

---

## 1. Bank of England Statistical Interactive Database (IADB)

### 1.1 API Overview

**Base URL**: `https://www.bankofengland.co.uk/boeapps/database/_iadb-fromshowcolumns.asp`

**API Type**: URL-based query interface (not REST)

**Authentication**: None required

**Rate Limits**: None documented (recommend respectful usage: ~1 request per 2-3 seconds)

**Data Format**: CSV, XML, or Excel (CSV recommended for programmatic access)

**Update Schedule**:
- Exchange rates (GBP/USD, GBP/EUR): Daily at 9:30 AM UK time
- SONIA benchmark: Daily by noon next business day
- Bank Rate: As announced (typically quarterly, irregular)
- Mortgage rates (2yr, 5yr): Monthly (mid-month)

**Important Notes**:
- Requests **must** include User-Agent header or server returns 500 error
- Missing values are represented as ".." in CSV output
- Weekend and bank holiday data is typically missing (no weekend updates)

### 1.2 Required Data Series

The following series codes provide the monetary policy data needed for the dashboard:

| Series Code | Description | Frequency | Typical Lag |
|-------------|-------------|-----------|-------------|
| `IUDBEDR` | Bank Rate (Official Bank Rate) | Irregular | None (same day) |
| `IUDSOIA` | SONIA (Sterling Overnight Index Average) | Daily | 1 business day |
| `IUMBV34` | 2-year fixed rate mortgage (75% LTV) | Monthly | ~15 days |
| `IUMBV42` | 5-year fixed rate mortgage (75% LTV) | Monthly | ~15 days |
| `XUDLUSS` | GBP/USD spot exchange rate | Daily | Same day by 16:00 |
| `XUDLERS` | GBP/EUR spot exchange rate | Daily | Same day by 16:00 |

**How to discover additional series codes**:
1. Navigate to https://www.bankofengland.co.uk/boeapps/database/
2. Browse to desired dataset category
3. Select series and click "Download data"
4. Inspect URL parameters for series codes

### 1.3 Request Specification

**HTTP Method**: GET

**Required Parameters**:
- `Datefrom` - Start date in format DD/Mon/YYYY (e.g., "01/Jan/2020")
- `Dateto` - End date in format DD/Mon/YYYY (e.g., "31/Dec/2024")
- `SeriesCodes` - Comma-separated series codes (no spaces)
- `CSVF` - Set to "TN" for CSV with series names as headers
- `UsingCodes` - Set to "Y" to use series codes
- `VPD` - Set to "Y"
- `VFD` - Set to "N"

**Example Request**:
```
GET https://www.bankofengland.co.uk/boeapps/database/_iadb-fromshowcolumns.asp?Datefrom=01/Jan/2020&Dateto=31/Dec/2024&SeriesCodes=IUDBEDR,IUDSOIA,XUDLUSS&CSVF=TN&UsingCodes=Y&VPD=Y&VFD=N

Headers:
  User-Agent: UK-Economic-Dashboard/1.0
```

### 1.4 Response Format

**Content-Type**: text/csv

**Structure**:
- First column: `DATE` in format "DD Mon YYYY" (e.g., "01 Jan 2024")
- Subsequent columns: One column per requested series code
- Column headers: Series codes as specified in request
- Missing values: Represented as ".."

**Example Response**:
```csv
DATE,IUDBEDR,IUDSOIA,XUDLUSS
01 Jan 2024,5.25,5.19,1.2734
02 Jan 2024,5.25,5.20,1.2698
03 Jan 2024,5.25,..,1.2705
04 Jan 2024,5.25,5.18,1.2689
```

**Data Characteristics**:
- Dates appear for every calendar day in requested range
- Missing values ("..")  appear for:
  - Weekends (for daily series like SONIA, exchange rates)
  - Bank holidays
  - Periods before series inception
  - Data quality issues (rare)
- No pagination - entire requested range returned in single response

### 1.5 Data Transformation Recommendations

**Date Parsing**:
- Input format: "DD Mon YYYY"
- Recommended: Convert to ISO 8601 date format (YYYY-MM-DD)
- Handle timezone: All dates represent UK timezone (Europe/London)

**Missing Value Handling**:
- Replace ".." with null/NaN
- For daily series (SONIA, exchange rates): Consider forward-fill for weekends
- For monthly series (mortgage rates): Missing values indicate data not yet published

**Frequency Alignment**:
To achieve consistent monthly frequency across all series:
- Bank Rate: Take last available value of each month (typically constant within month)
- SONIA: Calculate monthly average (exclude null values)
- Exchange rates: Calculate monthly average (exclude weekends/holidays)
- Mortgage rates: Use as-is (already published monthly)

**Derived Metrics**:
- Month-over-month change: (Current - Previous) / Previous × 100
- Year-over-year change: (Current - Same Month Previous Year) / Same Month Previous Year × 100

---

## 2. HM Land Registry - UK House Price Index

### 2.1 API Overview

**Base URL**: `http://landregistry.data.gov.uk/data/ukhpi`

**API Type**: REST-style Linked Data API

**Authentication**: None required

**Rate Limits**: None documented (recommend respectful usage)

**Data Format**: CSV, JSON, TTL, or HTML (CSV recommended)

**Update Schedule**:
- Publication: 20th working day of each month
- Publication time: Approximately 9:30 AM UK time
- Data lag: Covers up to 2 months prior (most recent 2 months suppressed)

**Coverage**: Data available from 1995 onwards for most regions

### 2.2 Geographic Coverage

**National Levels**:
- `united-kingdom` - Aggregate UK data
- `england` - England only
- `scotland` - Scotland only
- `wales` - Wales only
- `northern-ireland` - Northern Ireland only

**English Regions** (9 regions):
- `london`
- `south-east`
- `south-west`
- `east-anglia` (also known as East of England)
- `east-midlands`
- `west-midlands`
- `yorkshire-and-the-humber`
- `north-west`
- `north-east`

**Note**: More granular local authority data available but not required for dashboard

### 2.3 Request Specification

**HTTP Method**: GET

**Endpoint Pattern**: `/data/ukhpi/region/{region-slug}.{format}`

**Path Parameters**:
- `region-slug` - Geographic identifier (see section 2.2)
- `format` - Response format: `csv`, `json`, `ttl`, or `html`

**Query Parameters** (optional):
- `min-refMonth` - Start month (format: YYYY-MM)
- `max-refMonth` - End month (format: YYYY-MM)
- `propertyType` - Filter by type: `D` (detached), `S` (semi-detached), `T` (terraced), `F` (flat)

**Example Requests**:
```
# All data for England (CSV)
GET http://landregistry.data.gov.uk/data/ukhpi/region/england.csv

# London data for 2020-2024 (CSV)
GET http://landregistry.data.gov.uk/data/ukhpi/region/london.csv?min-refMonth=2020-01&max-refMonth=2024-12

# UK data for detached houses only (JSON)
GET http://landregistry.data.gov.uk/data/ukhpi/region/united-kingdom.json?propertyType=D
```

### 2.4 Response Format (CSV)

**Content-Type**: text/csv

**Key Columns** (subset of ~50 available columns):
- `refMonth` - Reference month (format: YYYY-MM)
- `refRegionName` - Human-readable region name
- `averagePrice` - Average house price in GBP
- `housePriceIndex` - Index value (base: January 2015 = 100)
- `percentageChange` - Month-over-month percentage change
- `percentageAnnualChange` - Year-over-year percentage change
- `salesVolume` - Number of residential property sales (suppressed for recent 2 months)

**Additional Property Type Columns** (if not filtered):
- `averagePriceDetached` - Average price for detached houses
- `averagePriceSemiDetached` - Average price for semi-detached houses
- `averagePriceTerraced` - Average price for terraced houses
- `averagePriceFlat` - Average price for flats/apartments

**Example Response** (CSV):
```csv
refMonth,refRegionName,averagePrice,housePriceIndex,percentageChange,percentageAnnualChange,salesVolume
2024-09,England,301567,150.23,0.5,3.2,65432
2024-08,England,299945,149.43,0.3,3.1,68901
2024-07,England,299050,148.98,0.4,2.9,72345
```

### 2.5 Response Format (JSON)

**Content-Type**: application/json

**Structure**: Array of result objects

**Example Response** (JSON, abbreviated):
```json
{
  "result": {
    "items": [
      {
        "refMonth": "2024-09",
        "refRegionName": "England",
        "averagePrice": 301567,
        "housePriceIndex": 150.23,
        "percentageChange": 0.5,
        "percentageAnnualChange": 3.2,
        "salesVolume": 65432
      }
    ]
  }
}
```

### 2.6 Data Characteristics

**Reference Months**:
- Data organized by month of completion (not sale agreement date)
- Most recent 2 months have salesVolume suppressed (shown as null or omitted)
- Revisions published retrospectively (updates to recent months)

**Index Baseline**: January 2015 = 100 for all regions

**Data Quality Notes**:
- Very occasionally, a month may be skipped (data quality issues)
- Percentage changes pre-calculated by Land Registry
- Outlier detection applied by source (extreme sales filtered out)

**Known Limitations**:
- Does not include new build sales (separate index available)
- Cash purchases and mortgage purchases combined
- Does not account for property characteristics (size, condition)

### 2.7 Regional Data Aggregation

For the regional heat map visualization, data must be fetched separately for each region. There is no single endpoint returning all regions.

**Recommended approach**:
1. Fetch data for each of the 9 English regions plus 4 nations (13 total requests)
2. Extract most recent `percentageAnnualChange` for each region
3. Map region slugs to display names and geographic boundaries

---

## 3. Office for National Statistics (ONS) API

### 3.1 API Overview

**Base URL**: `https://api.beta.ons.gov.uk/v1`

**API Type**: REST JSON API

**Authentication**: None required

**Rate Limits**: 
- 120 requests per 10 seconds
- 200 requests per minute
- Enforcement: HTTP 429 (Too Many Requests) response

**Data Format**: JSON (primary), CSV available for some datasets

**Update Schedule**: Varies by dataset (see section 3.3)

**Important Notes**:
- API is hierarchical: Datasets → Editions → Versions → Observations
- Each dataset can have multiple editions (e.g., "time-series", "2024")
- Most recent version of edition contains latest data
- Direct CSV downloads often simpler than navigating API hierarchy

### 3.2 API Architecture

The ONS API follows a hierarchical structure:

```
Dataset (e.g., "cpih01")
  └─ Edition (e.g., "time-series")
      └─ Version (e.g., "v10", "v11")
          └─ Observations (individual data points)
```

**Navigation flow**:
1. Identify dataset ID
2. List editions for dataset
3. Get latest version of desired edition
4. Fetch observations from version

### 3.3 Required Datasets

| Dataset | Description | Update Frequency | Typical Publication Day |
|---------|-------------|------------------|-------------------------|
| `cpih01` | Consumer Prices Index including housing costs (CPIH) | Monthly | ~15th of month at 07:00 |
| `lms` | Labour Market Statistics | Monthly | ~15th of month at 07:00 |
| `retail-sales-index` | Retail Sales Index | Monthly | ~20th of month at 07:00 |
| `gross-domestic-product-gdp` | GDP | Quarterly | Varies |

**How to discover datasets**:
- Browse: https://www.ons.gov.uk/
- API dataset list: `GET /datasets`
- Search: https://www.ons.gov.uk/search?q=

### 3.4 Request Specifications

#### 3.4.1 List All Datasets

**Endpoint**: `GET /datasets`

**Response**: JSON array of dataset objects with `id`, `title`, `description`

#### 3.4.2 Get Dataset Metadata

**Endpoint**: `GET /datasets/{dataset_id}`

**Path Parameters**:
- `dataset_id` - Dataset identifier (e.g., "cpih01")

**Response**: Dataset object including available editions

#### 3.4.3 List Editions

**Endpoint**: `GET /datasets/{dataset_id}/editions`

**Response**: Array of edition objects with `edition` identifier

#### 3.4.4 Get Latest Version

**Endpoint**: `GET /datasets/{dataset_id}/editions/{edition}/versions`

**Response**: Array of version objects, sorted by release date (most recent first)

#### 3.4.5 Get Observations

**Endpoint**: `GET /datasets/{dataset_id}/editions/{edition}/versions/{version}/observations`

**Query Parameters** (optional):
- `time` - Filter by time period (e.g., "2024-01")
- `geography` - Filter by geographic area
- `dimensions` - Filter by other dimensions (dataset-specific)

**Response**: Array of observation objects with `dimensions` and `observation` value

**Example Request Flow**:
```
# 1. Get CPI dataset info
GET https://api.beta.ons.gov.uk/v1/datasets/cpih01

# 2. List editions
GET https://api.beta.ons.gov.uk/v1/datasets/cpih01/editions

# 3. Get latest version of "time-series" edition
GET https://api.beta.ons.gov.uk/v1/datasets/cpih01/editions/time-series/versions

# 4. Fetch observations from version 12
GET https://api.beta.ons.gov.uk/v1/datasets/cpih01/editions/time-series/versions/12/observations
```

### 3.5 Response Formats

#### Dataset Response (Example)
```json
{
  "id": "cpih01",
  "title": "CPIH ANNUAL RATE 00: ALL ITEMS 2015=100",
  "description": "Consumer Prices Index including owner occupiers' housing costs",
  "edition": "time-series",
  "release_frequency": "Monthly",
  "next_release": "2024-11-20T07:00:00Z"
}
```

#### Observations Response (Example)
```json
{
  "observations": [
    {
      "dimensions": {
        "time": { "id": "2024-09" },
        "geography": { "id": "K02000001", "label": "United Kingdom" },
        "aggregate": { "id": "cpih1dim1A0", "label": "All Items" }
      },
      "observation": "3.2"
    },
    {
      "dimensions": {
        "time": { "id": "2024-08" },
        "geography": { "id": "K02000001", "label": "United Kingdom" },
        "aggregate": { "id": "cpih1dim1A0", "label": "All Items" }
      },
      "observation": "3.1"
    }
  ]
}
```

### 3.6 Simplified Alternative: Direct CSV Downloads

For many datasets, ONS provides direct CSV download URLs that bypass the API hierarchy:

**CPI Inflation** (CPIH Annual Rate):
```
GET https://www.ons.gov.uk/generator?format=csv&uri=/economy/inflationandpriceindices/timeseries/d7g7/mm23
```

**Employment Rate**:
```
GET https://www.ons.gov.uk/generator?format=csv&uri=/employmentandlabourmarket/peopleinwork/employmentandemployeetypes/timeseries/lf24/lms
```

**Retail Sales**:
```
GET https://www.ons.gov.uk/generator?format=csv&uri=/businessindustryandtrade/retailindustry/timeseries/j5dk/drsi
```

**CSV Format**: Title rows at top, then headers, then data rows

**Advantages of CSV approach**:
- Single request per dataset
- No need to navigate editions/versions
- Simpler parsing (skip title rows, read data)
- More stable (URLs rarely change)

**Disadvantages**:
- Less discoverable (need to know specific time series codes)
- No structured metadata in response

### 3.7 Rate Limit Handling

**Rate Limit Headers** (included in responses):
- `X-RateLimit-Limit` - Maximum requests allowed in time window
- `X-RateLimit-Remaining` - Requests remaining in current window
- `X-RateLimit-Reset` - Unix timestamp when limit resets

**429 Response** (when rate limited):
```json
{
  "error": "Rate limit exceeded",
  "retry_after": 10
}
```

**Recommended approach**:
- Track request timestamps
- Enforce client-side rate limit (e.g., max 100 requests/minute)
- Implement exponential backoff on 429 responses
- Cache responses to minimize API calls

---

## 4. Data Quality Considerations

### 4.1 Temporal Alignment

**Challenge**: Three sources publish on different schedules with different lags.

**Implications**:
- Bank of England: Most up-to-date (daily updates for exchange rates)
- HM Land Registry: 2-month lag (recent data suppressed)
- ONS: 1-2 month lag (depends on dataset)

**Recommendation**: Dashboard should clearly indicate the reference period for each data point.

### 4.2 Revisions

**Bank of England**: 
- Historical data stable, revisions rare
- Exchange rates and SONIA never revised

**HM Land Registry**:
- Recent 3-4 months subject to revision as late sales registered
- Revisions typically small (< 0.5%)

**ONS**:
- Significant revision cycles for GDP (can span years)
- CPI inflation rarely revised
- Employment data revised as more survey responses received

**Recommendation**: For cached data, refresh monthly series after publication dates to capture revisions.

### 4.3 Missing Data Patterns

**Bank of England**:
- Weekends and bank holidays: Daily series show ".."
- Historical gaps: Some series don't exist before certain dates

**HM Land Registry**:
- Sales volume: Recent 2 months always null
- Occasional missing months: Data quality issues (rare)

**ONS**:
- Quarterly series: 75% of months have no data (expected)
- Strike periods: Some months missing (e.g., COVID impact on surveys)

### 4.4 Validation Checks

**Sanity checks before accepting API data**:

**Bank of England**:
- Base Rate: 0% ≤ value ≤ 20%
- SONIA: Should be close to Base Rate (within 0.5%)
- Exchange rates: GBP/USD typically 1.0-1.6, GBP/EUR typically 1.0-1.4
- Mortgage rates: Should exceed Base Rate (typically by 1-5%)

**HM Land Registry**:
- Average price: £50,000 ≤ value ≤ £1,000,000 (regional variations)
- House Price Index: Should increase monotonically in long term
- Percentage changes: Typically -2% to +3% month-over-month

**ONS**:
- CPI inflation: Typically 0% to 10% (extreme values > 10% warrant investigation)
- Employment rate: 70% to 80% (UK historical range)
- Retail sales: Expect seasonal patterns (higher Q4)

---

## 5. API Stability and Versioning

### 5.1 Bank of England

**Stability**: High
- URL structure unchanged since 2010s
- Series codes stable (new series added, old ones deprecated gracefully)
- Breaking changes: None documented in past decade

**Deprecation policy**: None documented

### 5.2 HM Land Registry

**Stability**: Medium
- API relaunched 2017 (previous version deprecated)
- Current version stable since 2017
- URI structure unlikely to change (Linked Data standard)

**Versioning**: None (single version)

**Monitoring**: Watch https://landregistry.data.gov.uk/ for announcements

### 5.3 ONS

**Stability**: Medium-Low (beta API)
- API marked as "beta" (subject to change)
- Breaking changes possible with advance notice
- v1 endpoint stable since 2018 but evolving

**Versioning**: URL includes version (`/v1`)

**Monitoring**: 
- API changelog: Not published consistently
- Breaking changes: Announced via developer mailing list (sign up recommended)
- Consider CSV fallback for stability

---

## 6. Support and Documentation

### 6.1 Bank of England

**Official documentation**: Limited
- Dataset browser: https://www.bankofengland.co.uk/boeapps/database/
- Help: https://www.bankofengland.co.uk/boeapps/database/help.asp
- Support: No dedicated API support (general enquiries only)

**Community resources**: Minimal

### 6.2 HM Land Registry

**Official documentation**: Comprehensive
- API documentation: http://landregistry.data.gov.uk/app/root/doc/ppd
- Linked Data guide: http://landregistry.data.gov.uk/app/root/doc/ukhpi
- Support: data.services@landregistry.gov.uk

**Community resources**: Some Stack Overflow discussions

### 6.3 ONS

**Official documentation**: Good
- API reference: https://developer.ons.gov.uk/
- Dataset documentation: https://www.ons.gov.uk/
- Support: api@ons.gov.uk
- Status page: No public status page

**Community resources**: Active discussions on data.gov.uk forums

---

## Appendix A: Quick Reference

### A.1 Essential Endpoints

```
# Bank of England - Monetary data
GET https://www.bankofengland.co.uk/boeapps/database/_iadb-fromshowcolumns.asp?Datefrom=01/Jan/2020&Dateto=31/Dec/2024&SeriesCodes=IUDBEDR,IUDSOIA,XUDLUSS&CSVF=TN&UsingCodes=Y&VPD=Y&VFD=N

# HM Land Registry - England housing data
GET http://landregistry.data.gov.uk/data/ukhpi/region/england.csv?min-refMonth=2020-01

# ONS - CPI Inflation (CSV)
GET https://www.ons.gov.uk/generator?format=csv&uri=/economy/inflationandpriceindices/timeseries/d7g7/mm23
```

### A.2 Rate Limits Summary

| Source | Limit | Enforcement |
|--------|-------|-------------|
| Bank of England | None documented | None |
| HM Land Registry | None documented | None |
| ONS | 200/minute, 120/10sec | HTTP 429 |

### A.3 Update Schedule

| Source | Dataset | Frequency | Publication Time |
|--------|---------|-----------|------------------|
| BoE | Exchange rates | Daily | 09:30 UK |
| BoE | SONIA | Daily | 12:00 UK (next day) |
| BoE | Mortgage rates | Monthly | Mid-month |
| Land Registry | House prices | Monthly | 20th working day, 09:30 UK |
| ONS | CPI | Monthly | ~15th, 07:00 UK |
| ONS | Employment | Monthly | ~15th, 07:00 UK |
| ONS | Retail sales | Monthly | ~20th, 07:00 UK |

---

## Document Revision History

- **Version 1.0** (2026-01-08): Initial API specifications document
- Focused purely on API interface documentation
- Implementation details deliberately excluded
