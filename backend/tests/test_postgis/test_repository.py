"""
Tests for PostGIS repository operations.

Tests cover:
- Database connection and initialization
- CRUD operations for all entity types
- Spatial queries (nearest neighbor, radius search)
- GeoJSON export
- Network statistics
"""

import pytest
import pytest_asyncio
from decimal import Decimal

from smart_meter_simulator.database.repository import PostGISRepository
from smart_meter_simulator.database.models import Substation, Transformer, PowerLine, Meter

from .conftest import (
    test_database,
    sample_substation,
    sample_transformer,
    sample_power_line,
    sample_meter,
    sample_grid_data,
    assert_coordinates_equal,
    count_table_rows,
    cleanup_test_data
)


# =============================================================================
# Database Connection Tests
# =============================================================================

class TestDatabaseConnection:
    """Test database connection and initialization"""
    
    @pytest.mark.asyncio
    async def test_check_connection(self, test_database: PostGISRepository):
        """Test database connection check"""
        connected = await test_database.check_connection()
        assert connected is True
    
    @pytest.mark.asyncio
    async def test_postgis_version(self, test_database: PostGISRepository):
        """Test PostGIS version query"""
        version = await test_database.get_postgis_version()
        assert version is not None
        assert "PostGIS" in version
    
    @pytest.mark.asyncio
    async def test_create_tables(self, test_database: PostGISRepository):
        """Test table creation"""
        # Tables should already be created by fixture
        substations_count = await count_table_rows(test_database, "substations")
        assert substations_count >= 0


# =============================================================================
# Substation Tests
# =============================================================================

class TestSubstationOperations:
    """Test substation CRUD operations"""
    
    @pytest.mark.asyncio
    async def test_create_substation(self, test_database: PostGISRepository):
        """Test creating a substation"""
        substation = await test_database.create_substation(
            name="Test Substation",
            code="TEST-SUB-001",
            voltage_level_kv=22.0,
            operator="MEA",
            longitude=100.5018,
            latitude=13.7563
        )
        
        assert substation.id is not None
        assert substation.name == "Test Substation"
        assert substation.code == "TEST-SUB-001"
        assert float(substation.voltage_level_kv) == 22.0
        
        # Check coordinates
        lon, lat = substation.get_coordinates()
        assert_coordinates_equal((lon, lat), (100.5018, 13.7563))
    
    @pytest.mark.asyncio
    async def test_get_substation_by_id(
        self,
        test_database: PostGISRepository,
        sample_substation: Substation
    ):
        """Test retrieving substation by ID"""
        retrieved = await test_database.get_substation(sample_substation.id)
        
        assert retrieved is not None
        assert retrieved.id == sample_substation.id
        assert retrieved.code == sample_substation.code
    
    @pytest.mark.asyncio
    async def test_get_substation_by_code(
        self,
        test_database: PostGISRepository,
        sample_substation: Substation
    ):
        """Test retrieving substation by code"""
        retrieved = await test_database.get_substation_by_code(sample_substation.code)
        
        assert retrieved is not None
        assert retrieved.id == sample_substation.id
    
    @pytest.mark.asyncio
    async def test_get_substations_by_voltage(
        self,
        test_database: PostGISRepository,
        sample_grid_data: dict
    ):
        """Test filtering substations by voltage"""
        substations = await test_database.get_substations_by_voltage(22.0)
        
        assert len(substations) > 0
        for sub in substations:
            assert float(sub.voltage_level_kv) == 22.0
    
    @pytest.mark.asyncio
    async def test_update_substation(
        self,
        test_database: PostGISRepository,
        sample_substation: Substation
    ):
        """Test updating substation"""
        # Update capacity
        sample_substation.capacity_mva = Decimal("25.0")
        
        async with test_database.get_session() as session:
            session.add(sample_substation)
            await session.commit()
            await session.refresh(sample_substation)
        
        assert float(sample_substation.capacity_mva) == 25.0


# =============================================================================
# Transformer Tests
# =============================================================================

class TestTransformerOperations:
    """Test transformer CRUD operations"""
    
    @pytest.mark.asyncio
    async def test_create_transformer(self, test_database: PostGISRepository):
        """Test creating a transformer"""
        transformer = await test_database.create_transformer(
            code="TEST-TXN-001",
            voltage_primary_kv=22.0,
            voltage_secondary_kv=0.4,
            capacity_kva=500,
            longitude=100.5025,
            latitude=13.7570
        )
        
        assert transformer.id is not None
        assert transformer.code == "TEST-TXN-001"
        assert float(transformer.voltage_primary_kv) == 22.0
        assert float(transformer.voltage_secondary_kv) == 0.4
        
        # Check coordinates
        lon, lat = transformer.get_coordinates()
        assert_coordinates_equal((lon, lat), (100.5025, 13.7570))
    
    @pytest.mark.asyncio
    async def test_get_transformer(
        self,
        test_database: PostGISRepository,
        sample_transformer: Transformer
    ):
        """Test retrieving transformer by ID"""
        retrieved = await test_database.get_transformer(sample_transformer.id)
        
        assert retrieved is not None
        assert retrieved.id == sample_transformer.id
    
    @pytest.mark.asyncio
    async def test_find_nearest_transformer(
        self,
        test_database: PostGISRepository,
        sample_transformer: Transformer
    ):
        """Test nearest transformer search"""
        # Get transformer coordinates
        lon, lat = sample_transformer.get_coordinates()
        
        # Search near the transformer
        result = await test_database.find_nearest_transformer(
            longitude=lon + 0.001,  # Small offset
            latitude=lat + 0.001,
            max_distance_m=500
        )
        
        assert result is not None
        assert result["transformer_id"] == sample_transformer.id
        assert result["distance_m"] < 500


# =============================================================================
# Power Line Tests
# =============================================================================

class TestPowerLineOperations:
    """Test power line CRUD operations"""
    
    @pytest.mark.asyncio
    async def test_create_power_line(self, test_database: PostGISRepository):
        """Test creating a power line"""
        power_line = await test_database.create_power_line(
            code="TEST-LINE-001",
            voltage_level_kv=22.0,
            coordinates=[
                (100.5018, 13.7563),
                (100.5025, 13.7570),
                (100.5030, 13.7580)
            ],
            line_type="overhead"
        )
        
        assert power_line.id is not None
        assert power_line.code == "TEST-LINE-001"
        assert float(power_line.voltage_level_kv) == 22.0
        
        # Check coordinates
        coords = power_line.get_coordinates()
        assert len(coords) == 3
    
    @pytest.mark.asyncio
    async def test_get_power_line(
        self,
        test_database: PostGISRepository,
        sample_power_line: PowerLine
    ):
        """Test retrieving power line by ID"""
        retrieved = await test_database.get_power_line(sample_power_line.id)
        
        assert retrieved is not None
        assert retrieved.id == sample_power_line.id
    
    @pytest.mark.asyncio
    async def test_get_power_lines_by_voltage(
        self,
        test_database: PostGISRepository,
        sample_grid_data: dict
    ):
        """Test filtering power lines by voltage"""
        lines = await test_database.get_power_lines_by_voltage(22.0)
        
        assert len(lines) > 0
        for line in lines:
            assert float(line.voltage_level_kv) == 22.0


# =============================================================================
# Meter Tests
# =============================================================================

class TestMeterOperations:
    """Test meter CRUD operations"""
    
    @pytest.mark.asyncio
    async def test_create_meter(self, test_database: PostGISRepository):
        """Test creating a meter"""
        meter = await test_database.create_meter(
            meter_id="TEST-METER-000001",
            meter_type="solar_prosumer",
            serial_number="SN000000001",
            longitude=100.5020,
            latitude=13.7565
        )
        
        assert meter.id is not None
        assert meter.meter_id == "TEST-METER-000001"
        assert meter.meter_type == "solar_prosumer"
        
        # Check coordinates
        lon, lat = meter.get_coordinates()
        assert_coordinates_equal((lon, lat), (100.5020, 13.7565))
    
    @pytest.mark.asyncio
    async def test_get_meter(
        self,
        test_database: PostGISRepository,
        sample_meter: Meter
    ):
        """Test retrieving meter by ID"""
        retrieved = await test_database.get_meter(sample_meter.meter_id)
        
        assert retrieved is not None
        assert retrieved.meter_id == sample_meter.meter_id
    
    @pytest.mark.asyncio
    async def test_get_meters_in_radius(
        self,
        test_database: PostGISRepository,
        sample_grid_data: dict
    ):
        """Test radius search for meters"""
        meters = sample_grid_data["meters"]
        if not meters:
            pytest.skip("No meters in sample data")
        
        # Get first meter coordinates
        lon, lat = meters[0].get_coordinates()
        
        # Search nearby
        results = await test_database.get_meters_in_radius(
            longitude=lon,
            latitude=lat,
            radius_m=1000
        )
        
        assert len(results) > 0
        for meter in results:
            assert meter["distance_m"] <= 1000
    
    @pytest.mark.asyncio
    async def test_store_reading(
        self,
        test_database: PostGISRepository,
        sample_meter: Meter
    ):
        """Test storing meter reading"""
        from datetime import datetime
        
        reading = await test_database.store_reading(
            meter_id=sample_meter.meter_id,
            timestamp=datetime.utcnow(),
            energy_generated_kwh=5.234,
            energy_consumed_kwh=2.145,
            voltage_v=239.8,
            current_a=12.3,
            frequency_hz=50.02
        )
        
        assert reading.id is not None
        assert float(reading.energy_generated_kwh) == 5.234
        assert float(reading.energy_consumed_kwh) == 2.145


# =============================================================================
# GeoJSON Export Tests
# =============================================================================

class TestGeoJSONExport:
    """Test GeoJSON export functionality"""
    
    @pytest.mark.asyncio
    async def test_export_network_geojson(
        self,
        test_database: PostGISRepository,
        sample_grid_data: dict
    ):
        """Test exporting network as GeoJSON"""
        geojson = await test_database.export_network_geojson()
        
        assert geojson is not None
        assert geojson["type"] == "FeatureCollection"
        assert "features" in geojson
        
        # Should have features
        features = geojson["features"]
        assert len(features) > 0
        
        # Check feature structure
        for feature in features[:5]:  # Check first 5
            assert feature["type"] == "Feature"
            assert "geometry" in feature
            assert "properties" in feature
            assert "type" in feature["properties"]
    
    @pytest.mark.asyncio
    async def test_export_filtered_by_voltage(
        self,
        test_database: PostGISRepository,
        sample_grid_data: dict
    ):
        """Test exporting network filtered by voltage"""
        # Export only 22kV
        geojson = await test_database.export_network_geojson(
            voltage_min=22.0,
            voltage_max=22.0
        )
        
        features = geojson["features"]
        
        # All features should be 22kV or lower
        for feature in features:
            voltage = feature["properties"].get("voltage_level_kv", 0)
            if feature["properties"]["type"] in ["substation", "line"]:
                assert voltage <= 22.0


# =============================================================================
# Network Statistics Tests
# =============================================================================

class TestNetworkStatistics:
    """Test network statistics queries"""
    
    @pytest.mark.asyncio
    async def test_get_network_stats(
        self,
        test_database: PostGISRepository,
        sample_grid_data: dict
    ):
        """Test getting network statistics"""
        stats = await test_database.get_network_stats()
        
        assert "substations_by_voltage" in stats
        assert "lines_by_voltage_km" in stats
        assert "meters_by_type" in stats
        assert "total_substations" in stats
        assert "total_lines_km" in stats
        assert "total_meters" in stats
        
        # Should have data
        assert stats["total_substations"] >= 3
        assert stats["total_meters"] >= 50


# =============================================================================
# Spatial Query Tests
# =============================================================================

class TestSpatialQueries:
    """Test advanced spatial queries"""
    
    @pytest.mark.asyncio
    async def test_bounding_box_query(
        self,
        test_database: PostGISRepository,
        sample_grid_data: dict
    ):
        """Test bounding box spatial query"""
        # Query Bangkok area
        substations = await test_database.get_substations_in_bbox(
            min_lon=100.4,
            min_lat=13.7,
            max_lon=100.6,
            max_lat=13.8
        )
        
        assert len(substations) > 0
        
        # All results should be within bounds
        for sub in substations:
            lon, lat = sub.get_coordinates()
            assert 100.4 <= lon <= 100.6
            assert 13.7 <= lat <= 13.8
    
    @pytest.mark.asyncio
    async def test_distance_calculation(
        self,
        test_database: PostGISRepository,
        sample_substation: Substation
    ):
        """Test distance calculation between points"""
        # Get substation coordinates
        lon1, lat1 = sample_substation.get_coordinates()
        
        # Create another point 1km away
        lon2 = lon1 + 0.01  # Approx 1km at Bangkok latitude
        lat2 = lat1
        
        # Find nearest transformer to both points
        result1 = await test_database.find_nearest_transformer(lon1, lat1, max_distance_m=50000)
        result2 = await test_database.find_nearest_transformer(lon2, lat2, max_distance_m=50000)
        
        # Results should be different or have different distances
        if result1 and result2:
            assert result1["distance_m"] >= 0
            assert result2["distance_m"] >= 0


# =============================================================================
# Integration Tests
# =============================================================================

class TestIntegration:
    """Integration tests for complete workflows"""
    
    @pytest.mark.asyncio
    async def test_complete_workflow(
        self,
        test_database: PostGISRepository
    ):
        """Test complete workflow: create → query → export"""
        # Create substation
        substation = await test_database.create_substation(
            name="Workflow Test Substation",
            code="WORKFLOW-SUB-001",
            voltage_level_kv=22.0,
            longitude=100.5018,
            latitude=13.7563
        )
        
        # Create transformer
        transformer = await test_database.create_transformer(
            code="WORKFLOW-TXN-001",
            longitude=100.5025,
            latitude=13.7570
        )
        
        # Create meter
        meter = await test_database.create_meter(
            meter_id="WORKFLOW-METER-000001",
            meter_type="solar_prosumer",
            longitude=100.5020,
            latitude=13.7565
        )
        
        # Query by ID
        retrieved_sub = await test_database.get_substation(substation.id)
        assert retrieved_sub is not None
        
        # Find nearest transformer
        nearest = await test_database.find_nearest_transformer(
            100.5020, 13.7565, max_distance_m=500
        )
        assert nearest is not None
        
        # Export as GeoJSON
        geojson = await test_database.export_network_geojson()
        assert geojson is not None
        assert len(geojson["features"]) > 0
        
        # Get statistics
        stats = await test_database.get_network_stats()
        assert stats["total_substations"] > 0
    
    @pytest.mark.asyncio
    async def test_bulk_insert_performance(
        self,
        test_database: PostGISRepository
    ):
        """Test bulk insert performance"""
        import time
        
        # Insert 100 meters
        start_time = time.time()
        
        for i in range(100):
            await test_database.create_meter(
                meter_id=f"BULK-METER-{i:06d}",
                meter_type="solar_prosumer",
                longitude=100.5000 + (i * 0.0001),
                latitude=13.7500 + (i * 0.0001)
            )
        
        elapsed = time.time() - start_time
        
        # Should complete in reasonable time (< 10 seconds)
        assert elapsed < 10.0
        
        # Verify count
        count = await count_table_rows(test_database, "meters")
        assert count >= 100
