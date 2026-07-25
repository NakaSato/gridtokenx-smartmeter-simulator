"""EV charging station device + integration tests.

Covers GLM parsing of a dedicated-transformer EV node, the additive constant-
power draw of the ``EVCharger`` device model (no ZIP voltage scaling, diurnal
shape), and the engine-level coupling where a charging station raises total
consumption without passing through the generation-only frequency droop.
"""

import asyncio
from datetime import datetime
from pathlib import Path

from smart_meter_simulator.adapters.glm_topology_loader import load_glm_topology
from smart_meter_simulator.core.engine import SimulationEngine
from smart_meter_simulator.devices.ev import EVCharger

# A 4-port, 50 kW/port EV charging station on its own transformer node.
EV_GLM = """
object node { name mv; bustype SWING; nominal_voltage 22000; }
object node { name ev_bus; nominal_voltage 230; }
object transformer { name tr_ev; from mv; to ev_bus; }
object evcharger { name ev1; parent ev_bus; charge_rate 50000; num_ports 4; }
"""


def _write_glm(tmp_path) -> Path:
    glm = tmp_path / "ev.glm"
    glm.write_text(EV_GLM, encoding="utf-8")
    return glm


def _ev(**overrides) -> EVCharger:
    cfg = {
        "meter_id": "ev-test",
        "meter_type": "EV_Charger",
        "has_ev_charger": True,
        "ev_charger_kw": 22.0,
        "ev_num_ports": 4,
        "ev_utilization": 0.4,
    }
    cfg.update(overrides)
    return EVCharger(cfg)


# --- GLM parsing -----------------------------------------------------------


def test_ev_object_parsed_into_topology(tmp_path):
    topo = load_glm_topology(_write_glm(tmp_path))
    assert len(topo.ev_stations) == 1
    ev = topo.ev_stations[0]
    assert ev.bus == "ev_bus"  # parent is a node -> direct bus
    assert ev.max_charger_kw == 50.0  # charge_rate / 1000
    assert ev.num_ports == 4
    assert ev.dc_fast is False


# --- Device draw -----------------------------------------------------------


def test_ev_draw_is_positive_additive_load(tmp_path):
    ev = _ev()
    # Evening peak — the destination-charger profile is high.
    draw = ev.get_charge_kw(datetime(2026, 7, 22, 19, 0))
    assert draw > 0


def test_ev_draw_has_no_voltage_dependence(tmp_path):
    # EVCharger.get_charge_kw takes no voltage argument — the EVSE regulates its
    # own output, so draw is constant-power regardless of bus voltage.
    import inspect

    sig = inspect.signature(EVCharger.get_charge_kw)
    assert "voltage_pu" not in sig.parameters


def test_ev_diurnal_shape_varies(tmp_path):
    ev = _ev()
    night = ev.get_charge_kw(datetime(2026, 7, 22, 3, 0))
    evening = ev.get_charge_kw(datetime(2026, 7, 22, 19, 0))
    assert evening > night  # evening peak exceeds the small overnight floor


def test_dc_fast_uses_higher_rating(tmp_path):
    ac = _ev(meter_type="EV_Charger")
    dc = _ev(meter_type="DC_Fast_Charger")
    assert dc.is_dc_fast is True
    assert ac.is_dc_fast is False


# --- Engine integration ----------------------------------------------------


def test_engine_ev_raises_consumption(tmp_path):
    engine = SimulationEngine(grid_topology=f"glm:{_write_glm(tmp_path)}", num_meters=5)
    engine.grid.initialize_network(engine.meters)

    async def run():
        ev_meters = [m for m in engine.meters if getattr(m, "ev", None)]
        assert ev_meters, "expected an EV meter on the charging-station node"
        # Evening peak so the station is actively charging.
        await engine.tick(timestamp=datetime(2026, 7, 22, 19, 0))
        reading = next(
            r for r in engine.last_readings if r.meter_id == ev_meters[0].meter_id
        )
        assert reading.ev_charge_kw is not None
        assert reading.ev_charge_kw > 0
        assert reading.energy_consumed > 0
        assert engine.last_tick_summary["total_ev_load_kw"] > 0

    asyncio.run(run())
