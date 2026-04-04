"""
Tests for Thai Electrical Infrastructure Analysers

Tests for:
- Thai EGAT Substation Analyser
- Thai MEA Power Pole Analyser
- Thai PEA Infrastructure Analyser (when implemented)

Run with:
    uv run pytest tests/test_thai_power_analysers.py -v
"""

import pytest
from datetime import datetime
from unittest.mock import Mock, MagicMock


# ============================================================================
# EGAT Substation Analyser Tests
# ============================================================================

class TestThaiEGATSubstation:
    """Tests for EGAT substation analyser"""
    
    def test_egat_analyser_initialization(self):
        """Test EGAT analyser initializes correctly"""
        from smart_meter_simulator.osmose.analysers.thai_egat_substation import (
            AnalyserThaiEGATSubstation
        )
        
        analyser = AnalyserThaiEGATSubstation()
        
        assert analyser.analyser_id == "thai_egat_substation"
        assert analyser.country == "th"
        assert analyser.conflation_distance_m == 100.0
        assert 500.0 in analyser.transmission_voltages
        assert 230.0 in analyser.transmission_voltages
        assert 115.0 in analyser.transmission_voltages
    
    def test_egat_analyser_custom_config(self):
        """Test EGAT analyser with custom configuration"""
        from smart_meter_simulator.osmose.analysers.thai_egat_substation import (
            AnalyserThaiEGATSubstation
        )
        
        config = {
            'conflation_distance': 150.0,
            'voltage_tolerance': 0.15
        }
        
        analyser = AnalyserThaiEGATSubstation(config)
        
        assert analyser.conflation_distance_m == 150.0
    
    def test_egat_voltage_parsing(self):
        """Test EGAT voltage parsing function"""
        from smart_meter_simulator.osmose.analysers.thai_egat_substation import (
            AnalyserThaiEGATSubstation
        )
        
        analyser = AnalyserThaiEGATSubstation()
        
        # Test kV parsing
        assert analyser._parse_voltage("500kV") == 500.0
        assert analyser._parse_voltage("230kV") == 230.0
        assert analyser._parse_voltage("115kV") == 115.0
        
        # Test V parsing
        assert analyser._parse_voltage("500000V") == 500.0
        assert analyser._parse_voltage("230000V") == 230.0
        
        # Test no unit (assume kV)
        assert analyser._parse_voltage("500") == 500.0
        
        # Test edge cases
        assert analyser._parse_voltage(None) is None
        assert analyser._parse_voltage("") is None
        assert analyser._parse_voltage("invalid") is None
    
    def test_egat_haversine_distance(self):
        """Test EGAT distance calculation"""
        from smart_meter_simulator.osmose.analysers.thai_egat_substation import (
            AnalyserThaiEGATSubstation
        )
        
        analyser = AnalyserThaiEGATSubstation()
        
        # Same point
        distance = analyser._haversine_distance(14.3567, 100.6234, 14.3567, 100.6234)
        assert distance == 0.0
        
        # Short distance (Wang Noi to nearby)
        distance = analyser._haversine_distance(14.3567, 100.6234, 14.3600, 100.6300)
        assert 500 < distance < 1000  # Should be ~700m
    
    def test_egat_extract_osm_substations(self):
        """Test EGAT OSM substation extraction"""
        from smart_meter_simulator.osmose.analysers.thai_egat_substation import (
            AnalyserThaiEGATSubstation
        )
        
        analyser = AnalyserThaiEGATSubstation()
        
        osm_data = {
            "nodes": [
                {
                    "id": 1001,
                    "lat": 14.3567,
                    "lon": 100.6234,
                    "tags": {
                        "power": "substation",
                        "substation": "transmission",
                        "voltage": "500000",
                        "operator": "EGAT",
                        "ref:TH:EGAT": "EGAT-WN-001"
                    }
                },
                {
                    "id": 1002,
                    "lat": 14.1234,
                    "lon": 100.7890,
                    "tags": {
                        "power": "substation",
                        "voltage": "230000"
                    }
                },
                {
                    "id": 1003,
                    "lat": 13.7000,
                    "lon": 100.5000,
                    "tags": {
                        "amenity": "restaurant"  # Not a substation
                    }
                }
            ],
            "ways": [
                {
                    "id": 2001,
                    "center": {"lat": 13.6890, "lon": 100.6012},
                    "tags": {
                        "power": "substation",
                        "voltage": "115000"
                    }
                }
            ]
        }
        
        substations = analyser._extract_osm_substations(osm_data)
        
        # Should find 3 substations (2 nodes + 1 way)
        assert len(substations) == 3
        
        # Check first substation
        assert substations[0]["id"] == 1001
        assert substations[0]["voltage"] == 500.0
        assert substations[0]["ref"] == "EGAT-WN-001"
        assert substations[0]["operator"] == "EGAT"
    
    def test_egat_run_with_mock_data(self):
        """Test EGAT analyser run with mock data"""
        from smart_meter_simulator.osmose.analysers.thai_egat_substation import (
            AnalyserThaiEGATSubstation
        )
        
        analyser = AnalyserThaiEGATSubstation()
        
        # Minimal OSM data (no substations)
        osm_data = {"nodes": [], "ways": []}
        
        result = analyser.run(osm_data)
        
        # Should find issues (EGAT substations missing in OSM)
        assert result.total_issues > 0
        assert result.total_objects > 0
        assert len(result.issues) > 0
    
    def test_egat_create_result(self):
        """Test EGAT result creation"""
        from smart_meter_simulator.osmose.analysers.thai_egat_substation import (
            AnalyserThaiEGATSubstation
        )
        
        analyser = AnalyserThaiEGATSubstation()
        
        egat_data = analyser._get_mock_egat_data()
        osm_substations = []
        
        result = analyser._create_result(egat_data, osm_substations)
        
        assert result.analyser == "thai_egat_substation"
        assert result.country == "th"
        assert result.total_objects == len(egat_data)
        assert "timestamp" in result.__dict__


# ============================================================================
# MEA Power Pole Analyser Tests
# ============================================================================

class TestThaiMEAPole:
    """Tests for MEA power pole analyser"""
    
    def test_mea_analyser_initialization(self):
        """Test MEA analyser initializes correctly"""
        from smart_meter_simulator.osmose.analysers.thai_mea_pole import (
            AnalyserThaiMEAPole
        )
        
        analyser = AnalyserThaiMEAPole()
        
        assert analyser.analyser_id == "thai_mea_pole"
        assert analyser.country == "th"
        assert analyser.conflation_distance_m == 10.0
        assert "Bangkok" in analyser.mea_provinces
        assert "Nonthaburi" in analyser.mea_provinces
        assert "Samut Prakan" in analyser.mea_provinces
    
    def test_mea_analyser_custom_config(self):
        """Test MEA analyser with custom configuration"""
        from smart_meter_simulator.osmose.analysers.thai_mea_pole import (
            AnalyserThaiMEAPole
        )
        
        config = {
            'conflation_distance': 15.0,
            'mea_provinces': ['Bangkok']
        }
        
        analyser = AnalyserThaiMEAPole(config)
        
        assert analyser.conflation_distance_m == 15.0
        assert analyser.mea_provinces == ['Bangkok']
    
    def test_mea_voltage_parsing(self):
        """Test MEA voltage parsing"""
        from smart_meter_simulator.osmose.analysers.thai_mea_pole import (
            AnalyserThaiMEAPole
        )
        
        analyser = AnalyserThaiMEAPole()
        
        # Test kV parsing
        assert analyser._parse_voltage("22kV") == 22.0
        assert analyser._parse_voltage("33kV") == 33.0
        
        # Test V parsing
        assert analyser._parse_voltage("22000V") == 22.0
        
        # Test edge cases
        assert analyser._parse_voltage(None) is None
        assert analyser._parse_voltage("invalid") is None
    
    def test_mea_extract_osm_poles(self):
        """Test MEA OSM pole extraction"""
        from smart_meter_simulator.osmose.analysers.thai_mea_pole import (
            AnalyserThaiMEAPole
        )
        
        analyser = AnalyserThaiMEAPole()
        
        osm_data = {
            "nodes": [
                {
                    "id": 5001,
                    "lat": 13.8512,
                    "lon": 100.5923,
                    "tags": {
                        "power": "pole",
                        "operator": "MEA",
                        "voltage": "22000",
                        "ref": "MEA-BK-001234"
                    }
                },
                {
                    "id": 5002,
                    "lat": 13.7465,
                    "lon": 100.5345,
                    "tags": {
                        "power": "tower"
                    }
                },
                {
                    "id": 5003,
                    "lat": 13.7000,
                    "lon": 100.5000,
                    "tags": {
                        "amenity": "bench"  # Not a pole
                    }
                }
            ]
        }
        
        poles = analyser._extract_osm_poles(osm_data)
        
        # Should find 2 poles
        assert len(poles) == 2
        
        # Check first pole
        assert poles[0]["id"] == 5001
        assert poles[0]["voltage"] == 22.0
        assert poles[0]["operator"] == "MEA"
        assert poles[0]["ref"] == "MEA-BK-001234"
    
    def test_mea_run_with_mock_data(self):
        """Test MEA analyser run with mock data"""
        from smart_meter_simulator.osmose.analysers.thai_mea_pole import (
            AnalyserThaiMEAPole
        )
        
        analyser = AnalyserThaiMEAPole()
        
        # Minimal OSM data (no poles)
        osm_data = {"nodes": [], "ways": []}
        
        result = analyser.run(osm_data)
        
        # Should find issues (MEA poles missing in OSM)
        assert result.total_issues > 0
        assert result.total_objects > 0
    
    def test_mea_mock_data_structure(self):
        """Test MEA mock data structure"""
        from smart_meter_simulator.osmose.analysers.thai_mea_pole import (
            AnalyserThaiMEAPole
        )
        
        analyser = AnalyserThaiMEAPole()
        mock_data = analyser._get_mock_mea_data()
        
        assert len(mock_data) > 0
        
        # Check structure of first pole
        pole = mock_data[0]
        assert "pole_id" in pole
        assert "province" in pole
        assert "latitude" in pole
        assert "longitude" in pole
        assert "voltage_kv" in pole
        assert "precision" in pole
        
        # Check values
        assert pole["province"] in analyser.mea_provinces
        assert pole["voltage_kv"] in [22.0, 33.0]
        assert pole["precision"] in ["A", "B"]


# ============================================================================
# Integration Tests
# ============================================================================

class TestThaiPowerAnalysersIntegration:
    """Integration tests for Thai power analysers"""
    
    def test_egat_and_mea_together(self):
        """Test running EGAT and MEA analysers together"""
        from smart_meter_simulator.osmose.analysers.thai_egat_substation import (
            AnalyserThaiEGATSubstation
        )
        from smart_meter_simulator.osmose.analysers.thai_mea_pole import (
            AnalyserThaiMEAPole
        )
        
        # Create both analysers
        egat_analyser = AnalyserThaiEGATSubstation()
        mea_analyser = AnalyserThaiMEAPole()
        
        # Run both
        osm_data = {"nodes": [], "ways": []}
        
        egat_result = egat_analyser.run(osm_data)
        mea_result = mea_analyser.run(osm_data)
        
        # Both should produce results
        assert egat_result is not None
        assert mea_result is not None
        
        # Should have different analysers
        assert egat_result.analyser != mea_result.analyser
        
        # Should have different issue types (different item codes)
        assert list(egat_result.issues_by_item.keys())[0] != list(mea_result.issues_by_item.keys())[0]
    
    def test_factory_functions(self):
        """Test convenience factory functions"""
        from smart_meter_simulator.osmose.analysers.thai_egat_substation import (
            create_egat_substation_analyser
        )
        from smart_meter_simulator.osmose.analysers.thai_mea_pole import (
            create_mea_pole_analyser
        )
        
        # Test EGAT factory
        egat = create_egat_substation_analyser()
        assert egat is not None
        assert egat.analyser_id == "thai_egat_substation"
        
        # Test MEA factory
        mea = create_mea_pole_analyser()
        assert mea is not None
        assert mea.analyser_id == "thai_mea_pole"
        
        # Test with custom config
        egat_custom = create_egat_substation_analyser({
            'conflation_distance': 200.0
        })
        assert egat_custom.conflation_distance_m == 200.0


# ============================================================================
# Performance Tests
# ============================================================================

class TestThaiPowerAnalysersPerformance:
    """Performance tests for Thai power analysers"""
    
    def test_egat_large_dataset_performance(self):
        """Test EGAT analyser with large dataset"""
        from smart_meter_simulator.osmose.analysers.thai_egat_substation import (
            AnalyserThaiEGATSubstation
        )
        import time
        
        analyser = AnalyserThaiEGATSubstation()
        
        # Create large OSM dataset
        osm_data = {
            "nodes": [
                {
                    "id": i,
                    "lat": 13.7 + (i * 0.001),
                    "lon": 100.5 + (i * 0.001),
                    "tags": {"power": "substation", "voltage": "115000"}
                }
                for i in range(1000)
            ],
            "ways": []
        }
        
        # Time the execution
        start = time.time()
        result = analyser.run(osm_data)
        elapsed = time.time() - start
        
        # Should complete in reasonable time (<5 seconds)
        assert elapsed < 5.0
        assert result is not None
    
    def test_mea_large_dataset_performance(self):
        """Test MEA analyser with large dataset"""
        from smart_meter_simulator.osmose.analysers.thai_mea_pole import (
            AnalyserThaiMEAPole
        )
        import time
        
        analyser = AnalyserThaiMEAPole()
        
        # Create large OSM dataset
        osm_data = {
            "nodes": [
                {
                    "id": i,
                    "lat": 13.7 + (i * 0.0001),
                    "lon": 100.5 + (i * 0.0001),
                    "tags": {"power": "pole", "voltage": "22000"}
                }
                for i in range(1000)
            ],
            "ways": []
        }
        
        # Time the execution
        start = time.time()
        result = analyser.run(osm_data)
        elapsed = time.time() - start
        
        # Should complete in reasonable time (<5 seconds)
        assert elapsed < 5.0
        assert result is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
