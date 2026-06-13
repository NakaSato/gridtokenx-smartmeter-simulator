import asyncio
from pathlib import Path

import pandapower as pp

from smart_meter_simulator.core.engine import SimulationEngine
from smart_meter_simulator.core.topology import GridBus, GridTransformer

REFERENCE_GLM_FILE = Path("src/smart_meter_simulator/data/grids/grid_bus_network.glm")


def _engine(meters: int = 40) -> SimulationEngine:
    engine = SimulationEngine(
        grid_topology=f"glm:{REFERENCE_GLM_FILE}", num_meters=meters
    )
    engine.grid.initialize_network(engine.meters)
    return engine


def test_tap_changer_moves_lv_head():
    """A raised HV tap must pull the LV feeder head down (and vice versa)."""
    engine = _engine()
    asyncio.run(engine.tick())
    grid = engine.grid
    net, idx, lv = grid.pp_net, grid.pp_trafo_idx, grid.pp_trafo_lv_idx
    assert idx is not None and lv is not None

    def lv_at(tap: int) -> float:
        net.trafo.at[idx, "tap_pos"] = tap
        pp.runpp(net, numba=False, algorithm="nr", init="dc", max_iteration=50)
        return float(net.res_bus.vm_pu.at[lv])

    # Monotone: more positive tap -> lower LV. Confirms tap_changer_type is live.
    assert lv_at(-4) > lv_at(0) > lv_at(4)


def test_oltc_regulates_head_into_band():
    engine = _engine()
    cfg = engine.config
    asyncio.run(engine.tick())
    grid = engine.grid
    vlv = float(grid.pp_net.res_bus.vm_pu.at[grid.pp_trafo_lv_idx])
    in_band = abs(vlv - cfg.transformer_oltc_v_target) <= cfg.transformer_oltc_deadband
    saturated = abs(grid.transformer_tap_pos) == cfg.transformer_tap_max
    assert in_band or saturated
    assert engine.last_tick_summary["transformer_tap_pos"] == grid.transformer_tap_pos


def test_oltc_disabled_holds_neutral_tap():
    engine = _engine()
    engine.config.transformer_oltc_enabled = False
    asyncio.run(engine.tick())
    assert engine.grid.transformer_tap_pos == 0


def test_per_unit_oltc_override_regulates_when_global_disabled():
    """A transformer with an explicit oltc_enabled=True override must regulate
    even when the global TRANSFORMER_OLTC_ENABLED default is off."""
    engine = _engine()
    engine.config.transformer_oltc_enabled = False
    topo = engine.grid.topology
    topo.buses.append(GridBus("mv_src", phases="ABC", nominal_voltage=12700))
    topo.transformers.append(
        GridTransformer(
            "feeder_tx",
            hv_bus="mv_src",
            lv_bus="ref_lv_bus_1",
            sn_mva=0.63,
            oltc_enabled=True,
        )
    )
    engine.grid.initialize_network(engine.meters)
    asyncio.run(engine.tick())
    grid = engine.grid
    cfg = engine.config

    tx = next(t for t in grid.pp_transformers if t["name"] == "feeder_tx")
    assert tx["oltc"] is True
    lv_vm = float(grid.pp_net.res_bus.vm_pu.at[tx["lv_idx"]])
    in_band = abs(lv_vm - cfg.transformer_oltc_v_target) <= cfg.transformer_oltc_deadband
    saturated = abs(tx["tap_pos"]) == cfg.transformer_tap_max
    assert in_band or saturated, f"LV={lv_vm} tap={tx['tap_pos']}"
