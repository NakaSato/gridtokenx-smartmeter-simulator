"""
Tests for Thailand Power Plant Registry.
"""

import pytest

from smart_meter_simulator.core.power_plants import (
    PowerPlant,
    PowerPlantRegistry,
    FuelType,
    PlantRegion,
    CARBON_INTENSITY,
    PLANTS,
    get_registry,
    reset_registry,
)


# ============================================================================
# PowerPlant Model Tests
# ============================================================================

class TestPowerPlantModel:
    def test_carbon_intensity(self):
        plant = PowerPlant("test", "Test", "ทดสอบ", FuelType.COAL,
                           PlantRegion.CENTRAL, "Test", 100)
        assert plant.carbon_intensity == 820

    def test_carbon_intensity_default(self):
        plant = PowerPlant("test", "Test", "ทดสอบ", FuelType.NUCLEAR,
                           PlantRegion.NORTH, "Test", 100)
        assert plant.carbon_intensity == 12

    def test_is_renewable_solar(self):
        plant = PowerPlant("test", "Test", "ทดสอบ", FuelType.SOLAR,
                           PlantRegion.NORTHEAST, "Test", 100)
        assert plant.is_renewable is True

    def test_is_renewable_gas(self):
        plant = PowerPlant("test", "Test", "ทดสอบ", FuelType.NATURAL_GAS,
                           PlantRegion.EAST, "Test", 100)
        assert plant.is_renewable is False

    def test_is_dispatchable_gas(self):
        plant = PowerPlant("test", "Test", "ทดสอบ", FuelType.NATURAL_GAS,
                           PlantRegion.EAST, "Test", 100)
        assert plant.is_dispatchable is True

    def test_is_dispatchable_solar(self):
        plant = PowerPlant("test", "Test", "ทดสอบ", FuelType.SOLAR,
                           PlantRegion.NORTHEAST, "Test", 100)
        assert plant.is_dispatchable is False

    def test_is_dispatchable_hydro(self):
        plant = PowerPlant("test", "Test", "ทดสอบ", FuelType.HYDRO,
                           PlantRegion.NORTH, "Test", 100)
        assert plant.is_dispatchable is True


# ============================================================================
# Registry Query Tests
# ============================================================================

class TestRegistryQueries:
    @pytest.fixture(autouse=True)
    def setup(self):
        # Use real plants for each test
        reset_registry(list(PLANTS))
        yield
        reset_registry()

    def test_list_all_defaults(self):
        registry = get_registry()
        plants = registry.list_all()
        assert len(plants) > 0

    def test_list_by_fuel(self):
        registry = get_registry()
        plants = registry.list_all(fuel=FuelType.NATURAL_GAS)
        assert all(p.fuel == FuelType.NATURAL_GAS for p in plants)
        assert len(plants) > 0

    def test_list_by_region(self):
        registry = get_registry()
        plants = registry.list_all(region=PlantRegion.SOUTH)
        assert all(p.region == PlantRegion.SOUTH for p in plants)

    def test_list_by_status(self):
        registry = get_registry()
        plants = registry.list_all(status="operational")
        assert all(p.status == "operational" for p in plants)

    def test_list_decommissioned(self):
        registry = get_registry()
        plants = registry.list_all(status="decommissioned")
        assert all(p.status == "decommissioned" for p in plants)
        assert len(plants) > 0  # Krabi should be there

    def test_list_limit(self):
        registry = get_registry()
        plants = registry.list_all(limit=3)
        assert len(plants) <= 3

    def test_get_by_id(self):
        registry = get_registry()
        plant = registry.get_by_id("bangpakong")
        assert plant is not None
        assert plant.name == "Bang Pakong"
        assert plant.capacity_mw == 3500

    def test_get_by_id_not_found(self):
        registry = get_registry()
        plant = registry.get_by_id("nonexistent")
        assert plant is None

    def test_search_by_name_en(self):
        registry = get_registry()
        results = registry.search("bang")
        assert any("Bang" in p.name for p in results)

    def test_search_by_name_th(self):
        registry = get_registry()
        results = registry.search("แม่เมาะ")
        assert any(p.name_th == "แม่เมาะ" for p in results)

    def test_search_no_match(self):
        registry = get_registry()
        results = registry.search("xyznonexistent")
        assert len(results) == 0


# ============================================================================
# Nearby Search Tests
# ============================================================================

class TestNearbySearch:
    @pytest.fixture(autouse=True)
    def setup(self):
        reset_registry(list(PLANTS))
        yield
        reset_registry()

    def test_nearby_bangkok(self):
        registry = get_registry()
        plants = registry.nearby(13.75, 100.50, radius_km=30)
        # Should find South Bangkok, Nong Chok
        assert len(plants) > 0
        names = [p.name for p in plants]
        assert any("Bangkok" in n or "Nong" in n for n in names)

    def test_nearby_sorted_by_distance(self):
        registry = get_registry()
        plants = registry.nearby(13.60, 100.90, radius_km=200)
        # Closest should be Bang Pakong (exact coordinates)
        assert len(plants) > 1
        # First should be the closest
        assert plants[0].id == "bangpakong"

    def test_nearby_no_results(self):
        registry = get_registry()
        # Middle of ocean
        plants = registry.nearby(0.0, 0.0, radius_km=10)
        assert len(plants) == 0

    def test_nearby_wide_radius(self):
        registry = get_registry()
        plants = registry.nearby(13.75, 100.50, radius_km=500)
        # Should catch most plants in central Thailand
        assert len(plants) > 5


# ============================================================================
# Stats Tests
# ============================================================================

class TestStats:
    @pytest.fixture(autouse=True)
    def setup(self):
        reset_registry(list(PLANTS))
        yield
        reset_registry()

    def test_stats_has_data(self):
        registry = get_registry()
        stats = registry.stats()
        assert stats["total_plants"] > 0
        assert stats["total_capacity_mw"] > 0

    def test_stats_capacity_reasonable(self):
        registry = get_registry()
        stats = registry.stats()
        # Thai grid should be >10,000 MW
        assert stats["total_capacity_mw"] > 10000

    def test_stats_by_fuel(self):
        registry = get_registry()
        stats = registry.stats()
        assert "natural_gas" in stats["by_fuel"]
        assert stats["by_fuel"]["natural_gas"] > 0

    def test_stats_renewable_percentage(self):
        registry = get_registry()
        stats = registry.stats()
        assert "renewable_mw" in stats
        assert "renewable_pct" in stats
        assert 0 < stats["renewable_pct"] < 100

    def test_stats_carbon_intensity(self):
        registry = get_registry()
        stats = registry.stats()
        # Thai grid avg ~400-500 gCO2/kWh
        assert 200 < stats["avg_carbon_intensity_gco2_kwh"] < 800

    def test_stats_by_region(self):
        registry = get_registry()
        stats = registry.stats()
        assert len(stats["by_region"]) > 0


# ============================================================================
# Group By Tests
# ============================================================================

class TestGroupBy:
    @pytest.fixture(autouse=True)
    def setup(self):
        reset_registry(list(PLANTS))
        yield
        reset_registry()

    def test_group_by_fuel(self):
        registry = get_registry()
        groups = registry.group_by("fuel")
        assert "natural_gas" in groups
        assert len(groups["natural_gas"]) > 1

    def test_group_by_region(self):
        registry = get_registry()
        groups = registry.group_by("region")
        assert "south" in groups
        assert "north" in groups
        assert "northeast" in groups

    def test_group_records_have_id(self):
        registry = get_registry()
        groups = registry.group_by("fuel")
        for group_name, records in groups.items():
            for rec in records:
                assert "id" in rec
                assert "capacity_mw" in rec
                assert "name" in rec


# ============================================================================
# Custom Registry Tests
# ============================================================================

class TestCustomRegistry:
    def test_custom_plants(self):
        custom = [
            PowerPlant("custom1", "Custom Plant", "พืชทดสอบ",
                       FuelType.SOLAR, PlantRegion.CENTRAL, "Test",
                       capacity_mw=50, lat=14.0, lon=100.0),
        ]
        registry = PowerPlantRegistry(custom)
        plants = registry.list_all()
        assert len(plants) == 1
        assert plants[0].id == "custom1"

    def test_empty_registry(self):
        empty = PowerPlantRegistry([])
        assert len(empty.plants) == 0
        stats = empty.stats()
        assert stats["total_plants"] == 0
        assert stats["total_capacity_mw"] == 0


# ============================================================================
# Dataset Integrity Tests
# ============================================================================

class TestDatasetIntegrity:
    def test_all_plants_have_coordinates(self):
        for p in PLANTS:
            if p.status == "operational":
                assert p.lat != 0.0, f"{p.name} missing lat"
                assert p.lon != 0.0, f"{p.name} missing lon"

    def test_all_plants_have_positive_capacity(self):
        for p in PLANTS:
            assert p.capacity_mw > 0, f"{p.name} has zero/negative capacity"

    def test_all_fuel_types_have_carbon_intensity(self):
        for ft in FuelType:
            assert ft in CARBON_INTENSITY, f"Missing carbon for {ft}"

    def test_no_duplicate_ids(self):
        ids = [p.id for p in PLANTS]
        assert len(ids) == len(set(ids)), "Duplicate plant IDs found"

    def test_minimum_plants_count(self):
        # Should have at least 20 plants in the dataset
        assert len(PLANTS) >= 20

    def test_largest_plant(self):
        largest = max(PLANTS, key=lambda p: p.capacity_mw)
        # Ratchaburi should be one of the largest
        assert largest.capacity_mw >= 3000
