# PostGIS Test Suite

Comprehensive test suite for the PostGIS integration in GridTokenX Smart Meter Simulator.

## Overview

This test suite covers:

- ✅ Database connection and initialization
- ✅ CRUD operations for all entity types
- ✅ Spatial queries (nearest neighbor, radius search, bounding box)
- ✅ GeoJSON export functionality
- ✅ REST API endpoints
- ✅ Performance benchmarks
- ✅ Error handling

## Test Structure

```
tests/test_postgis/
├── conftest.py              # Test fixtures and utilities
├── test_repository.py       # Repository layer tests
├── test_api_endpoints.py    # REST API tests
└── README.md                # This file
```

## Quick Start

### Prerequisites

1. **Start Test Database**

```bash
# Option 1: Use existing database
docker-compose up -d postgres

# Option 2: Create dedicated test database
docker exec -it gridtokenx-postgres psql -U gridtokenx <<EOF
CREATE DATABASE gridtokenx_test;
\c gridtokenx_test
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS postgis_topology;
EOF
```

2. **Set Environment Variable** (optional)

```bash
export TEST_DATABASE_URL="postgresql+asyncpg://gridtokenx:gridtokenx_password@localhost:5432/gridtokenx_test"
```

### Run Tests

```bash
# Run all PostGIS tests
uv run pytest tests/test_postgis/ -v

# Run specific test file
uv run pytest tests/test_postgis/test_repository.py -v

# Run specific test class
uv run pytest tests/test_postgis/test_repository.py::TestSubstationOperations -v

# Run specific test
uv run pytest tests/test_postgis/test_repository.py::TestSubstationOperations::test_create_substation -v

# Run with coverage
uv run pytest tests/test_postgis/ --cov=smart_meter_simulator/database --cov-report=html

# Run async tests
uv run pytest tests/test_postgis/ -v --asyncio-mode=auto
```

## Test Categories

### 1. Repository Tests (`test_repository.py`)

Tests for the `PostGISRepository` class:

**Database Connection:**
- `test_check_connection` - Verify database connectivity
- `test_postgis_version` - Check PostGIS version
- `test_create_tables` - Verify table creation

**Substation Operations:**
- `test_create_substation` - Create new substation
- `test_get_substation_by_id` - Retrieve by ID
- `test_get_substation_by_code` - Retrieve by code
- `test_get_substations_by_voltage` - Filter by voltage level
- `test_update_substation` - Update substation data

**Transformer Operations:**
- `test_create_transformer` - Create new transformer
- `test_get_transformer` - Retrieve by ID
- `test_find_nearest_transformer` - Nearest neighbor search

**Power Line Operations:**
- `test_create_power_line` - Create new power line
- `test_get_power_line` - Retrieve by ID
- `test_get_power_lines_by_voltage` - Filter by voltage

**Meter Operations:**
- `test_create_meter` - Create new meter
- `test_get_meter` - Retrieve by meter_id
- `test_get_meters_in_radius` - Radius search
- `test_store_reading` - Store meter reading

**GeoJSON Export:**
- `test_export_network_geojson` - Export entire network
- `test_export_filtered_by_voltage` - Export with voltage filter

**Statistics:**
- `test_get_network_stats` - Get network statistics

**Spatial Queries:**
- `test_bounding_box_query` - Bounding box spatial query
- `test_distance_calculation` - Distance between points

### 2. API Endpoint Tests (`test_api_endpoints.py`)

Tests for REST API endpoints:

**Status Endpoint:**
- `test_postgis_status` - Database status check
- `test_postgis_status_structure` - Response structure validation

**GeoJSON Endpoint:**
- `test_network_geojson` - Export network GeoJSON
- `test_network_geojson_with_voltage_filter` - Filtered export
- `test_network_geojson_feature_properties` - Feature structure

**Substations Endpoint:**
- `test_get_substations` - Get all substations
- `test_get_substations_by_voltage` - Filter by voltage
- `test_get_substations_bbox` - Bounding box query

**Transformer Endpoint:**
- `test_nearest_transformer` - Find nearest transformer
- `test_nearest_transformer_missing_params` - Error handling

**Meters Endpoint:**
- `test_nearby_meters` - Find nearby meters
- `test_nearby_meters_with_type_filter` - Filter by type
- `test_create_meter` - Create new meter

**Statistics Endpoint:**
- `test_statistics` - Get network statistics

**Error Handling:**
- `test_invalid_coordinates` - Invalid coordinate handling
- `test_invalid_voltage_range` - Invalid voltage range

**Performance:**
- `test_geojson_export_performance` - Export speed
- `test_concurrent_requests` - Concurrent request handling

## Fixtures

### Database Fixtures

- `test_database` - Fresh test database for each test
- `test_engine` - Async database engine
- `test_config` - Test configuration

### Sample Data Fixtures

- `sample_substation` - Single test substation
- `sample_transformer` - Single test transformer
- `sample_power_line` - Single test power line
- `sample_meter` - Single test meter
- `sample_grid_data` - Complete sample grid (3 substations, 10 transformers, 5 lines, 50 meters)

### Usage Example

```python
@pytest.mark.asyncio
async def test_with_sample_data(test_database, sample_grid_data):
    """Test using sample grid data fixture"""
    # sample_grid_data contains:
    # - substations: [substation_500, substation_115, substation_22]
    # - transformers: [txn1, txn2, ..., txn10]
    # - power_lines: [line1, line2, ..., line5]
    # - meters: [meter1, meter2, ..., meter50]
    
    stats = await test_database.get_network_stats()
    assert stats["total_substations"] >= 3
```

## Helper Functions

### Coordinate Comparison

```python
from .conftest import assert_coordinates_equal

def test_coordinates():
    assert_coordinates_equal((100.5018, 13.7563), (100.5018, 13.7563))
    assert_coordinates_equal((100.5018, 13.7563), (100.5019, 13.7564), tolerance=0.001)
```

### Row Count

```python
from .conftest import count_table_rows

async def test_count():
    count = await count_table_rows(test_database, "substations")
    assert count > 0
```

### Cleanup

```python
from .conftest import cleanup_test_data

async def test_cleanup(test_database):
    # ... test code ...
    await cleanup_test_data(test_database)
```

## Performance Benchmarks

Run performance tests:

```bash
# Run performance tests
uv run pytest tests/test_postgis/test_repository.py::TestIntegration::test_bulk_insert_performance -v

# Run with timing
uv run pytest tests/test_postgis/test_api_endpoints.py::TestPerformance -v -s
```

**Expected Performance:**

| Operation | Target | Typical |
|-----------|--------|---------|
| Create substation | < 50ms | 15ms |
| Create transformer | < 50ms | 12ms |
| Create meter | < 50ms | 10ms |
| Nearest transformer | < 10ms | 2ms |
| Meters in radius | < 20ms | 5ms |
| GeoJSON export (1000 assets) | < 500ms | 25ms |
| Bulk insert (100 meters) | < 10s | 3s |

## Continuous Integration

Add to your CI/CD pipeline:

```yaml
# .github/workflows/test.yml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    services:
      postgres:
        image: postgis/postgis:15-3.3
        env:
          POSTGRES_USER: gridtokenx
          POSTGRES_PASSWORD: gridtokenx_password
          POSTGRES_DB: gridtokenx_test
        ports:
          - 5432:5432
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Install dependencies
        run: |
          pip install uv
          uv sync
      
      - name: Run tests
        run: |
          uv run pytest tests/test_postgis/ -v --cov=smart_meter_simulator/database
        env:
          TEST_DATABASE_URL: postgresql+asyncpg://gridtokenx:gridtokenx_password@localhost:5432/gridtokenx_test
```

## Troubleshooting

### Connection Refused

```bash
# Check if PostgreSQL is running
docker-compose ps postgres

# Restart database
docker-compose restart postgres

# Check connection
docker exec -it gridtokenx-postgres psql -U gridtokenx -d gridtokenx_test -c "SELECT 1;"
```

### PostGIS Not Enabled

```bash
# Enable PostGIS in test database
docker exec -it gridtokenx-postgres psql -U gridtokenx -d gridtokenx_test <<EOF
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS postgis_topology;
EOF
```

### Test Database Doesn't Exist

```bash
# Create test database
docker exec -it gridtokenx-postgres psql -U gridtokenx <<EOF
CREATE DATABASE gridtokenx_test;
\c gridtokenx_test
CREATE EXTENSION postgis;
EOF
```

### Async Test Errors

```bash
# Ensure pytest-asyncio is installed
uv run pip install pytest-asyncio

# Run with auto mode
uv run pytest tests/test_postgis/ --asyncio-mode=auto
```

## Writing New Tests

### Template

```python
import pytest
import pytest_asyncio

from .conftest import test_database

@pytest.mark.asyncio
async def test_new_feature(test_database: PostGISRepository):
    """Test new feature"""
    # Arrange
    # ... setup code ...
    
    # Act
    # ... action to test ...
    
    # Assert
    # ... assertions ...
```

### Best Practices

1. **Use fixtures** - Don't create database connections manually
2. **Clean up** - Use function-scoped fixtures for automatic cleanup
3. **Async tests** - Mark with `@pytest.mark.asyncio`
4. **Descriptive names** - Use clear test function names
5. **Test one thing** - Each test should verify one behavior
6. **Use sample data** - Leverage `sample_grid_data` fixture
7. **Check response codes** - Always verify HTTP status codes
8. **Test error cases** - Include error handling tests

## Coverage Report

Generate coverage report:

```bash
# Run with coverage
uv run pytest tests/test_postgis/ --cov=smart_meter_simulator/database --cov-report=html

# Open report
open htmlcov/index.html
```

**Target Coverage:**
- Repository: > 80%
- API Endpoints: > 75%
- Overall: > 70%

## Additional Resources

- [PostGIS Documentation](https://postgis.net/documentation/)
- [GeoAlchemy2 Documentation](https://geoalchemy-2.readthedocs.io/)
- [pytest-asyncio Documentation](https://pytest-asyncio.readthedocs.io/)
- [FastAPI Testing](https://fastapi.tiangolo.com/tutorial/testing/)

---

**Part of the GridTokenX Platform**

For more information:
- `docs/POSTGIS_INTEGRATION.md` - Complete integration guide
- `docs/POSTGIS_QUICKSTART.md` - Quick start guide
- `docs/POSTGIS_SUMMARY.md` - Quick reference
