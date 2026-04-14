"""
Tests for EGAT Transmission and PyPSA-TH Integration

Tests cover:
- EGAT transmission builder (substations, lines, network building)
- EGAT regional networks
- EGAT GeoJSON export
- PyPSA-TH loader (when PyPSA available)
- Thai grid combined networks
- API endpoints
"""

import pytest
from typing import Dict, Any


# ============================================================================
# EGAT Transmission Tests
# ============================================================================

class TestEGATSubstations:
    """Test EGAT substation data."""

    def test_substations_loaded(self):
        """Test that EGAT substations are loaded."""
        from smart_meter_simulator.adapters.egat_transmission import EGAT_SUBSTATIONS
        assert len(EGAT_SUBSTATIONS) > 0

    def test_substation_500kv_count(self):
        """Test that 500 kV substations exist."""
        from smart_meter_simulator.adapters.egat_transmission import (
            EGAT_SUBSTATIONS, SubstationType
        )
        subs_500 = [s for s in EGAT_SUBSTATIONS.values() if s["voltage_kv"] == 500]
        assert len(subs_500) >= 6, "Expected at least 6 500 kV substations"

    def test_substation_230kv_count(self):
        """Test that 230 kV substations exist."""
        from smart_meter_simulator.adapters.egat_transmission import EGAT_SUBSTATIONS
        subs_230 = [s for s in EGAT_SUBSTATIONS.values() if s["voltage_kv"] == 230]
        assert len(subs_230) >= 10, "Expected at least 10 230 kV substations"

    def test_substation_115kv_count(self):
        """Test that 115 kV substations exist."""
        from smart_meter_simulator.adapters.egat_transmission import EGAT_SUBSTATIONS
        subs_115 = [s for s in EGAT_SUBSTATIONS.values() if s["voltage_kv"] == 115]
        assert len(subs_115) >= 5, "Expected at least 5 115 kV substations"

    def test_substation_regions(self):
        """Test that substations cover all Thai regions."""
        from smart_meter_simulator.adapters.egat_transmission import EGAT_SUBSTATIONS
        regions = set(s["region"] for s in EGAT_SUBSTATIONS.values())
        expected_regions = {"North", "Central", "Northeast", "East", "South"}
        assert expected_regions.issubset(regions), f"Missing regions: {expected_regions - regions}"

    def test_substation_coordinates(self):
        """Test that substations have valid coordinates."""
        from smart_meter_simulator.adapters.egat_transmission import EGAT_SUBSTATIONS
        for sub_id, sub in EGAT_SUBSTATIONS.items():
            assert -10 <= sub["latitude"] <= 20, f"{sub_id}: Invalid latitude {sub['latitude']}"
            assert 98 <= sub["longitude"] <= 106, f"{sub_id}: Invalid longitude {sub['longitude']}"

    def test_substation_mae_moh(self):
        """Test Mae Moh 500 kV substation (major generation hub)."""
        from smart_meter_simulator.adapters.egat_transmission import EGAT_SUBSTATIONS
        sub = EGAT_SUBSTATIONS.get("Mae_Moh_500")
        assert sub is not None
        assert sub["voltage_kv"] == 500
        assert "Lampang" in sub["province"]
        assert sub["capacity_mva"] >= 2000


class TestEGATLines:
    """Test EGAT transmission line data."""

    def test_lines_loaded(self):
        """Test that EGAT lines are loaded."""
        from smart_meter_simulator.adapters.egat_transmission import EGAT_TRANSMISSION_LINES
        assert len(EGAT_TRANSMISSION_LINES) > 0

    def test_lines_have_500kv(self):
        """Test that 500 kV lines exist."""
        from smart_meter_simulator.adapters.egat_transmission import EGAT_TRANSMISSION_LINES
        lines_500 = [l for l in EGAT_TRANSMISSION_LINES if l["voltage_kv"] == 500]
        assert len(lines_500) >= 5, "Expected at least 5 500 kV lines"

    def test_lines_have_230kv(self):
        """Test that 230 kV lines exist."""
        from smart_meter_simulator.adapters.egat_transmission import EGAT_TRANSMISSION_LINES
        lines_230 = [l for l in EGAT_TRANSMISSION_LINES if l["voltage_kv"] == 230]
        assert len(lines_230) >= 5, "Expected at least 5 230 kV lines"

    def test_lines_have_valid_length(self):
        """Test that lines have valid lengths."""
        from smart_meter_simulator.adapters.egat_transmission import EGAT_TRANSMISSION_LINES
        for line in EGAT_TRANSMISSION_LINES:
            assert line["length_km"] > 0, f"Line {line.get('line_id', 'unknown')}: Invalid length"

    def test_lines_total_length(self):
        """Test total transmission line length."""
        from smart_meter_simulator.adapters.egat_transmission import EGAT_TRANSMISSION_LINES
        total_km = sum(l["length_km"] for l in EGAT_TRANSMISSION_LINES)
        assert total_km > 2000, f"Expected total length > 2000 km, got {total_km}"


class TestEGATTransmissionBuilder:
    """Test EGAT transmission builder functionality."""

    def test_builder_init(self):
        """Test builder initialization."""
        from smart_meter_simulator.adapters.egat_transmission import EGATTransmissionBuilder
        builder = EGATTransmissionBuilder()
        assert builder is not None
        assert len(builder.substations) > 0
        assert len(builder.lines) > 0

    def test_get_substations_by_voltage(self):
        """Test filtering substations by voltage."""
        from smart_meter_simulator.adapters.egat_transmission import EGATTransmissionBuilder
        builder = EGATTransmissionBuilder()
        subs_500 = builder.get_substations(voltage_kv=500)
        assert len(subs_500) >= 6

    def test_get_substations_by_region(self):
        """Test filtering substations by region."""
        from smart_meter_simulator.adapters.egat_transmission import EGATTransmissionBuilder
        builder = EGATTransmissionBuilder()
        subs_north = builder.get_substations(region="North")
        assert len(subs_north) > 0

    def test_get_lines_by_voltage(self):
        """Test filtering lines by voltage."""
        from smart_meter_simulator.adapters.egat_transmission import EGATTransmissionBuilder
        builder = EGATTransmissionBuilder()
        lines_500 = builder.get_lines(voltage_kv=500)
        assert len(lines_500) > 0

    def test_build_full_network(self):
        """Test building full EGAT network."""
        from smart_meter_simulator.adapters.egat_transmission import EGATTransmissionBuilder
        builder = EGATTransmissionBuilder()
        net = builder.build_full_network()
        assert net is not None
        assert len(net.bus) > 0
        assert len(net.line) > 0

    def test_build_regional_network(self):
        """Test building regional EGAT network."""
        from smart_meter_simulator.adapters.egat_transmission import EGATTransmissionBuilder
        builder = EGATTransmissionBuilder()
        for region in ["North", "Central", "Northeast", "East", "South"]:
            net = builder.build_regional_network(region=region)
            assert net is not None
            assert len(net.bus) > 0, f"Region {region} has no buses"

    def test_build_network_500kv_only(self):
        """Test building 500 kV only network."""
        from smart_meter_simulator.adapters.egat_transmission import EGATTransmissionBuilder
        builder = EGATTransmissionBuilder()
        net = builder.build_full_network(
            include_500kv=True,
            include_230kv=False,
            include_115kv=False,
        )
        assert net is not None
        voltage_levels = net.bus['vn_kv'].unique()
        assert 500 in voltage_levels
        assert 230 not in voltage_levels
        assert 115 not in voltage_levels

    def test_network_statistics(self):
        """Test network statistics."""
        from smart_meter_simulator.adapters.egat_transmission import EGATTransmissionBuilder
        builder = EGATTransmissionBuilder()
        stats = builder.get_network_statistics()
        assert stats["total_substations"] > 0
        assert stats["total_transmission_lines"] > 0
        assert stats["total_line_length_km"] > 0
        assert len(stats["regions_covered"]) > 0

    def test_geojson_export(self):
        """Test GeoJSON export."""
        from smart_meter_simulator.adapters.egat_transmission import EGATTransmissionBuilder
        builder = EGATTransmissionBuilder()
        geojson = builder.export_geojson()
        assert geojson["type"] == "FeatureCollection"
        assert len(geojson["features"]) > 0
        assert "metadata" in geojson

        # Check feature types
        feature_types = set(f["properties"]["feature_type"] for f in geojson["features"])
        assert "substation" in feature_types
        assert "line" in feature_types


class TestEGATConvenienceFunctions:
    """Test EGAT convenience functions."""

    def test_create_egat_full_network(self):
        """Test create_egat_full_network convenience function."""
        from smart_meter_simulator.adapters.egat_transmission import create_egat_full_network
        net = create_egat_full_network()
        assert net is not None
        assert len(net.bus) > 0

    def test_create_egat_regional_network(self):
        """Test create_egat_regional_network convenience function."""
        from smart_meter_simulator.adapters.egat_transmission import create_egat_regional_network
        net = create_egat_regional_network(region="Central")
        assert net is not None

    def test_get_egat_statistics(self):
        """Test get_egat_statistics convenience function."""
        from smart_meter_simulator.adapters.egat_transmission import get_egat_statistics
        stats = get_egat_statistics()
        assert isinstance(stats, dict)
        assert "total_substations" in stats

    def test_get_egat_geojson(self):
        """Test get_egat_geojson convenience function."""
        from smart_meter_simulator.adapters.egat_transmission import get_egat_geojson
        geojson = get_egat_geojson()
        assert geojson["type"] == "FeatureCollection"


# ============================================================================
# PyPSA-TH Loader Tests
# ============================================================================

class TestPyPSATHConfig:
    """Test PyPSA-TH configuration."""

    def test_default_config(self):
        """Test default PyPSA-TH configuration."""
        from smart_meter_simulator.adapters.pypsa_th_loader import PyPSATHConfig
        config = PyPSATHConfig()
        assert config.use_prebuilt_network is True
        assert config.fallback_to_egat is True


class TestPyPSATHLoader:
    """Test PyPSA-TH loader (skipped if PyPSA not installed)."""

    @pytest.mark.skip(reason="PyPSA-TH pre-built network not available")
    def test_load_pypsa_network(self):
        """Test loading PyPSA network (requires pre-built .nc file)."""
        from smart_meter_simulator.adapters.pypsa_th_loader import PyPSATHLoader
        loader = PyPSATHLoader()
        n = loader.load_pypsa_network()
        # This test is skipped unless pre-built network is available
        assert n is not None

    def test_loader_fallback_to_egat(self):
        """Test loader fallback to EGAT when PyPSA not available."""
        from smart_meter_simulator.adapters.pypsa_th_loader import PyPSATHLoader, PyPSATHConfig
        from pathlib import Path

        config = PyPSATHConfig(
            pypsa_th_path=Path("/nonexistent/path"),
            fallback_to_egat=True,
        )
        loader = PyPSATHLoader(config)
        net = loader.load_to_pandapower()
        # Should fall back to EGAT
        assert net is not None
        assert len(net.bus) > 0


# ============================================================================
# Thai Grid Topology Integration Tests
# ============================================================================

class TestThaiGridIntegration:
    """Test Thai grid topology integration with EGAT and PyPSA-TH."""

    def test_egat_available_flag(self):
        """Test that EGAT availability flag is set."""
        from smart_meter_simulator.adapters.thai_grid_topology import EGAT_AVAILABLE
        assert EGAT_AVAILABLE is True

    def test_create_egat_transmission_network(self):
        """Test creating EGAT transmission network via Thai topology module."""
        from smart_meter_simulator.adapters.thai_grid_topology import create_egat_transmission_network
        net = create_egat_transmission_network()
        assert net is not None
        assert len(net.bus) > 0

    def test_create_egat_regional_network(self):
        """Test creating regional EGAT network via Thai topology module."""
        from smart_meter_simulator.adapters.thai_grid_topology import create_egat_transmission_network
        net = create_egat_transmission_network(region="Central")
        assert net is not None

    def test_get_thai_grid_statistics(self):
        """Test getting Thai grid statistics."""
        from smart_meter_simulator.adapters.thai_grid_topology import get_thai_grid_statistics
        stats = get_thai_grid_statistics(include_egat=True, include_pypsa=False)
        assert "egat" in stats
        assert stats["egat"]["total_substations"] > 0

    def test_combined_grid_builder(self):
        """Test combined Thai grid builder (transmission + distribution)."""
        pytest.skip("Combined network building takes too long for unit tests")
        # This test is skipped in CI but works locally
        from smart_meter_simulator.adapters.thai_grid_topology import ThaiGridBuilder
        builder = ThaiGridBuilder()
        net = builder.build_combined_transmission_distribution(
            region="Central",
            num_households_per_substation=10,  # Small for test
        )
        assert net is not None
        assert len(net.bus) > 0
        # Should have multiple voltage levels
        voltage_levels = net.bus['vn_kv'].unique()
        assert len(voltage_levels) >= 3  # 500, 230/115, 22, 0.4


# ============================================================================
# API Endpoint Tests
# ============================================================================

class TestEGATAPIEndpoints:
    """Test EGAT API endpoints (requires FastAPI test client)."""

    @pytest.fixture
    def client(self):
        """Create FastAPI test client."""
        from fastapi.testclient import TestClient
        from smart_meter_simulator.app import create_app
        app = create_app()
        return TestClient(app)

    def test_egat_transmission_endpoint(self, client):
        """Test GET /api/v1/grid/egat/transmission."""
        response = client.get("/api/v1/grid/egat/transmission")
        assert response.status_code == 200
        data = response.json()
        assert "substations" in data
        assert "lines" in data
        assert "statistics" in data

    def test_egat_transmission_filtered_by_region(self, client):
        """Test GET /api/v1/grid/egat/transmission?region=North."""
        response = client.get("/api/v1/grid/egat/transmission?region=North")
        assert response.status_code == 200
        data = response.json()
        assert data["region"] == "North"

    def test_egat_transmission_filtered_by_voltage(self, client):
        """Test GET /api/v1/grid/egat/transmission?voltage_kv=500."""
        response = client.get("/api/v1/grid/egat/transmission?voltage_kv=500")
        assert response.status_code == 200
        data = response.json()
        assert data["voltage_filter_kv"] == 500
        for sub in data["substations"]:
            assert sub["voltage_kv"] == 500

    def test_egat_statistics_endpoint(self, client):
        """Test GET /api/v1/grid/egat/statistics."""
        response = client.get("/api/v1/grid/egat/statistics")
        assert response.status_code == 200
        data = response.json()
        assert "total_substations" in data
        assert "total_transmission_lines" in data

    def test_egat_geojson_endpoint(self, client):
        """Test GET /api/v1/grid/egat/geojson."""
        response = client.get("/api/v1/grid/egat/geojson")
        assert response.status_code == 200
        data = response.json()
        assert data["type"] == "FeatureCollection"
        assert len(data["features"]) > 0

    def test_egat_substation_detail(self, client):
        """Test GET /api/v1/grid/egat/substations/{sub_id}."""
        response = client.get("/api/v1/grid/egat/substations/Mae_Moh_500")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "Mae_Moh_500"
        assert data["voltage_kv"] == 500

    def test_egat_substation_detail_not_found(self, client):
        """Test GET /api/v1/grid/egat/substations/{invalid_id}."""
        response = client.get("/api/v1/grid/egat/substations/NonExistent_500")
        assert response.status_code == 404

    def test_thai_statistics_endpoint(self, client):
        """Test GET /api/v1/grid/thai/statistics."""
        response = client.get("/api/v1/grid/thai/statistics")
        assert response.status_code == 200
        data = response.json()
        assert "egat" in data


# ============================================================================
# Integration Tests (Require pandapower)
# ============================================================================

@pytest.mark.integration
class TestEGATPandapowerIntegration:
    """Integration tests for EGAT + pandapower."""

    def test_full_network_power_flow(self):
        """Test that full EGAT network can be created (without power flow)."""
        from smart_meter_simulator.adapters.egat_transmission import create_egat_full_network
        net = create_egat_full_network()
        assert net is not None
        # Network should be structurally valid
        assert len(net.bus) > 0
        assert len(net.line) > 0
        assert len(net.ext_grid) > 0  # Should have slack buses

    def test_regional_network_structure(self):
        """Test regional network has expected structure."""
        from smart_meter_simulator.adapters.egat_transmission import EGATTransmissionBuilder
        builder = EGATTransmissionBuilder()

        for region in ["North", "Central", "Northeast", "East", "South"]:
            net = builder.build_regional_network(region=region)
            assert len(net.bus) > 0, f"Region {region}: No buses"
            # Each region should have at least one external grid (slack)
            assert len(net.ext_grid) > 0, f"Region {region}: No slack bus"

    def test_conductor_types_assigned(self):
        """Test that conductor types are properly assigned to lines."""
        from smart_meter_simulator.adapters.egat_transmission import EGATTransmissionBuilder
        builder = EGATTransmissionBuilder()
        net = builder.build_full_network()

        if len(net.line) > 0:
            # All lines should have a std_type
            std_types = net.line['std_type'].dropna()
            assert len(std_types) == len(net.line), "Some lines missing std_type"


# ============================================================================
# Grid Map Rendering API Tests
# ============================================================================

class TestGridMapRendering:
    """Test the /api/v1/grid/map endpoint."""

    @pytest.fixture
    def client(self):
        """Create FastAPI test client."""
        from fastapi.testclient import TestClient
        from smart_meter_simulator.app import create_app
        app = create_app()
        return TestClient(app)

    def test_map_geojson_all_layers(self, client):
        """Test GET /api/v1/grid/map with all layers."""
        r = client.get("/api/v1/grid/map?format=geojson&layers=all")
        assert r.status_code == 200
        data = r.json()
        assert data["type"] == "FeatureCollection"
        assert "features" in data
        assert "metadata" in data
        assert data["metadata"]["total_features"] > 0

    def test_map_geojson_egat_only(self, client):
        """Test GET /api/v1/grid/map with EGAT layer only."""
        r = client.get("/api/v1/grid/map?format=geojson&layers=egat")
        assert r.status_code == 200
        data = r.json()
        features = data["features"]
        assert len(features) > 0
        # Should have substations and lines
        layer_types = set(f["properties"]["layer"] for f in features)
        assert "egat_substation" in layer_types
        assert "egat_line" in layer_types

    def test_map_geojson_region_filter(self, client):
        """Test GET /api/v1/grid/map with region filter."""
        r = client.get("/api/v1/grid/map?format=geojson&layers=egat&region=Central")
        assert r.status_code == 200
        data = r.json()
        # Central region should have fewer features than all
        assert data["metadata"]["region_filter"] == "Central"
        # All features should be in Central region
        for f in data["features"]:
            props = f["properties"]
            if "region" in props:
                assert props["region"] == "Central"

    def test_map_geojson_substations_only(self, client):
        """Test GET /api/v1/grid/map with substations layer."""
        r = client.get("/api/v1/grid/map?format=geojson&layers=substations")
        assert r.status_code == 200
        data = r.json()
        for f in data["features"]:
            assert f["properties"]["layer"] == "substation"

    def test_map_geojson_bbox_filter(self, client):
        """Test GET /api/v1/grid/map with bounding box filter."""
        r = client.get("/api/v1/grid/map?format=geojson&layers=egat&bbox=99.0,13.0,101.0,14.5")
        assert r.status_code == 200
        data = r.json()
        # All features should be within bounding box
        for f in data["features"]:
            coords = f["geometry"]["coordinates"]
            if f["geometry"]["type"] == "Point":
                lon, lat = coords
                assert 99.0 <= lon <= 101.0
                assert 13.0 <= lat <= 14.5

    def test_map_geojson_voltage_colors(self, client):
        """Test that voltage-based colors are assigned."""
        r = client.get("/api/v1/grid/map?format=geojson&layers=egat")
        assert r.status_code == 200
        data = r.json()
        for f in data["features"]:
            props = f["properties"]
            if props["layer"] == "egat_substation":
                assert "marker_color" in props
                assert "marker_size" in props
            elif props["layer"] == "egat_line":
                assert "line_color" in props
                assert "line_weight" in props

    def test_map_geojson_egat_substation_detail(self, client):
        """Test EGAT substation feature properties."""
        r = client.get("/api/v1/grid/map?format=geojson&layers=egat")
        assert r.status_code == 200
        data = r.json()
        subs = [f for f in data["features"] if f["properties"]["layer"] == "egat_substation"]
        assert len(subs) > 0
        # Check required properties
        required_props = ["id", "name", "name_th", "voltage_kv", "type", "province", "region", "capacity_mva"]
        for sub in subs:
            for prop in required_props:
                assert prop in sub["properties"], f"Missing property: {prop}"

    def test_map_geojson_metadata(self, client):
        """Test GeoJSON metadata fields."""
        r = client.get("/api/v1/grid/map?format=geojson&layers=all")
        assert r.status_code == 200
        data = r.json()
        meta = data["metadata"]
        assert "total_features" in meta
        assert meta["total_features"] == len(data["features"])
        assert "layers_requested" in meta
        assert "generated_at" in meta
