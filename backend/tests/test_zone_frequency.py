"""Per-zone frequency decoupling tests (Phase 3).

A commanded-islanded zone's frequency floats on only its own members'
supply/demand balance, decoupled from the utility-backed grid frequency that
connected/unzoned meters track. With nothing islanded the model collapses to a
single global frequency over all readings — identical to the pre-zone behaviour.
"""

import asyncio

import pytest

from smart_meter_simulator.core.engine import SimulationEngine

MZ_GLM = """
object node { name mv; bustype SWING; nominal_voltage 22000; }
object node { name z1_head; groupid 1; nominal_voltage 230; }
object node { name z1_a; groupid 1; nominal_voltage 230; }
object node { name z2_head; groupid 2; nominal_voltage 230; }
object node { name z2_a; groupid 2; nominal_voltage 230; }
object transformer { name pcc1; from mv; to z1_head; }
object transformer { name pcc2; from mv; to z2_head; }
object overhead_line { name l1; from z1_head; to z1_a; length 100 ft; }
object overhead_line { name l2; from z2_head; to z2_a; length 100 ft; }
"""


def _engine(tmp_path) -> SimulationEngine:
    glm = tmp_path / "mz.glm"
    glm.write_text(MZ_GLM, encoding="utf-8")
    engine = SimulationEngine(grid_topology=f"glm:{glm}", num_meters=5)
    engine.grid.initialize_network(engine.meters)
    # get_config() is a cached singleton another test may have toggled off;
    # this suite asserts droop behaviour, so pin it on regardless of run order.
    engine.config.freq_droop_enabled = True
    return engine


def test_freq_from_balance_direction(tmp_path):
    eng = _engine(tmp_path)
    nominal = eng.config.freq_nominal_hz
    assert eng._freq_from_balance(0.0, 0.0) == nominal
    assert eng._freq_from_balance(10.0, 5.0) > nominal  # surplus -> over-frequency
    assert eng._freq_from_balance(5.0, 10.0) < nominal  # deficit -> under-frequency


def test_no_island_keeps_single_global_frequency(tmp_path):
    eng = _engine(tmp_path)

    async def run():
        await eng.tick()
        # Nothing islanded: no per-zone frequency, grid freq is the all-readings
        # balance, every zone reports that same grid frequency.
        assert eng.zone_frequency_hz == {}
        total_gen = sum(r.energy_generated for r in eng.last_readings)
        total_load = sum(r.energy_consumed for r in eng.last_readings)
        assert eng.grid_frequency_hz == pytest.approx(
            eng._freq_from_balance(total_gen, total_load)
        )
        for z in eng.last_tick_summary["zones"]:
            assert z["frequency_hz"] == pytest.approx(eng.grid_frequency_hz)

    asyncio.run(run())


def test_islanded_zone_frequency_decouples_from_grid(tmp_path):
    eng = _engine(tmp_path)
    code_by_meter = {m.meter_id: m.config.get("zone_code", 0) for m in eng.meters}

    async def run():
        eng.zone_controller.island(1)
        await eng.tick()

        # Zone 1 now has its own frequency entry; zone 2 does not (still grid).
        assert set(eng.zone_frequency_hz) == {1}

        # Grid frequency is derived from everything NOT in islanded zone 1.
        g_gen = sum(
            r.energy_generated
            for r in eng.last_readings
            if code_by_meter.get(r.meter_id, 0) != 1
        )
        g_load = sum(
            r.energy_consumed
            for r in eng.last_readings
            if code_by_meter.get(r.meter_id, 0) != 1
        )
        assert eng.grid_frequency_hz == pytest.approx(
            eng._freq_from_balance(g_gen, g_load)
        )

        # Zone 1 frequency is derived from only zone-1 readings.
        z_gen = sum(
            r.energy_generated
            for r in eng.last_readings
            if code_by_meter.get(r.meter_id, 0) == 1
        )
        z_load = sum(
            r.energy_consumed
            for r in eng.last_readings
            if code_by_meter.get(r.meter_id, 0) == 1
        )
        assert eng.zone_frequency_hz[1] == pytest.approx(
            eng._freq_from_balance(z_gen, z_load)
        )

        # Summary surfaces the decoupled value for zone 1, grid value for zone 2.
        zones = {z["zone_code"]: z for z in eng.last_tick_summary["zones"]}
        assert zones[1]["frequency_hz"] == pytest.approx(eng.zone_frequency_hz[1])
        assert zones[2]["frequency_hz"] == pytest.approx(eng.grid_frequency_hz)

    asyncio.run(run())
