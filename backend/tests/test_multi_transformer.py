"""Multi / nested transformer support in the pandapower build.

Injects a two-transformer cascade (MV/MV coupler -> MV/LV feeder head) above
the reference GLM's LV substation bus and checks that both transformers are
built, solved, OLTC-regulated, and surfaced — while a single external-grid
slack lands on the grid-edge HV bus.
"""

import asyncio
from pathlib import Path

import pytest

from smart_meter_simulator.adapters.glm_topology_loader import load_glm_topology
from smart_meter_simulator.core.engine import SimulationEngine
from smart_meter_simulator.core.topology import GridBus, GridTransformer

_GLM_WITH_TRANSFORMER = """
object node { name mv_src; phases ABCN; nominal_voltage 12700; }
object node { name lv_head; phases ABCN; nominal_voltage 240; }
object transformer_configuration {
    name xfmr_cfg;
    connect_type WYE_WYE;
    power_rating 500;
    primary_voltage 12700;
    secondary_voltage 240;
    resistance 0.011;
    reactance 0.02;
}
object transformer {
    name feeder_tx;
    phases ABCN;
    from mv_src;
    to lv_head;
    configuration xfmr_cfg;
}
"""


def test_glm_loader_parses_transformer(tmp_path):
    glm = tmp_path / "tx.glm"
    glm.write_text(_GLM_WITH_TRANSFORMER)
    topo = load_glm_topology(glm)
    assert len(topo.transformers) == 1
    tx = topo.transformers[0]
    assert tx.name == "feeder_tx"
    assert tx.hv_bus == "mv_src"
    assert tx.lv_bus == "lv_head"
    assert tx.sn_mva == 0.5  # 500 kVA
    assert abs(tx.vkr_percent - 1.1) < 1e-9  # R 0.011 pu
    assert abs(tx.vk_percent - ((0.011**2 + 0.02**2) ** 0.5) * 100.0) < 1e-9
    assert topo.validate().is_valid


REFERENCE_GLM_FILE = Path("src/smart_meter_simulator/data/grids/grid_bus_network.glm")


def _engine_with_cascade(meters: int = 40) -> SimulationEngine:
    engine = SimulationEngine(
        grid_topology=f"glm:{REFERENCE_GLM_FILE}", num_meters=meters
    )
    topo = engine.grid.topology
    # Two new MV buses (12.7 kV L-N -> ~22 kV L-L on a 3-phase base) and a
    # cascade: grid -> hv_tx (MV/MV) -> mv_mid -> feeder_tx (MV/LV) -> the LV
    # substation bus the GLM feeder already hangs off.
    topo.buses.append(GridBus("mv_src", phases="ABC", nominal_voltage=12700))
    topo.buses.append(GridBus("mv_mid", phases="ABC", nominal_voltage=12700))
    topo.transformers.append(
        GridTransformer("hv_tx", hv_bus="mv_src", lv_bus="mv_mid", sn_mva=2.0)
    )
    topo.transformers.append(
        GridTransformer(
            "feeder_tx", hv_bus="mv_mid", lv_bus="ref_lv_bus_1", sn_mva=0.63
        )
    )
    engine.grid.initialize_network(engine.meters)
    return engine


def test_builds_both_transformers_with_single_slack():
    engine = _engine_with_cascade()
    grid = engine.grid
    # The reference GLM already ships 3 PCC transformers (one per zone); the
    # cascade adds 2 more above them.
    assert len(grid.pp_transformers) == 5
    names = [t["name"] for t in grid.pp_transformers]
    assert names[-2:] == ["hv_tx", "feeder_tx"]
    assert names[:3] == ["pcc_1", "pcc_2", "pcc_3"]
    # Exactly one external-grid slack, seated on the grid-edge HV bus.
    assert len(grid.pp_net.ext_grid) == 1
    slack_bus_idx = int(grid.pp_net.ext_grid.bus.iat[0])
    assert slack_bus_idx == grid.pp_bus_map["mv_src"]
    # Legacy aliases point at the first (feeder-head) transformer.
    assert grid.pp_trafo_idx == grid.pp_transformers[0]["idx"]


def test_cascade_solves_and_surfaces_results():
    engine = _engine_with_cascade()
    asyncio.run(engine.tick())
    grid = engine.grid

    # Power flow converged on the pandapower path: the LV head energised.
    lv_vm = float(grid.pp_net.res_bus.vm_pu.at[grid.pp_bus_map["ref_lv_bus_1"]])
    assert 0.8 < lv_vm < 1.2

    summary = grid.get_topology_summary()
    assert summary["transformer_count"] == 5
    assert {t["name"] for t in summary["transformers"]} == {
        "pcc_1",
        "pcc_2",
        "pcc_3",
        "hv_tx",
        "feeder_tx",
    }
    # Aggregate loss is the sum of per-unit losses; loading is the max. Compared
    # approximately: with several units the aggregate and this sum accumulate
    # their floats in different orders and can land an ULP apart.
    per_unit = summary["transformers"]
    assert summary["transformer_loss_kw"] == pytest.approx(
        sum(t["loss_kw"] for t in per_unit)
    )
    assert summary["transformer_loading_pct"] == max(t["loading_pct"] for t in per_unit)


def test_oltc_regulates_each_unit_into_band():
    engine = _engine_with_cascade()
    cfg = engine.config
    asyncio.run(engine.tick())
    grid = engine.grid
    target, db, tap_max = (
        cfg.transformer_oltc_v_target,
        cfg.transformer_oltc_deadband,
        cfg.transformer_tap_max,
    )
    for tx in grid.pp_transformers:
        lv_vm = float(grid.pp_net.res_bus.vm_pu.at[tx["lv_idx"]])
        in_band = abs(lv_vm - target) <= db
        saturated = abs(tx["tap_pos"]) == tap_max
        assert in_band or saturated, f"{tx['name']} LV={lv_vm} tap={tx['tap_pos']}"


def test_transformer_as_graph_edge_keeps_topology_connected():
    # The distflow fallback graph must reach the LV side through a transformer
    # edge instead of islanding it.
    import networkx as nx

    engine = _engine_with_cascade()
    graph = engine.grid.topology.to_networkx()
    assert graph.has_edge("mv_src", "mv_mid")
    assert graph.has_edge("mv_mid", "ref_lv_bus_1")
    assert nx.is_weakly_connected(graph)
    # The distflow root prefers the grid-edge HV bus (the pandapower slack),
    # not the interior LV substation bus.
    assert engine.grid.topology.get_substation_bus() == "mv_src"
