import asyncio
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest
from fastapi import HTTPException

from smart_meter_simulator.adapters import GlmTopologyAdapter
from smart_meter_simulator.config.settings import SimulatorConfig
from smart_meter_simulator.core import app_state
from smart_meter_simulator.core.engine import SimulationEngine
from smart_meter_simulator.core.grid_manager import GridManager

from smart_meter_simulator.core.topology_factory import (
    load_glm_core_topology,
    load_topology_spec,
    parse_topology_spec,
)
from smart_meter_simulator.core.topology import GridBus, GridLine, GridTopology
from smart_meter_simulator.devices.load import Load
from smart_meter_simulator.devices.solar import Solar
from smart_meter_simulator.meter_generator import MeterGenerator
from smart_meter_simulator.models import EnergyReading
from smart_meter_simulator.routers import grid_v1, simulation_v1


REFERENCE_GLM_FILE = Path("src/smart_meter_simulator/data/grids/grid_bus_network.glm")


def test_reference_glm_loads_as_core_topology():
    topology = load_glm_core_topology(REFERENCE_GLM_FILE)

    assert len(topology.buses) == 80
    assert len(topology.lines) == 79
    assert len(topology.loads) == 32
    # Partial-penetration reference: 15 of the 80 buses carry a 10 kW PV (150 kW total).
    assert len(topology.pvs) == 15
    assert sum(pv.capacity_kw for pv in topology.pvs) == pytest.approx(150.0, abs=0.1)
    assert all(pv.capacity_kw == pytest.approx(10.0, abs=0.01) for pv in topology.pvs)
    assert {pv.bus for pv in topology.pvs} <= set(topology.bus_names)
    assert len({pv.bus for pv in topology.pvs}) == 15
    assert topology.get_substation_bus() == "ref_lv_bus_1"
    assert topology.validate().is_valid


def test_grid_topology_spec_loads_reference_glm():
    topology = load_topology_spec(f"glm:{REFERENCE_GLM_FILE}")

    assert parse_topology_spec(f"glm:{REFERENCE_GLM_FILE}") == (
        "glm",
        str(REFERENCE_GLM_FILE),
    )
    assert len(topology.buses) == 80
    assert topology.validate().is_valid


def test_glm_line_configuration_impedance_feeds_core_line_model(tmp_path):
    glm_file = tmp_path / "configured_line.glm"
    glm_file.write_text(
        """
        object node {
            name source;
            bustype SWING;
            nominal_voltage 230;
        }
        object node {
            name load_bus;
            nominal_voltage 230;
        }
        object line_configuration {
            name config_a;
            z11 0.804672+0.1609344j ohm/mile;
            z22 0.804672+0.1609344j ohm/mile;
            z33 0.804672+0.1609344j ohm/mile;
            capacity_kw 125;
        }
        object overhead_line {
            name line_source_load;
            from source;
            to load_bus;
            length 1 km;
            configuration config_a;
        }
        """,
        encoding="utf-8",
    )

    topology = load_glm_core_topology(glm_file)
    line = topology.lines[0]

    assert line.length == pytest.approx(1.0)
    assert line.length_unit == "km"
    assert line.resistance_ohm_per_km == pytest.approx(0.5)
    assert line.reactance_ohm_per_km == pytest.approx(0.1)
    assert line.capacity_kw == pytest.approx(125.0)
    assert line.properties["configuration"] == "config_a"


def test_config_defaults_grid_topology_to_reference_glm(monkeypatch):
    monkeypatch.delenv("GRID_TOPOLOGY", raising=False)
    monkeypatch.delenv("NUM_METERS", raising=False)

    config = SimulatorConfig(_env_file=None)
    topology = load_glm_core_topology(REFERENCE_GLM_FILE)

    assert config.grid_topology == f"glm:{REFERENCE_GLM_FILE}"
    assert config.simulation_interval == 15
    assert config.num_meters == len(topology.buses)
    assert config.pv_on_every_bus is True
    assert config.bus_pv_capacity_min_kw == 10.0
    assert config.bus_pv_capacity_max_kw == 10.0


def test_engine_uses_glm_core_topology_without_adapter():
    engine = SimulationEngine(grid_topology=f"glm:{REFERENCE_GLM_FILE}", num_meters=5)
    engine.grid.initialize_network(engine.meters)

    assert len(engine.meters) == 80
    assert all(meter.config["has_solar"] for meter in engine.meters)
    assert all(meter.config["solar_capacity"] == 10.0 for meter in engine.meters)
    assert [meter.config["bus_idx"] for meter in engine.meters] == list(range(80))
    assert [meter.config["node_id"] for meter in engine.meters] == [
        bus.name for bus in engine.grid.topology.buses
    ]
    assert engine.grid.adapter is None
    assert engine.grid.topology is not None
    assert len(engine.grid.meter_to_bus) == 80

    summary = engine.grid.get_topology_summary()
    assert summary["mode"] == "glm_topology"
    assert summary["num_buses"] == 80
    assert summary["num_lines"] == 79
    assert summary["num_loads"] == 32
    assert summary["num_pv"] == 15
    assert summary["pv_capacity_kw"] == pytest.approx(150.0, abs=0.1)
    assert summary["mapped_meters"] == 80
    assert summary["validation"]["is_valid"]


def test_grid_topology_endpoint_returns_core_topology_shape():
    engine = SimulationEngine(grid_topology=f"glm:{REFERENCE_GLM_FILE}", num_meters=5)
    engine.grid.initialize_network(engine.meters)
    previous_engine = app_state.engine
    app_state.engine = engine

    try:
        response = asyncio.run(grid_v1.grid_topology())
    finally:
        app_state.engine = previous_engine

    topology = response["topology"]
    assert topology["source"] == "glm"
    assert topology["source_path"] == str(REFERENCE_GLM_FILE)
    assert topology["mode"] == "glm_topology"
    assert topology["num_buses"] == 80
    assert topology["num_lines"] == 79
    assert topology["num_static_loads"] == 32
    assert topology["num_pv"] == 15
    assert topology["pv_capacity_kw"] == pytest.approx(150.0, abs=0.1)
    assert topology["substation"] == "ref_lv_bus_1"
    assert topology["validation"]["is_valid"]
    assert topology["meters"] == 80
    assert all(bus["has_solar"] for bus in response["buses"].values())
    assert response["buses"]["0"]["node_id"] == "ref_lv_bus_1"
    assert response["buses"]["0"]["solar_capacity_kw"] > 0


def test_environment_topology_switch_accepts_glm_spec():
    engine = SimulationEngine(grid_topology=f"glm:{REFERENCE_GLM_FILE}", num_meters=5)
    engine.grid.initialize_network(engine.meters)

    response = asyncio.run(
        simulation_v1.update_environment(
            weather=None,
            grid_stress=None,
            topology=f"glm:{REFERENCE_GLM_FILE}",
            engine=engine,
        )
    )

    assert response["status"] == "updated"
    assert response["topology_spec"] == f"glm:{REFERENCE_GLM_FILE}"
    assert response["topology"]["source"] == "glm"
    assert response["topology"]["mapped_meters"] == 80


def test_environment_topology_switch_rejects_non_glm_spec():
    engine = SimulationEngine(grid_topology=f"glm:{REFERENCE_GLM_FILE}", num_meters=5)

    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(
            simulation_v1.update_environment(
                weather=None, grid_stress=None, topology="ieee123", engine=engine
            )
        )

    assert exc_info.value.status_code == 400
    assert "Unsupported topology spec" in exc_info.value.detail


def test_grid_manager_converts_interval_energy_to_kw_load():
    engine = SimulationEngine(grid_topology=f"glm:{REFERENCE_GLM_FILE}", num_meters=1)
    engine.grid.initialize_network(engine.meters)
    meter = engine.meters[0]
    bus = engine.grid.meter_to_bus[meter.meter_id]

    reading = EnergyReading(
        meter_id=meter.meter_id,
        timestamp=datetime.now(timezone.utc),
        energy_generated=0.0,
        energy_consumed=15 / 3600,
        surplus_energy=0.0,
        deficit_energy=15 / 3600,
        interval_seconds=15,
        location="test",
        meter_type="Grid_Consumer",
        user_type="Consumer",
    )

    engine.grid.update_grid_state(engine.meters, [reading])

    assert engine.grid.bus_load[bus] == pytest.approx(1.0)


def test_zip_load_voltage_response_scales_with_voltage():
    base_kw = 10.0

    low_voltage_kw = Load.apply_zip_voltage_response(
        base_kw,
        voltage_pu=0.95,
        z_fraction=0.2,
        i_fraction=0.3,
        p_fraction=0.5,
    )
    high_voltage_kw = Load.apply_zip_voltage_response(
        base_kw,
        voltage_pu=1.05,
        z_fraction=0.2,
        i_fraction=0.3,
        p_fraction=0.5,
    )

    assert low_voltage_kw < base_kw
    assert high_voltage_kw > base_kw


def test_pv_model_generates_daytime_power_only():
    solar = Solar(
        {
            "solar_capacity": 5.0,
            "latitude": 13.75,
            "longitude": 100.5,
            "pv_tilt_deg": 15.0,
            "pv_azimuth_deg": 180.0,
        }
    )
    tz = ZoneInfo("Asia/Bangkok")

    midday_kw = solar.get_generation_kw(datetime(2026, 4, 1, 12, 0, tzinfo=tz), "Sunny")
    midnight_kw = solar.get_generation_kw(
        datetime(2026, 4, 1, 0, 0, tzinfo=tz), "Sunny"
    )

    assert midday_kw > 0.0
    assert midnight_kw == pytest.approx(0.0, abs=0.05)


def test_distflow_uses_line_impedance_and_distance():
    topology = GridTopology(
        source="test",
        buses=[
            GridBus(
                name="source", nominal_voltage=230.0, properties={"bustype": "SWING"}
            ),
            GridBus(name="load_bus", nominal_voltage=230.0),
        ],
        lines=[
            GridLine(
                name="line_source_load",
                from_bus="source",
                to_bus="load_bus",
                length=1.0,
                length_unit="km",
                resistance_ohm_per_km=0.5,
                reactance_ohm_per_km=0.1,
                capacity_kw=100.0,
            )
        ],
    )
    grid = GridManager(topology=topology)
    meter = type("Meter", (), {"meter_id": "meter_1", "config": {"bus_idx": 1}})()
    grid.initialize_network([meter])
    # This test targets the distflow fallback (lossless downstream flow accounting).
    # pandapower is a hard dependency and would otherwise take precedence, so disable it.
    grid.pp_net = None

    reading = EnergyReading(
        meter_id="meter_1",
        timestamp=datetime.now(timezone.utc),
        energy_generated=0.0,
        energy_consumed=15 / 3600,
        surplus_energy=0.0,
        deficit_energy=15 / 3600,
        interval_seconds=15,
        reactive_power_kvar=0.2,
        location="test",
        meter_type="Grid_Consumer",
        user_type="Consumer",
    )

    grid.update_grid_state([meter], [reading])
    line_state = grid.get_line_state("line_source_load")

    assert grid.bus_voltages["load_bus"] < 1.0
    assert line_state["resistance_ohm"] == pytest.approx(0.5)
    assert line_state["reactance_ohm"] == pytest.approx(0.1)
    assert line_state["flow_kw"] == pytest.approx(1.0)
    assert line_state["flow_kvar"] == pytest.approx(0.2)
    assert line_state["loss_kw"] > 0


def test_glm_topology_adapter_loads_reference_glm():
    adapter = GlmTopologyAdapter(str(REFERENCE_GLM_FILE))

    assert adapter.get_bus_count() == 80
    assert adapter.get_line_count() == 79
    assert adapter.get_load_count() == 32
    assert adapter.get_substation_bus() == "ref_lv_bus_1"
    assert adapter.validation.is_valid


def test_ieee_meter_generation_honors_target_count():
    meters = MeterGenerator(5).generate_ieee_meters(
        num_nodes=80,
        target_meters=5,
        node_ids=[f"ref_lv_bus_{idx + 1}" for idx in range(80)],
    )

    assert len(meters) == 5
    assert [meter["bus_idx"] for meter in meters] == [0, 16, 32, 48, 64]
    assert [meter["node_id"] for meter in meters] == [
        "ref_lv_bus_1",
        "ref_lv_bus_17",
        "ref_lv_bus_33",
        "ref_lv_bus_49",
        "ref_lv_bus_65",
    ]


def test_ieee_meter_generation_can_put_pv_on_every_bus():
    meters = MeterGenerator(2).generate_ieee_meters(
        num_nodes=4,
        target_meters=2,
        pv_on_every_bus=True,
        node_ids=["node_a", "node_b", "node_c", "node_d"],
        pv_capacity_kw_by_node={
            "node_a": 10.0,
            "node_b": 10.0,
            "node_c": 10.0,
            "node_d": 10.0,
        },
    )

    assert len(meters) == 4
    assert [meter["bus_idx"] for meter in meters] == [0, 1, 2, 3]
    assert [meter["node_id"] for meter in meters] == [
        "node_a",
        "node_b",
        "node_c",
        "node_d",
    ]
    assert {meter["meter_type"] for meter in meters} == {"Solar_Prosumer"}
    assert all(meter["has_solar"] for meter in meters)
    assert all(meter["solar_capacity"] == 10.0 for meter in meters)


def test_meter_generation_uses_glm_pv_capacity_by_node():
    meters = MeterGenerator(2).generate_ieee_meters(
        num_nodes=2,
        target_meters=2,
        pv_on_every_bus=True,
        node_ids=["node_a", "node_b"],
        pv_capacity_kw_by_node={"node_a": 3.5, "node_b": 7.25},
    )

    assert [meter["node_id"] for meter in meters] == ["node_a", "node_b"]
    assert [meter["solar_capacity"] for meter in meters] == [3.5, 7.25]
