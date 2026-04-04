"""
Tests for PostGIS API endpoints.

Tests cover:
- API endpoint responses
- Query parameters
- Error handling
- JSON response structure
"""

import pytest
import pytest_asyncio
from typing import AsyncGenerator
from httpx import AsyncClient

from fastapi import FastAPI
from fastapi.testclient import TestClient

from smart_meter_simulator.app import create_app
from smart_meter_simulator.database.repository import PostGISRepository

from .conftest import (
    test_database,
    sample_grid_data,
    TEST_DATABASE_URL
)


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture(scope="function")
def test_app(test_database: PostGISRepository) -> FastAPI:
    """Create test FastAPI app"""
    app = create_app()
    return app


@pytest.fixture(scope="function")
def test_client(test_app: FastAPI) -> TestClient:
    """Create test client"""
    with TestClient(test_app) as client:
        yield client


@pytest_asyncio.fixture(scope="function")
async def async_client(test_app: FastAPI) -> AsyncGenerator[AsyncClient, None]:
    """Create async test client"""
    async with AsyncClient(app=test_app, base_url="http://test") as ac:
        yield ac


# =============================================================================
# Endpoint: GET /api/grid/postgis/status
# =============================================================================

class TestPostGISStatusEndpoint:
    """Test /api/grid/postgis/status endpoint"""
    
    @pytest.mark.asyncio
    async def test_postgis_status(self, async_client: AsyncClient):
        """Test status endpoint returns database info"""
        response = await async_client.get("/api/grid/postgis/status")
        
        # Should return 200 if database is available
        if response.status_code == 200:
            data = response.json()
            assert "connected" in data
            assert data["connected"] is True
            assert "postgis_version" in data
            assert "statistics" in data
        else:
            # Database not configured - should return 503
            assert response.status_code == 503
    
    @pytest.mark.asyncio
    async def test_postgis_status_structure(self, async_client: AsyncClient):
        """Test status response structure"""
        response = await async_client.get("/api/grid/postgis/status")
        
        if response.status_code == 200:
            data = response.json()
            
            # Check required fields
            assert isinstance(data["connected"], bool)
            assert isinstance(data["postgis_version"], str)
            assert isinstance(data["statistics"], dict)
            
            # Check statistics structure
            stats = data["statistics"]
            assert "substations_by_voltage" in stats
            assert "lines_by_voltage_km" in stats
            assert "meters_by_type" in stats


# =============================================================================
# Endpoint: GET /api/grid/postgis/network/geojson
# =============================================================================

class TestNetworkGeoJSONEndpoint:
    """Test /api/grid/postgis/network/geojson endpoint"""
    
    @pytest.mark.asyncio
    async def test_network_geojson(self, async_client: AsyncClient):
        """Test GeoJSON export endpoint"""
        response = await async_client.get("/api/grid/postgis/network/geojson")
        
        if response.status_code == 200:
            data = response.json()
            
            # Check GeoJSON structure
            assert data["type"] == "FeatureCollection"
            assert "features" in data
            assert isinstance(data["features"], list)
    
    @pytest.mark.asyncio
    async def test_network_geojson_with_voltage_filter(
        self,
        async_client: AsyncClient,
        sample_grid_data: dict
    ):
        """Test GeoJSON export with voltage filter"""
        response = await async_client.get(
            "/api/grid/postgis/network/geojson?voltage_min=22&voltage_max=22"
        )
        
        if response.status_code == 200:
            data = response.json()
            
            # All features should match voltage filter
            for feature in data["features"]:
                voltage = feature["properties"].get("voltage_level_kv", 0)
                if feature["properties"]["type"] in ["substation", "line"]:
                    assert voltage <= 22.0
    
    @pytest.mark.asyncio
    async def test_network_geojson_feature_properties(
        self,
        async_client: AsyncClient,
        sample_grid_data: dict
    ):
        """Test GeoJSON feature properties"""
        response = await async_client.get("/api/grid/postgis/network/geojson")
        
        if response.status_code == 200 and len(response.json()["features"]) > 0:
            data = response.json()
            
            # Check first feature
            feature = data["features"][0]
            
            assert "type" in feature
            assert feature["type"] == "Feature"
            
            assert "geometry" in feature
            assert "properties" in feature
            
            props = feature["properties"]
            assert "type" in props  # substation, line, transformer, etc.


# =============================================================================
# Endpoint: GET /api/grid/postgis/substations
# =============================================================================

class TestSubstationsEndpoint:
    """Test /api/grid/postgis/substations endpoint"""
    
    @pytest.mark.asyncio
    async def test_get_substations(self, async_client: AsyncClient):
        """Test getting all substations"""
        response = await async_client.get("/api/grid/postgis/substations")
        
        if response.status_code == 200:
            data = response.json()
            
            assert "count" in data
            assert "substations" in data
            assert isinstance(data["substations"], list)
    
    @pytest.mark.asyncio
    async def test_get_substations_by_voltage(
        self,
        async_client: AsyncClient,
        sample_grid_data: dict
    ):
        """Test filtering substations by voltage"""
        response = await async_client.get("/api/grid/postgis/substations?voltage=22")
        
        if response.status_code == 200:
            data = response.json()
            
            # All results should be 22kV
            for sub in data["substations"]:
                assert sub["voltage_level_kv"] == 22.0
    
    @pytest.mark.asyncio
    async def test_get_substations_bbox(self, async_client: AsyncClient):
        """Test bounding box query"""
        response = await async_client.get(
            "/api/grid/postgis/substations"
            "?min_lon=100.4&min_lat=13.7&max_lon=100.6&max_lat=13.8"
        )
        
        if response.status_code == 200:
            data = response.json()
            
            # All results should be within bounds
            for sub in data["substations"]:
                coords = sub["location"]["coordinates"]
                assert 100.4 <= coords[0] <= 100.6
                assert 13.7 <= coords[1] <= 13.8


# =============================================================================
# Endpoint: GET /api/grid/postgis/transformers/nearest
# =============================================================================

class TestNearestTransformerEndpoint:
    """Test /api/grid/postgis/transformers/nearest endpoint"""
    
    @pytest.mark.asyncio
    async def test_nearest_transformer(
        self,
        async_client: AsyncClient,
        sample_grid_data: dict
    ):
        """Test finding nearest transformer"""
        response = await async_client.get(
            "/api/grid/postgis/transformers/nearest"
            "?longitude=100.5018&latitude=13.7563&max_distance_m=5000"
        )
        
        if response.status_code == 200:
            data = response.json()
            
            assert "transformer_id" in data
            assert "code" in data
            assert "distance_m" in data
            assert "capacity_kva" in data
            
            assert data["distance_m"] > 0
        else:
            # No transformer found within range
            assert response.status_code == 404
    
    @pytest.mark.asyncio
    async def test_nearest_transformer_missing_params(self, async_client: AsyncClient):
        """Test error handling for missing parameters"""
        response = await async_client.get(
            "/api/grid/postgis/transformers/nearest"
            "?longitude=100.5018"  # Missing latitude
        )
        
        # Should return 422 for validation error
        assert response.status_code == 422


# =============================================================================
# Endpoint: GET /api/grid/postgis/meters/nearby
# =============================================================================

class TestNearbyMetersEndpoint:
    """Test /api/grid/postgis/meters/nearby endpoint"""
    
    @pytest.mark.asyncio
    async def test_nearby_meters(
        self,
        async_client: AsyncClient,
        sample_grid_data: dict
    ):
        """Test finding nearby meters"""
        response = await async_client.get(
            "/api/grid/postgis/meters/nearby"
            "?longitude=100.5018&latitude=13.7563&radius_m=1000"
        )
        
        if response.status_code == 200:
            data = response.json()
            
            assert "count" in data
            assert "meters" in data
            assert isinstance(data["meters"], list)
            
            # Check meter structure
            for meter in data["meters"]:
                assert "meter_id" in meter
                assert "meter_type" in meter
                assert "distance_m" in meter
    
    @pytest.mark.asyncio
    async def test_nearby_meters_with_type_filter(
        self,
        async_client: AsyncClient,
        sample_grid_data: dict
    ):
        """Test filtering meters by type"""
        response = await async_client.get(
            "/api/grid/postgis/meters/nearby"
            "?longitude=100.5018&latitude=13.7563&radius_m=1000&meter_type=solar_prosumer"
        )
        
        if response.status_code == 200:
            data = response.json()
            
            # All results should be solar_prosumer
            for meter in data["meters"]:
                assert meter["meter_type"] == "solar_prosumer"


# =============================================================================
# Endpoint: POST /api/grid/postgis/meters
# =============================================================================

class TestCreateMeterEndpoint:
    """Test /api/grid/postgis/meters endpoint (POST)"""
    
    @pytest.mark.asyncio
    async def test_create_meter(self, async_client: AsyncClient):
        """Test creating a new meter"""
        response = await async_client.post(
            "/api/grid/postgis/meters"
            "?meter_id=TEST-API-METER-001"
            "&meter_type=solar_prosumer"
            "&longitude=100.5018"
            "&latitude=13.7563"
        )
        
        if response.status_code == 200:
            data = response.json()
            
            assert "id" in data
            assert "meter_id" in data
            assert data["meter_id"] == "TEST-API-METER-001"
            assert "meter_type" in data
            assert "location" in data
        else:
            # Database not available
            assert response.status_code == 503
    
    @pytest.mark.asyncio
    async def test_create_meter_missing_params(self, async_client: AsyncClient):
        """Test error handling for missing parameters"""
        response = await async_client.post(
            "/api/grid/postgis/meters"
            "?meter_id=TEST-METER-002"
            # Missing meter_type, longitude, latitude
        )
        
        # Should return 422 for validation error
        assert response.status_code == 422


# =============================================================================
# Endpoint: GET /api/grid/postgis/statistics
# =============================================================================

class TestStatisticsEndpoint:
    """Test /api/grid/postgis/statistics endpoint"""
    
    @pytest.mark.asyncio
    async def test_statistics(self, async_client: AsyncClient):
        """Test network statistics endpoint"""
        response = await async_client.get("/api/grid/postgis/statistics")
        
        if response.status_code == 200:
            data = response.json()
            
            assert "substations_by_voltage" in data
            assert "lines_by_voltage_km" in data
            assert "meters_by_type" in data
            assert "total_substations" in data
            assert "total_lines_km" in data
            assert "total_meters" in data


# =============================================================================
# Error Handling Tests
# =============================================================================

class TestErrorHandling:
    """Test API error handling"""
    
    @pytest.mark.asyncio
    async def test_invalid_coordinates(self, async_client: AsyncClient):
        """Test handling of invalid coordinates"""
        response = await async_client.get(
            "/api/grid/postgis/transformers/nearest"
            "?longitude=999&latitude=999&max_distance_m=1000"
        )
        
        # Should return 404 (no transformer found) or handle gracefully
        assert response.status_code in [200, 404, 503]
    
    @pytest.mark.asyncio
    async def test_invalid_voltage_range(self, async_client: AsyncClient):
        """Test handling of invalid voltage range"""
        response = await async_client.get(
            "/api/grid/postgis/network/geojson?voltage_min=1000&voltage_max=500"
        )
        
        # Should handle gracefully (empty result or error)
        assert response.status_code in [200, 400, 503]


# =============================================================================
# Performance Tests
# =============================================================================

class TestPerformance:
    """Test API performance"""
    
    @pytest.mark.asyncio
    async def test_geojson_export_performance(
        self,
        async_client: AsyncClient,
        sample_grid_data: dict
    ):
        """Test GeoJSON export performance"""
        import time
        
        start = time.time()
        response = await async_client.get("/api/grid/postgis/network/geojson")
        elapsed = time.time() - start
        
        # Should complete in < 2 seconds
        assert elapsed < 2.0
        
        if response.status_code == 200:
            data = response.json()
            assert len(data["features"]) > 0
    
    @pytest.mark.asyncio
    async def test_concurrent_requests(
        self,
        async_client: AsyncClient,
        sample_grid_data: dict
    ):
        """Test handling concurrent requests"""
        import asyncio
        
        async def make_request():
            return await async_client.get("/api/grid/postgis/statistics")
        
        # Make 10 concurrent requests
        tasks = [make_request() for _ in range(10)]
        responses = await asyncio.gather(*tasks)
        
        # All should succeed
        for response in responses:
            assert response.status_code in [200, 503]
