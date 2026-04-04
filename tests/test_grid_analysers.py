"""
Tests for GridTokenX Custom Analysers

Tests for:
- PowerSubstationValidator
- PowerLineConnectivity
- DuplicateDetection
- MeterConflation
"""

import pytest
from smart_meter_simulator.osmose.analysers import (
    PowerSubstationValidator,
    PowerLineConnectivity,
    DuplicateDetection,
    MeterConflation,
)
from smart_meter_simulator.osmose.analysers.meter_conflation import ConflationConfig
from smart_meter_simulator.osmose.core.issue import IssueLevel


# ---- Test Data ----

SAMPLE_OSM_DATA_WITH_SUBSTATIONS = {
    "nodes": [
        {
            "id": 1,
            "lat": 13.7563,
            "lon": 100.5018,
            "tags": {"power": "substation", "voltage": "22000", "substation": "distribution"},
        },
        {
            "id": 2,
            "lat": 13.7570,
            "lon": 100.5025,
            "tags": {"power": "substation"},  # Missing voltage and substation type
        },
        {
            "id": 3,
            "lat": 13.7564,
            "lon": 100.5019,  # Very close to node 1 (~12m)
            "tags": {"power": "substation", "voltage": "22000", "substation": "distribution"},
        },
        {
            "id": 4,
            "lat": 13.7600,
            "lon": 100.5100,
            "tags": {"power": "substation", "voltage": "22000", "substation": "distribution"},
        },
        # Power poles
        {
            "id": 10,
            "lat": 13.7565,
            "lon": 100.5020,
            "tags": {"power": "pole"},
        },
        {
            "id": 11,
            "lat": 13.7567,
            "lon": 100.5022,
            "tags": {"power": "pole"},
        },
    ],
    "ways": [
        {
            "id": 100,
            "nodes": [10, 11],
            "tags": {"power": "line", "voltage": "22000"},
        },
    ],
    "relations": [],
}

SAMPLE_OSM_DATA_WITH_LINES = {
    "nodes": [
        {"id": 1, "lat": 13.7560, "lon": 100.5010, "tags": {"power": "substation", "voltage": "22000", "substation": "distribution"}},
        {"id": 2, "lat": 13.7570, "lon": 100.5020, "tags": {"power": "pole"}},
        {"id": 3, "lat": 13.7580, "lon": 100.5030, "tags": {"power": "pole"}},
        {"id": 4, "lat": 13.7590, "lon": 100.5040, "tags": {"power": "substation", "voltage": "22000", "substation": "distribution"}},
    ],
    "ways": [
        # Connected line (1->2->3->4)
        {"id": 100, "nodes": [1, 2, 3, 4], "tags": {"power": "line", "voltage": "22000"}},
        # Dangling line (5->6, not connected to anything)
        {"id": 101, "nodes": [5, 6], "tags": {"power": "line"}},  # missing voltage
        {"id": 102, "nodes": [7, 8], "nodes_extra": [], "tags": {"power": "line", "material": "invalid_material"}},
    ],
    "relations": [],
}

SAMPLE_METERS = [
    {"meter_id": "MTR_001", "lat": 13.7563, "lon": 100.5018},  # Near pole
    {"meter_id": "MTR_002", "lat": 13.7564, "lon": 100.5019},  # Near same pole
    {"meter_id": "MTR_003", "lat": 13.8000, "lon": 100.6000},  # Far from anything
]

OSM_DATA_WITH_POLES = {
    "nodes": [
        {"id": 100, "lat": 13.7563, "lon": 100.5018, "tags": {"power": "pole"}},
        {"id": 101, "lat": 13.7565, "lon": 100.5020, "tags": {"power": "pole"}},
        {"id": 102, "lat": 13.7570, "lon": 100.5025, "tags": {"power": "transformer", "voltage": "22000"}},
    ],
    "ways": [],
    "relations": [],
}


# ---- PowerSubstationValidator Tests ----

class TestPowerSubstationValidator:
    def test_init(self):
        analyser = PowerSubstationValidator(country="TH")
        assert analyser.country == "TH"
        assert analyser.analyser_id == "power_substation_validator"

    def test_valid_substation(self):
        analyser = PowerSubstationValidator(country="TH")
        osm_data = {
            "nodes": [
                {"id": 1, "lat": 13.7563, "lon": 100.5018,
                 "tags": {"power": "substation", "voltage": "22000", "substation": "distribution"}},
            ],
            "ways": [],
            "relations": [],
        }
        result = analyser.run(osm_data)
        assert result.total_issues == 0

    def test_missing_voltage(self):
        analyser = PowerSubstationValidator(country="TH")
        osm_data = {
            "nodes": [
                {"id": 1, "lat": 13.7563, "lon": 100.5018,
                 "tags": {"power": "substation", "substation": "distribution"}},
            ],
            "ways": [],
            "relations": [],
        }
        result = analyser.run(osm_data)
        assert result.total_issues >= 1
        assert result.issues_by_level["1"] >= 1  # HIGH level

    def test_missing_substation_type(self):
        analyser = PowerSubstationValidator(country="TH")
        osm_data = {
            "nodes": [
                {"id": 1, "lat": 13.7563, "lon": 100.5018,
                 "tags": {"power": "substation", "voltage": "22000"}},
            ],
            "ways": [],
            "relations": [],
        }
        result = analyser.run(osm_data)
        assert result.total_issues >= 1

    def test_duplicate_substations(self):
        analyser = PowerSubstationValidator(country="TH")
        osm_data = {
            "nodes": [
                {"id": 1, "lat": 13.7563, "lon": 100.5018,
                 "tags": {"power": "substation", "voltage": "22000", "substation": "distribution"}},
                {"id": 2, "lat": 13.75631, "lon": 100.50181,  # ~1.4m away
                 "tags": {"power": "substation", "voltage": "22000", "substation": "distribution"}},
            ],
            "ways": [],
            "relations": [],
        }
        result = analyser.run(osm_data)
        # Should find duplicate issue
        assert result.total_issues >= 1

    def test_invalid_transformer_count(self):
        analyser = PowerSubstationValidator(country="TH")
        osm_data = {
            "nodes": [
                {"id": 1, "lat": 13.7563, "lon": 100.5018,
                 "tags": {"power": "substation", "voltage": "22000", "substation": "distribution", "transformers": "0"}},
            ],
            "ways": [],
            "relations": [],
        }
        result = analyser.run(osm_data)
        assert result.total_issues >= 1

    def test_result_structure(self):
        analyser = PowerSubstationValidator(country="TH")
        result = analyser.run({"nodes": [], "ways": [], "relations": []})
        assert result.analyser == "power_substation_validator"
        assert result.country == "TH"
        assert "1" in result.issues_by_level
        assert "2" in result.issues_by_level
        assert "3" in result.issues_by_level
        assert isinstance(result.processing_time_ms, int)


# ---- PowerLineConnectivity Tests ----

class TestPowerLineConnectivity:
    def test_init(self):
        analyser = PowerLineConnectivity(country="TH")
        assert analyser.country == "TH"
        assert analyser.analyser_id == "power_line_connectivity"

    def test_valid_connected_line(self):
        analyser = PowerLineConnectivity(country="TH")
        osm_data = {
            "nodes": [
                {"id": 1, "lat": 13.7560, "lon": 100.5010, "tags": {"power": "substation", "voltage": "22000", "substation": "distribution"}},
                {"id": 2, "lat": 13.7570, "lon": 100.5020, "tags": {"power": "pole"}},
                {"id": 3, "lat": 13.7580, "lon": 100.5030, "tags": {"power": "substation", "voltage": "22000", "substation": "distribution"}},
            ],
            "ways": [
                {"id": 100, "nodes": [1, 2, 3], "tags": {"power": "line", "voltage": "22000"}},
            ],
            "relations": [],
        }
        result = analyser.run(osm_data)
        # No dangling ends, no missing voltage
        assert result.total_issues == 0

    def test_missing_voltage_on_line(self):
        analyser = PowerLineConnectivity(country="TH")
        osm_data = {
            "nodes": [
                {"id": 1, "lat": 13.7560, "lon": 100.5010, "tags": {}},
                {"id": 2, "lat": 13.7570, "lon": 100.5020, "tags": {}},
            ],
            "ways": [
                {"id": 100, "nodes": [1, 2], "tags": {"power": "line"}},
            ],
            "relations": [],
        }
        result = analyser.run(osm_data)
        assert result.total_issues >= 1

    def test_result_structure(self):
        analyser = PowerLineConnectivity(country="TH")
        result = analyser.run({"nodes": [], "ways": [], "relations": []})
        assert result.analyser == "power_line_connectivity"
        assert result.country == "TH"
        assert isinstance(result.total_issues, int)


# ---- DuplicateDetection Tests ----

class TestDuplicateDetection:
    def test_init(self):
        analyser = DuplicateDetection(country="TH")
        assert analyser.country == "TH"
        assert analyser.analyser_id == "duplicate_detection"
        assert analyser.pole_dist == 5.0

    def test_no_duplicates(self):
        analyser = DuplicateDetection(country="TH", pole_dist_m=5.0)
        osm_data = {
            "nodes": [
                {"id": 1, "lat": 13.7560, "lon": 100.5010, "tags": {"power": "pole"}},
                {"id": 2, "lat": 13.7570, "lon": 100.5020, "tags": {"power": "pole"}},  # ~140m away
            ],
            "ways": [],
            "relations": [],
        }
        result = analyser.run(osm_data)
        assert result.total_issues == 0

    def test_duplicate_poles(self):
        analyser = DuplicateDetection(country="TH", pole_dist_m=5.0)
        osm_data = {
            "nodes": [
                {"id": 1, "lat": 13.7563, "lon": 100.5018, "tags": {"power": "pole"}},
                {"id": 2, "lat": 13.75631, "lon": 100.50181, "tags": {"power": "pole"}},  # ~1.4m away
            ],
            "ways": [],
            "relations": [],
        }
        result = analyser.run(osm_data)
        assert result.total_issues >= 1
        assert result.issues_by_level["1"] >= 1  # HIGH level

    def test_duplicate_transformers(self):
        analyser = DuplicateDetection(country="TH", transformer_dist_m=5.0)
        osm_data = {
            "nodes": [
                {"id": 1, "lat": 13.7563, "lon": 100.5018, "tags": {"power": "transformer"}},
                {"id": 2, "lat": 13.75632, "lon": 100.50182, "tags": {"power": "transformer"}},  # ~2.8m away
            ],
            "ways": [],
            "relations": [],
        }
        result = analyser.run(osm_data)
        assert result.total_issues >= 1


# ---- MeterConflation Tests ----

class TestMeterConflation:
    def test_init(self):
        config = ConflationConfig(max_pole_distance_m=30.0)
        analyser = MeterConflation(country="TH", config=config)
        assert analyser.country == "TH"
        assert analyser.config.max_pole_distance_m == 30.0

    def test_match_to_pole(self):
        config = ConflationConfig(max_pole_distance_m=50.0)
        analyser = MeterConflation(country="TH", config=config)
        analyser.load_infrastructure(OSM_DATA_WITH_POLES)

        meters = [{"meter_id": "MTR_001", "lat": 13.7563, "lon": 100.5018}]
        result = analyser.run(meters)

        matches = [analyser._match_meter(m) for m in meters]
        assert len(matches) == 1
        assert matches[0].status == "matched"
        assert matches[0].matched_type == "pole"
        assert matches[0].distance_m < 1.0  # Same location

    def test_unmatched_meter(self):
        config = ConflationConfig(max_pole_distance_m=50.0)
        analyser = MeterConflation(country="TH", config=config)
        analyser.load_infrastructure(OSM_DATA_WITH_POLES)

        # Far from any infrastructure
        meters = [{"meter_id": "MTR_FAR", "lat": 13.8000, "lon": 100.6000}]
        result = analyser.run(meters)
        assert result.total_issues >= 1

    def test_match_summary(self):
        config = ConflationConfig(max_pole_distance_m=50.0)
        analyser = MeterConflation(country="TH", config=config)
        analyser.load_infrastructure(OSM_DATA_WITH_POLES)

        matches = [
            analyser._match_meter({"meter_id": f"MTR_{i}", "lat": 13.7563, "lon": 100.5018})
            for i in range(3)
        ]
        summary = analyser.get_match_summary(matches)
        assert summary["total_meters"] == 3
        assert "match_rate" in summary
        assert "avg_distance_m" in summary


# ---- GridQualityManager Integration Tests ----

class TestGridQualityManager:
    def test_create_manager(self):
        from smart_meter_simulator.osmose.grid_quality import create_quality_manager
        mgr = create_quality_manager()
        assert mgr is not None
        assert mgr.config.country == "TH"

    def test_validate_infrastructure(self):
        from smart_meter_simulator.osmose.grid_quality import create_quality_manager
        import asyncio

        mgr = create_quality_manager()
        osm_data = {
            "nodes": [
                {"id": 1, "lat": 13.7563, "lon": 100.5018,
                 "tags": {"power": "substation", "voltage": "22000", "substation": "distribution"}},
            ],
            "ways": [],
            "relations": [],
        }

        result = asyncio.run(mgr.validate_infrastructure(osm_data))
        assert result.analyser == "combined_infrastructure"
        assert result.country == "TH"
        assert isinstance(result.total_objects, int)

    def test_quality_score(self):
        from smart_meter_simulator.osmose.grid_quality import create_quality_manager
        mgr = create_quality_manager()
        score = mgr.get_quality_score()
        assert "overall" in score
        assert "infrastructure" in score
        assert "accuracy" in score
        assert score["overall"] == 100.0  # Default, no issues yet
