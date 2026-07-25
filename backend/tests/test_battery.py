"""BESS (battery energy storage) device + integration tests.

Covers GLM parsing of a dedicated-transformer battery node, the autonomous
frequency-reserve droop + congestion dispatch of the ``Battery`` device model,
its reserve-floor discipline, determinism, and the engine-level coupling where a
discharging battery raises grid generation and its SoC drops.
"""

import asyncio
from pathlib import Path

from smart_meter_simulator.adapters.glm_topology_loader import load_glm_topology
from smart_meter_simulator.core.engine import SimulationEngine
from smart_meter_simulator.devices.battery import Battery

# A 250 kW / 1000 kWh BESS on its own transformer node behind zone-1's PCC.
# Zone 1 has no PV, so the battery is the zone's only DER (island slack).
BESS_GLM = """
object node { name mv; bustype SWING; nominal_voltage 22000; }
object node { name z1_head; groupid 1; nominal_voltage 230; }
object node { name z1_bess; groupid 1; nominal_voltage 230; }
object transformer { name pcc1; from mv; to z1_head; }
object overhead_line { name l1; from z1_head; to z1_bess; length 100 ft; }
object inverter { name inv_b; parent z1_bess; rated_power 250000; }
object battery { name bat1; parent inv_b; battery_capacity 1000000; }
"""


def _write_glm(tmp_path) -> Path:
    glm = tmp_path / "bess.glm"
    glm.write_text(BESS_GLM, encoding="utf-8")
    return glm


def _battery(**overrides) -> Battery:
    cfg = {
        "meter_id": "bat-test",
        "meter_type": "BESS",
        "has_battery": True,
        "battery_power_kw": 100.0,
        "battery_capacity_kwh": 200.0,
        "battery_soc_init": 0.6,
        "battery_soc_min": 0.1,
        "battery_soc_max": 0.95,
        "battery_reserve_soc_floor": 0.3,
        "battery_droop_percent": 5.0,
        "battery_freq_deadband_hz": 0.05,
        "battery_congest_high_pct": 90.0,
        "battery_congest_low_pct": 80.0,
    }
    cfg.update(overrides)
    return Battery(cfg)


# --- GLM parsing -----------------------------------------------------------


def test_battery_object_parsed_into_topology(tmp_path):
    topo = load_glm_topology(_write_glm(tmp_path))
    assert len(topo.batteries) == 1
    bat = topo.batteries[0]
    assert bat.bus == "z1_bess"  # resolved through the inverter parent
    assert bat.power_kw == 250.0  # inverter rated_power / 1000
    assert bat.energy_kwh == 1000.0  # battery_capacity Wh / 1000


def test_battery_bus_is_der_slack_in_pv_less_zone(tmp_path):
    topo = load_glm_topology(_write_glm(tmp_path))
    # No PV anywhere, yet zone 1 gets a DER bus (the BESS) and is islandable.
    assert topo.zones[1].der_bus == "z1_bess"
    assert topo.zones[1].islandable is True


# --- Device dispatch -------------------------------------------------------


def test_discharge_on_underfrequency(tmp_path):
    bat = _battery()
    soc0 = bat.soc
    disp = bat.dispatch(
        frequency_hz=49.0, transformer_loading_pct=0.0, interval_seconds=900
    )
    assert disp > 0  # deficit -> discharge (grid injection)
    assert bat.soc < soc0  # SoC drained


def test_charge_on_overfrequency(tmp_path):
    bat = _battery()
    soc0 = bat.soc
    disp = bat.dispatch(
        frequency_hz=51.0, transformer_loading_pct=0.0, interval_seconds=900
    )
    assert disp < 0  # surplus -> charge (load)
    assert bat.soc > soc0


def test_deadband_no_dispatch_near_nominal(tmp_path):
    bat = _battery()
    disp = bat.dispatch(
        frequency_hz=50.02, transformer_loading_pct=0.0, interval_seconds=900
    )
    assert disp == 0.0


def test_droop_respects_reserve_floor(tmp_path):
    # SoC sitting exactly on the reserve floor: frequency droop cannot discharge.
    bat = _battery(battery_soc_init=0.3)
    disp = bat.dispatch(
        frequency_hz=48.0, transformer_loading_pct=0.0, interval_seconds=900
    )
    assert disp == 0.0  # no headroom above the reserve floor for droop


def test_congestion_discharges_into_reserve(tmp_path):
    # At the reserve floor, congestion (unlike droop) may draw down to soc_min.
    bat = _battery(battery_soc_init=0.3)
    disp = bat.dispatch(
        frequency_hz=50.0, transformer_loading_pct=95.0, interval_seconds=900
    )
    assert disp > 0  # congestion relief taps the reserve


def test_congestion_hysteresis_holds_between_bands(tmp_path):
    bat = _battery()
    # Cross the high threshold -> discharge ramps in.
    d_high = bat.dispatch(50.0, 92.0, 900)
    assert d_high > 0
    # Loading falls into the hold band (80..90) -> keep discharging (no toggle).
    d_hold = bat.dispatch(50.0, 85.0, 900)
    assert d_hold > 0
    # Below the low threshold -> release.
    d_release = bat.dispatch(50.0, 70.0, 900)
    assert d_release == 0.0


def test_dispatch_is_deterministic(tmp_path):
    a = _battery()
    b = _battery()
    seq = [(49.5, 0.0), (49.0, 95.0), (51.0, 0.0), (50.5, 88.0)]
    for f, load in seq:
        assert a.dispatch(f, load, 900) == b.dispatch(f, load, 900)
    assert a.soc == b.soc


# --- Engine integration ----------------------------------------------------


def test_engine_underfrequency_discharges_bess(tmp_path):
    engine = SimulationEngine(grid_topology=f"glm:{_write_glm(tmp_path)}", num_meters=5)
    engine.grid.initialize_network(engine.meters)

    async def run():
        # Force an under-frequency signal onto the storage meter(s) for this tick.
        bess_meters = [m for m in engine.meters if getattr(m, "battery", None)]
        assert bess_meters, "expected a BESS meter on the battery node"
        soc_before = bess_meters[0].battery.soc
        for m in bess_meters:
            m.receive_frequency(49.0)

        await engine.tick()

        reading = next(
            r for r in engine.last_readings if r.meter_id == bess_meters[0].meter_id
        )
        assert reading.battery_dispatch_kw is not None
        assert reading.battery_dispatch_kw > 0  # discharging
        assert reading.energy_generated > 0  # discharge shows as generation
        assert bess_meters[0].battery.soc < soc_before  # SoC drained
        summary = engine.last_tick_summary
        assert summary["total_battery_discharge_kw"] > 0
        assert summary["battery_count"] >= 1
        assert summary["avg_battery_soc_pct"] is not None

    asyncio.run(run())
